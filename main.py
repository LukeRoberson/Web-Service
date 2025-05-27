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
from colorama import Fore, Style
import requests
import os
import logging

from config import PluginConfig, GlobalConfig
from alerts import AlertLogger
from api import web_api
from web import web_routes


# Set up logging
logging.basicConfig(level=logging.INFO)

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
        logging.info(
            f"Received webhook request for plugin '{plugin_name}' "
            f"from IP: {src}"
        )

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
