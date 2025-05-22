"""
Main module for starting the web service and setting up the routes.

Usage:
    Run this module to start the web application.

Example:
    $ python main.py
"""

from flask import Flask, render_template, request
import flask
import sys
from colorama import Fore, Style
import requests
import os

from config import PluginConfig, GlobalConfig
from alerts import AlertLogger


# Create the Flask application
app = Flask(__name__)

# Initialise the logging module
logger = AlertLogger()

# Load the configuration
print(Fore.YELLOW + "Loading configuration..." + Style.RESET_ALL)
app_config = GlobalConfig()
app_config.load_config()

# Load the plugin configuration
print()
print(Fore.YELLOW + "Loading plugins..." + Style.RESET_ALL)
plugin_list = PluginConfig()
plugin_list.load_config()
print(Fore.GREEN, len(plugin_list), Style.RESET_ALL, "plugins loaded")

print()
print(Fore.YELLOW + "Loaded plugins:" + Style.RESET_ALL)
for plugin in plugin_list:
    print("  ", plugin['name'])
print()


# Function Factory - Function to create a function
# Dynamic webhook handler function per plugin
def make_dynamic_webhook_handler(plugin_name, ip_list):
    def handle_dynamic_webhook():
        src = request.remote_addr
        print(Fore.YELLOW, "DEBGU: Source IP:", src, Style.RESET_ALL)
        print(Fore.YELLOW, "Allowed IPs:", ip_list, Style.RESET_ALL)

        # Proxy the webhook request to the plugin
        response = requests.post(
            f"http://{plugin_name}:5000/webhook",
            json=request.json
        )

        # Proxy the response back to the original request
        return (
            response.content,
            response.status_code,
            response.headers.items()
        )

    return handle_dynamic_webhook


# Dynamically register routes for each plugin
for plugin in plugin_list:
    endpoint = f"webhook_{plugin['name']}"
    allowed_ips = plugin['webhook']['allowed-ip']

    # Register the webhook URL
    #   (1) Use safe URL from the plugin config
    #   (2) Use the plugin name as the endpoint (the route's name)
    #   (3) Use the plugin name as the function name
    #   (4) POST method only
    app.add_url_rule(
        plugin['webhook']['safe_url'],
        endpoint,
        make_dynamic_webhook_handler(plugin['name'], allowed_ips),
        methods=['POST']
    )


@app.route('/config')
def config():
    return render_template(
        'config.html',
        title="Config",
        config=app_config.config,
    )


@app.route('/about')
def about():
    return render_template(
        'about.html',
        title="About",
        flask_version=flask.__version__,
        python_version=sys.version,
        debug_mode=app.debug
    )


@app.route('/alerts')
def alerts():
    '''
    Route to display the alerts page.
    Gets the recent alerts from the logger and passes them to the template.
    '''

    # Collect a list of alerts
    alerts = logger.get_recent_alerts()

    return render_template(
        'alerts.html',
        title="Alerts",
        alerts=alerts,
    )


@app.route('/plugins')
def plugins():
    # Refresh the plugin list
    plugin_list.load_config()

    print(
        Fore.YELLOW,
        "DEBUG: Loading plugins page",
        Style.RESET_ALL
    )
    print(
        Fore.YELLOW,
        "DEBUG: Plugin list:",
        plugin_list.config,
        Style.RESET_ALL
    )

    return render_template(
        'plugins.html',
        title="Plugins",
        plugins=plugin_list.config,
    )


@app.route(
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
        return flask.jsonify(
            {
                'result': 'error',
                'message': 'Failed to update configuration'
            }
        )

    # If successful, recycle the workers to apply the changes
    with open('/app/reload.txt', 'a'):
        os.utime('/app/reload.txt', None)

    return flask.jsonify(
        {
            'result': 'success'
        }
    )


@app.route(
    '/api/config',
    methods=['PATCH']
)
def api_config():
    """
    API endpoint to manage global configuration.
    Called by the UI when changes are made.

    Returns:
        JSON response indicating success.
    """

    # The body of the request
    data = request.json

    # Refresh the plugin list
    app_config.load_config()

    # PATCH is used to update config
    if request.method == 'PATCH':
        result = app_config.update_config(data)

    # If this failed...
    if not result:
        return flask.jsonify(
            {
                'result': 'error',
                'message': 'Failed to update configuration'
            }
        )

    # If successful, recycle the workers to apply the changes
    with open('/app/reload.txt', 'a'):
        os.utime('/app/reload.txt', None)

    return flask.jsonify(
        {
            'result': 'success'
        }
    )


@app.route('/api/webhook', methods=['POST'])
def api_webhook():
    """
    API endpoint to receive webhooks from plugins.
    POST from the plugin when a webhook is received.

    Returns:
        JSON response indicating success.
    """

    # The body of the request
    data = request.json
    print(
        Fore.YELLOW,
        "DEBUG: Received webhook:",
        data,
        Style.RESET_ALL
    )

    # Process the webhook data, store in the DB
    logger.log_alert(
        source=data['source'],
        type=data['type'],
        message=data['message']
    )

    # Purge old alerts
    logger.purge_old_alerts()

    # Return a success response
    return flask.jsonify(
        {
            'result': 'success'
        }
    )


'''
NOTE: When running in a container, the host and port are set in the
    uWSGI config. uWSGI starts the process, which means the
    Flask app is not run directly.
    This can be uncommented for local testing.
'''
# if __name__ == "__main__":
#     # Run the application
#     app.run(
#         debug=True,
#         host='0.0.0.0',
#         port=5000,
#     )
