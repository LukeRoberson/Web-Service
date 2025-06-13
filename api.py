"""
Module: api.py

Adds API endpoints for the web service.

Functions:
    - get_plugin_by_name:
        Find a plugin's configuration by its name.

Blueprints:
    - web_api: A Flask blueprint that handles API endpoints for
        the web interface.

Routes:
    - /api/health:
        Test endpoint for health checks. Used by Docker
    - /api/plugins:
        Manage plugins (POST to add, PATCH to update, DELETE to remove).
    - /api/webhook:
        Receive webhooks from plugins.

Dependencies:
    - Flask: For creating the web API.
    - os: For file operations.
    - logging: For logging errors and warnings.

Custom Dependencies:
    - systemlog: For logging system messages.
"""

# Standard library imports
from flask import (
    Blueprint,
    Response,
    request,
    current_app,
    jsonify,
    make_response
)
import os
import logging
from typing import Optional
import requests

# Custom imports
from systemlog import system_log
from config import PluginConfig


RELOAD_FILE = '/app/reload.txt'
CONFIG_URL = "http://core:5100/api/config"


# Create a Flask blueprint for the API
web_api = Blueprint(
    'web_api',
    __name__
)


def get_plugin_by_name(
    plugin_list: 'PluginConfig',
    plugin_name: str
) -> Optional[dict]:
    """
    Find a plugin's configuration by its name.

    Args:
        plugin_list (PluginConfig): The plugin configuration object.
        plugin_name (str): The name of the plugin to find.
    """

    for plugin in plugin_list.config:
        if plugin['name'] == plugin_name:
            return plugin

    return None


@web_api.route(
    '/api/health',
    methods=['GET']
)
def health() -> Response:
    '''
    API endpoint to test the web service.
    Called by health checks to verify the service is running.

    Returns:
        str: Empty string indicating the service is healthy.
        200: HTTP status code indicating success.
    '''

    return make_response(
        '',
        200
    )


@web_api.route(
    '/api/plugins',
    methods=['GET', 'POST', 'PATCH', 'DELETE']
)
def api_plugins() -> Response:
    """
    API endpoint to manage plugins.
    Called by the UI when changes are made.

    Methods:
        GET - Retrieve config for a specific plugin.
        POST - Add a new plugin.
        PATCH - Update an existing plugin.
        DELETE - Remove a plugin.

    POST/JSON body should contain the plugin configuration.

    PATCH/JSON body should contain the updated plugin configuration.

    DELETE/JSON body should contain the name of the plugin to remove.

    Returns:
        JSON response indicating success.
    """

    # Get the plugin list, refresh the configuration
    plugin_list = current_app.config['PLUGIN_LIST']
    plugin_list.load_config()

    # GET is used to get the current configuration for a specific plugin
    if request.method == 'GET':
        plugin_name = request.headers.get('X-Plugin-Name')
        if not plugin_name:
            return make_response(
                jsonify(
                    {
                        'result': 'error',
                        'message': 'Missing X-Plugin-Name header'
                    }
                ),
                400
            )

        plugin = get_plugin_by_name(plugin_list, plugin_name)
        if plugin:
            return jsonify({
                'result': 'success',
                'plugin': plugin}
            )

        system_log.log(
            f"Plugin {plugin_name} not found in configuration",
            severity='error'
        )

        return make_response(
            jsonify(
                {
                    'result': 'error',
                    'message': f'Plugin {plugin_name} not found'
                }
            ),
            404
        )

    # POST is used to add a new plugin
    elif request.method == 'POST':
        result = plugin_list.register(request.json)

        # If this failed...
        if not result:
            return jsonify(
                {
                    'result': 'error',
                    'message': 'Failed to update configuration'
                }
            )

    # PATCH is used to update an existing plugin
    elif request.method == 'PATCH':
        result = plugin_list.update_config(request.json)

        # If this failed...
        if not result:
            return jsonify(
                {
                    'result': 'error',
                    'message': 'Failed to update configuration'
                }
            )

    # DELETE is used to remove a plugin
    elif request.method == 'DELETE':
        data = request.json
        if not data or 'name' not in data:
            return make_response(
                jsonify(
                    {
                        'result': 'error',
                        'message': 'Missing plugin name in request body'
                    }
                ),
                400
            )
        result = plugin_list.delete(data['name'])

    # If successful, recycle the workers to apply the changes
    try:
        with open(RELOAD_FILE, 'a'):
            os.utime(RELOAD_FILE, None)
    except Exception as e:
        logging.error("Failed to update reload.txt: %s", e)

    return jsonify(
        {
            'result': 'success'
        }
    )


@web_api.route(
    '/api/config',
    methods=['GET', 'PATCH']
)
def api_config() -> Response:
    """
    API endpoint to manage global configuration.

    Methods:
        GET - Called by a module to get the current configuration.
        PATCH - Called by the UI when changes are made.

    PATCH/JSON body should contain the updated configuration.

    Returns:
        JSON response indicating success.
    """

    # Get the config, refresh the configuration
    app_config = current_app.config['GLOBAL_CONFIG']

    # GET is used to get the current configuration
    if request.method == 'GET':
        return make_response(
            jsonify(
                {
                    'result': 'success',
                    'config': app_config
                }
            )
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json

        # Forward the PATCH request to the core service
        try:
            resp = requests.patch(CONFIG_URL, json=data, timeout=5)
            if resp.status_code != 200:
                return make_response(
                    jsonify(
                        {
                            'result': 'error',
                            'message': f"Failed to update configuration: "
                            f"{resp.text}"
                        }
                    ), resp.status_code
                )

        except Exception as e:
            logging.error("Failed to patch core service: %s", e)
            return make_response(
                jsonify(
                    {
                        'result': 'error',
                        'message': f'Failed to update configuration: {e}'
                    }
                ),
                500
            )

        # If successful, recycle the workers to apply the changes
        try:
            with open(RELOAD_FILE, 'a'):
                os.utime(RELOAD_FILE, None)
        except Exception as e:
            logging.error("Failed to update reload.txt: %s", e)

        return make_response(
            jsonify(
                {
                    'result': 'success'
                }
            ),
            200
        )

    # If the method is not GET or PATCH, return a 405 Method Not Allowed
    return make_response(
        jsonify(
            {
                'result': 'error',
                'message': 'Method not allowed'
            }
        ),
        405
    )


@web_api.route(
    '/api/webhook',
    methods=['POST']
)
def api_webhook() -> Response:
    """
    API endpoint to receive logs from plugins and services.
    Logging service will broker the logs to the appropriate destinations.
    Logging service sends a POST request to this endpoint

    POST/JSON body should contain the following fields:
        - timestamp: The time the alert was generated.
        - source: The source of the alert (e.g., plugin name).
        - group: The group of the alert (e.g., 'service').
        - category: The category of the alert (e.g., 'web-ui').
        - alert: The type of alert (e.g., 'system').
        - severity: The severity of the alert (e.g., 'info', 'warning', etc).
        - message: The message of the alert.

    Returns:
        JSON response indicating success.
    """

    # The body of the request
    data = request.json
    logging.debug("Received webhook data: %s", data)

    if data is None:
        return make_response(
            jsonify(
                {
                    'result': 'error',
                    'message': 'No data provided'
                }
            ),
            400
        )

    # Get the logger object from the current app config
    logger = current_app.config['LOGGER']

    # Process the webhook data, store in the DB
    logger.log_alert(
        timestamp=data['timestamp'],
        source=data['source'],
        group=data['group'],
        category=data['category'],
        alert=data['alert'],
        severity=data['severity'],
        message=data['message']
    )

    # Purge old alerts
    logger.purge_old_alerts()

    # Return a success response
    return jsonify(
        {
            'result': 'success'
        }
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
