"""
API module.
    Used for communication between services and the web UI.

Blueprint lists routes for the web API. This is registered in main.py

Routes:
    - /api/test:
        Test endpoint for health checks.
    - /api/plugins:
        Manage plugins (POST to add, PATCH to update, DELETE to remove).
    - /api/config:
        Manage global configuration (GET to retrieve, PATCH to update).
    - /api/webhook:
        Receive webhooks from plugins.
"""


from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
)

import os
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)

# Create a Flask blueprint for the API
web_api = Blueprint(
    'web_api',
    __name__
)


@web_api.route(
    '/api/test',
    methods=['GET']
)
def api_test():
    '''
    API endpoint to test the web service.
    Called by health checks to verify the service is running.
    '''

    return '', 200


@web_api.route(
    '/api/plugins',
    methods=['POST', 'PATCH', 'DELETE']
)
def api_plugins():
    """
    API endpoint to manage plugins.
    Called by the UI when changes are made.

    Returns:
        JSON response indicating success.
    """

    # The body of the request
    data = request.json

    # Get the plugin list object from the current app config
    plugin_list = current_app.config['PLUGIN_LIST']

    # Refresh the plugin list
    plugin_list.load_config()

    # POST is used to add a new plugin
    if request.method == 'POST':
        result = plugin_list.register(data)

    # PATCH is used to update an existing plugin
    elif request.method == 'PATCH':
        result = plugin_list.update_config(data)

    # DELETE is used to remove a plugin
    elif request.method == 'DELETE':
        result = plugin_list.delete(data['name'])

    # If this failed...
    if not result:
        return jsonify(
            {
                'result': 'error',
                'message': 'Failed to update configuration'
            }
        )

    # If successful, recycle the workers to apply the changes
    with open('/app/reload.txt', 'a'):
        os.utime('/app/reload.txt', None)

    return jsonify(
        {
            'result': 'success'
        }
    )


@web_api.route(
    '/api/config',
    methods=['GET', 'PATCH']
)
def api_config():
    """
    API endpoint to manage global configuration.
        GET - Called by a module to get the current configuration.
        PATCH - Called by the UI when changes are made.

    Returns:
        JSON response indicating success.
    """
    logging.info("Global config requested through API")
    logging.info("GLOBAL_CONFIG: %s", current_app.config['GLOBAL_CONFIG'])

    # Get the config object from the current app config
    app_config = current_app.config['PLUGIN_LIST']

    # Refresh the configuration
    app_config.load_config()

    # GET is used to get the current configuration
    if request.method == 'GET':
        return jsonify(
            {
                'result': 'success',
                'config': app_config.config
            }
        )

    # PATCH is used to update config
    if request.method == 'PATCH':
        # The body of the request
        data = request.json

        result = app_config.update_config(data)

        # If this failed...
        if not result:
            return jsonify(
                {
                    'result': 'error',
                    'message': 'Failed to update configuration'
                }
            )

        # If successful, recycle the workers to apply the changes
        with open('/app/reload.txt', 'a'):
            os.utime('/app/reload.txt', None)

        return jsonify(
            {
                'result': 'success'
            }
        )


@web_api.route(
    '/api/webhook',
    methods=['POST']
)
def api_webhook():
    """
    API endpoint to receive webhooks from plugins.
    POST from the plugin when a webhook is received.

    Returns:
        JSON response indicating success.
    """

    # The body of the request
    data = request.json
    logging.info("Received webhook data: %s", data)

    # Get the logger object from the current app config
    logger = current_app.config['ALERT_LOGGER']

    # Process the webhook data, store in the DB
    logger.log_alert(
        source=data['source'],
        type=data['type'],
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
