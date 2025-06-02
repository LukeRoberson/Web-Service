"""
Main module for starting the web service and setting up the routes.

Usage:
    Run this module to start the web application.

Example:
    $ python main.py
"""

from flask import (
    Flask,
    request,
)
from flask_session import Session
import requests
import os
import logging

from config import PluginConfig, GlobalConfig
from alerts import AlertLogger
from api import web_api
from web import web_routes


# Load the configuration
app_config = GlobalConfig()
app_config.load_config()

# Set up logging
log_level_str = app_config.config['web']['logging-level'].upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level)
print(f"Logging level set to: {log_level_str}")

# Initialise the logging module (for alerts page)
logger = AlertLogger()

# Load the plugin configuration
plugin_list = PluginConfig()
plugin_list.load_config()

logging.info("%s plugins loaded", len(plugin_list))

for plugin in plugin_list:
    logging.debug(
        "Plugin '%s' loaded with webhook URL: %s",
        plugin['name'],
        plugin['webhook']['safe_url']
    )

# Create the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('api_master_pw')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PLUGIN_LIST'] = plugin_list
app.config['GLOBAL_CONFIG'] = app_config
app.config['LOGGER'] = logger
Session(app)

# Register blueprints
app.register_blueprint(web_api)
app.register_blueprint(web_routes)


# Function Factory - Function to create a function
# Dynamic webhook handler function per plugin
def make_dynamic_webhook_handler(plugin_name, ip_list):
    def handle_dynamic_webhook():
        src = request.remote_addr
        headers = dict(request.headers)

        # Remove headers that requests will set automatically
        headers.pop('Host', None)
        headers.pop('Content-Length', None)
        headers.pop('Transfer-Encoding', None)

        logging.debug(
            f"Received webhook for plugin '{plugin_name}' "
            f"from IP: {src}"
        )

        # Proxy the webhook request to the plugin
        response = requests.post(
            f"http://{plugin_name}:5000/webhook",
            data=request.get_data(),
            headers=headers,
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
