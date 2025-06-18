"""
Module: api.py

Adds API endpoints for the web service.

Classes:
    - PluginAPI: A context manager for managing plugins through the Core API.

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


RELOAD_FILE = '/app/reload.txt'
CONFIG_URL = "http://core:5100/api/config"
PLUGINS_URL = "http://core:5100/api/plugins"


# Create a Flask blueprint for the API
web_api = Blueprint(
    'web_api',
    __name__
)


def error_response(
    message,
    status=400
) -> Response:
    """
    A helper function to create an error response.

    Args:
        message (str): The error message to return.
        status (int): The HTTP status code for the error response.

    Returns:
        Response: A Flask Response object with the error message
            and status code.
    """

    return make_response(
        jsonify(
            {
                'result': 'error',
                'message': message
            }
        ),
        status
    )


def success_response(
    message=None,
    data=None,
    status=200
) -> Response:
    """
    A helper function to create a success response.

    Args:
        message (str, optional): A success message to include in the response.
        data (dict, optional): Additional data to include in the response.
        status (int): The HTTP status code for the success response.

    Returns:
        Response: A Flask Response object with the success message
            and status code.
    """

    # Standard response structure
    resp = {
        'result': 'success'
    }

    # Update with custom message or data if provided
    if message:
        resp['message'] = message
    if data:
        resp.update(data)

    return make_response(
        jsonify(
            resp
        ),
        status
    )


class PluginAPI:
    """
    Manage plugins through the Core API.

    Args:
        plugins_url (str): The URL to the plugins API.
    """

    def __init__(
        self,
        plugins_url: str = PLUGINS_URL
    ):
        """
        Initialize the PluginAPI with the URL to the plugins API.
        """
        self.url = plugins_url

    def __enter__(
        self
    ) -> 'PluginAPI':
        """
        Enter the runtime context related to this object.

        Returns:
            PluginAPI: The instance of the PluginAPI.
        """

        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[object]
    ) -> None:
        """
        Exit the runtime context related to this object.

        Args:
            exc_type (Optional[type]): The exception type.
            exc_value (Optional[Exception]): The exception value.
            traceback (Optional[object]): The traceback object.
        """

        # No cleanup needed for this context manager
        pass

    def _plugin_request(
        self,
        method: str,
        config: dict
    ) -> bool:
        """
        Make a request to the Core API to manage plugins.

        Args:
            method (str): The HTTP method to use
                (e.g., 'POST', 'PATCH', 'DELETE').
            config (dict): The configuration for the plugin to manage.

        Returns:
            bool: True if the request was successful, False otherwise.
        """

        if not config:
            logging.error("No configuration provided for the plugin.")
            return False

        try:
            response = requests.request(
                method,
                self.url,
                json=config,
                timeout=3
            )

            if response.status_code != 200:
                logging.error(
                    "Core service failed to %s plugin:\n %s",
                    method,
                    response.text
                )
                return False

        except Exception as e:
            logging.error("Error accessing the plugins API: %s", e)
            return False

        return True

    def get_plugins(
        self,
    ) -> list[dict]:
        """
        Fetch the list of plugins from the core API.

        Args:
            plugins_url (str): The URL to fetch the plugins from.

        Returns:
            dict: A dictionary containing the list of plugins.
        """

        # API call
        try:
            response = requests.get(
                self.url,
                headers={"X-Plugin-Name": "all"},
                timeout=3
            )
            if response.status_code == 200:
                plugin_list = response.json()['plugins']
                logging.debug("Fetched plugins from API: %s", plugin_list)

            else:
                plugin_list = []
                logging.warning(
                    "Failed to fetch plugins from API:\n %s",
                    response.text
                )

        except Exception as e:
            plugin_list = []
            logging.error("Error accessing the plugins API: %s", e)

        return plugin_list

    def get_plugin_by_name(
        self,
        plugin_name: str
    ) -> Optional[dict]:
        """
        Find a plugin's configuration by its name.

        Args:
            plugin_name (str): The name of the plugin to find.
        """

        plugin_list = self.get_plugins()
        for plugin in plugin_list:
            if plugin['name'] == plugin_name:
                return plugin

        return None

    def add_plugin(
        self,
        config: dict
    ) -> bool:
        """
        Add a new plugin using the Core API.

        Args:
            config (dict): The configuration for the plugin to add.

        Returns:
            bool: True if the plugin was added successfully, False otherwise.
        """

        return self._plugin_request(
            'POST',
            config,
        )

    def update_plugin(
        self,
        config: dict
    ) -> bool:
        """
        Update an existing plugin using the Core API.

        Args:
            config (dict): The updated configuration for the plugin.

        Returns:
            bool: True if the plugin was updated successfully, False otherwise.
        """

        return self._plugin_request(
            'PATCH',
            config
        )

    def delete_plugin(
        self,
        config
    ) -> bool:
        """
        Delete a plugin using the Core API.

        Args:
            config (dict):
                The configuration containing the name of the plugin to delete.

        Returns:
            bool: True if the plugin was deleted successfully, False otherwise.
        """

        return self._plugin_request(
            'DELETE',
            config
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
        with PluginAPI(plugins_url=PLUGINS_URL) as plugin_api:
            # Find the plugin by name
            plugin = plugin_api.get_plugin_by_name(
                plugin_name=plugin_name
            )

        if plugin:
            return jsonify(
                {
                    "result": "success",
                    "plugin": plugin
                }
            )

        return error_response(
            f'Plugin {plugin_name} not found',
            status=404
        )

    # POST is used to add a new plugin
    elif request.method == 'POST':
        if not request.json:
            return error_response('No configuration provided')

        with PluginAPI(plugins_url=PLUGINS_URL) as plugin_api:
            result = plugin_api.add_plugin(
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

        with PluginAPI(plugins_url=PLUGINS_URL) as plugin_api:
            # Update the plugin configuration
            result = plugin_api.update_plugin(
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

        with PluginAPI(plugins_url=PLUGINS_URL) as plugin_api:
            result = plugin_api.delete_plugin(
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
    app_config = current_app.config['GLOBAL_CONFIG']

    # GET is used to get the current configuration
    if request.method == 'GET':
        return success_response(
            data={"config": app_config}
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json

        # Forward the PATCH request to the core service
        try:
            resp = requests.patch(CONFIG_URL, json=data, timeout=5)
            if resp.status_code != 200:
                return error_response(
                    f"Failed to update configuration: {resp.text}"
                )

        except Exception as e:
            logging.error("Failed to patch core service: %s", e)
            return error_response(f"Failed to update configuration: {e}")

        # If successful, recycle the workers to apply the changes
        try:
            with open(RELOAD_FILE, 'a'):
                os.utime(RELOAD_FILE, None)
        except Exception as e:
            logging.error("Failed to update reload.txt: %s", e)

        return success_response()

    # If the method is not GET or PATCH, return a 405 Method Not Allowed
    return error_response(
        'Method not allowed',
        status=405
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
