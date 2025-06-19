"""
Module: api.py

Adds API endpoints for the web service.

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

Custom Imports:
    - sdk.error_response: A helper function to create error responses.
    - sdk.success_response: A helper function to create success responses.
"""

# Standard library imports
from flask import (
    Blueprint,
    Response,
    request,
    make_response
)
import logging

# Custom imports
from sdk import error_response, success_response
from sdk import PluginManager, Config


RELOAD_FILE = '/app/reload.txt'
CONFIG_URL = "http://core:5100/api/config"
PLUGINS_URL = "http://core:5100/api/plugins"


# Create a Flask blueprint for the API
web_api = Blueprint(
    'web_api',
    __name__
)


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

    # GET is used to get the current configuration for a specific plugin
    if request.method == 'GET':
        # Expects the X-Plugin-Name header to specify which plugin
        plugin_name = request.headers.get('X-Plugin-Name')
        if not plugin_name:
            return error_response('Missing X-Plugin-Name header')

        # Get the plugin config from the list
        plugin = None
        with PluginManager(PLUGINS_URL) as plugin_manager:
            plugin = plugin_manager.read(
                name=plugin_name
            )

        if plugin:
            return success_response(
                data={"plugin": plugin}
            )

        return error_response(
            f'Plugin {plugin_name} not found',
            status=404
        )

    # POST is used to add a new plugin
    elif request.method == 'POST':
        if not request.json:
            return error_response('No configuration provided')

        result = None
        with PluginManager(PLUGINS_URL) as plugin_manager:
            result = plugin_manager.create(
                config=request.json
            )

        # If this failed...
        if not result:
            logging.error("Failed to add plugin: %s", request.json)
            return error_response('Failed to add plugin')

        # Successfully added the plugin
        return success_response(
            message='Plugin added successfully',
            status=201
        )

    # PATCH is used to update an existing plugin
    elif request.method == 'PATCH':
        if not request.json:
            return error_response('No configuration provided')

        result = None
        with PluginManager(PLUGINS_URL) as plugin_manager:
            # Update the plugin configuration
            result = plugin_manager.update(
                config=request.json
            )

        # If this failed...
        if not result:
            logging.error("Failed to update plugin: %s", request.json)
            return error_response('Failed to update plugin')

        # Successfully updated the plugin
        return success_response('Plugin updated successfully')

    # DELETE is used to remove a plugin
    elif request.method == 'DELETE':
        data = request.json
        if not data or 'name' not in data:
            return error_response('No plugin name provided')

        result = None
        with PluginManager(PLUGINS_URL) as plugin_manager:
            result = plugin_manager.delete(
                config=data
            )

        # If this failed...
        if not result:
            logging.error("Failed to delete plugin: %s", data)
            return error_response('Failed to delete plugin')

        # Successfully deleted the plugin
        return success_response('Plugin deleted successfully')

    return success_response()


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
    app_config = {}
    with Config(CONFIG_URL) as config:
        app_config = config.read()

    # GET is used to get the current configuration
    if request.method == 'GET':
        return success_response(
            data={"config": app_config}
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json
        if not data:
            return error_response('No configuration provided')

        result = None
        message = None
        with Config(CONFIG_URL) as config_manager:
            # Update the configuration with the provided data
            result, message = config_manager.update(
                config=data,
                reload_file=RELOAD_FILE
            )

        if result is False:
            logging.error("Failed to update configuration: %s", message)
            return error_response(f"Failed to update configuration: {message}")
        else:
            return success_response()

    # If the method is not GET or PATCH, return a 405 Method Not Allowed
    return error_response(
        'Method not allowed',
        status=405
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
