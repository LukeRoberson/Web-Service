"""
Module: main.py

Main module for starting the web service and setting up the routes.
This service is responsible for:
    - The web interface
    - Loading global configuration
    - Loading plugins and their configuration
    - Forwarding webhooks to the appropriate plugins
    - Displaying live alerts

Module Tasks:
    1. Fetch global configuration from the Core service
    2. Set up logging for the service
    3. Setup live logging (the /alerts page)
    4. Fetch plugin configurations from the Core service
    5. Create a Flask application instance and loading blueprints.

Usage:
    This is a Flask application that should run behind a WSGI server inside
        a Docker container.
    Build the Docker image and run it with the provided Dockerfile.

Functions:
    - create_webhook_handler:
        Factory function to create a webhook handler for each plugin.
    - logging_setup:
        Sets up the root logger for the web service.
    - create_app:
        Creates the Flask application instance and sets up the configuration.

Blueprints:
    - web_api: Handles API endpoints for the web interface.
    - web_routes: Handles web routes for the web interface.

Dependencies:
    - Flask: For creating the web application.
    - Flask-Session: For session management.
    - requests: For making HTTP requests to plugins.
    - logging: For logging messages to the terminal.

Custom Dependencies:
    - LiveAlerts: For logging alerts to the web interface.
"""

# Standard library imports
from flask import (
    Flask,
    request,
)
from flask_session import Session
import requests
from requests.exceptions import RequestException
import os
import logging
from typing import Callable, Optional, Any

# Custom imports
from api import web_api
from web import web_routes
from sdk import Config, PluginManager


CONFIG_URL = "http://core:5100/api/config"
PLUGIN_URL = "http://core:5100/api/plugins"


def create_webhook_handler(
    plugin_name: str,
    ip_list: Optional[list[str]] = None,
) -> Callable[[], tuple]:
    """
    Create a dynamic webhook handler for a plugin.
    This function returns a handler that will process incoming webhook
    requests for a specific plugin

    Args:
        plugin_name (str): The name of the plugin.
        ip_list (list): List of allowed IP addresses for the webhook.

    Returns:
        callable: A function that handles the webhook request.
    """

    def webhook_handler() -> tuple[bytes, int, Any]:
        '''
        Handle incoming webhook requests for a specific plugin.
        One of these functions is created for each plugin

        This effectively makes the web service a proxy for the plugin's
        webhook endpoint.
        It forwards the request to the plugin and returns the response.

        Returns:
            tuple: A tuple containing:
                - The content of the response from the plugin.
                - The status code of the response.
                - The headers of the response.
        '''

        # Collects the source IP address and headers
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

        try:
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

        # Handle problems, such as the plugin hasn't started yet
        except RequestException as e:
            logging.error(
                f"Failed to reach {plugin_name} plugin.\n"
                f"It may not have started yet\n"
                f"{e}"
            )

            # This is sent back to the webhook sender
            return (
                b"Service is not available",
                503,
                {'Content-Type': 'text/plain'}.items()
            )

    return webhook_handler


def logging_setup(
    config: dict,
) -> None:
    """
    Set up the root logger for the web service.

    Args:
        config (dict): The global configuration dictionary

    Returns:
        None
    """

    # Get the logging level from the configuration (eg, "INFO")
    log_level_str = config['web']['logging-level'].upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Set up the logging configuration
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging setup complete with level: %s", log_level)


def create_app(
) -> Flask:
    """
    Create the Flask application instance and set up the configuration.
    Registers the necessary blueprints for the web service.

    Args:
        None

    Returns:
        Flask: The Flask application instance with the necessary
            configuration and blueprints registered.
    """

    # Create the Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('api_master_pw')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/app/flask_session'
    Session(app)

    # Register blueprints
    app.register_blueprint(web_api)
    app.register_blueprint(web_routes)

    # Retrieve a list of plugins and their configurations
    plugins = []
    with PluginManager(PLUGIN_URL) as plugin_manager:
        plugins = plugin_manager.read()

    # Dynamically register routes for each plugin
    logging.debug("Registering webhooks for plugins...")
    logging.debug(f"Plugins: {plugins}")

    for plugin in plugins:
        logging.debug(f"Registering webhook for plugin: {plugin['name']}")
        endpoint = f"webhook_{plugin['name']}"
        allowed_ips = plugin['webhook']['allowed-ip']

        # Register the webhook URL
        app.add_url_rule(
            rule=plugin['webhook']['safe_url'],
            endpoint=endpoint,
            view_func=create_webhook_handler(plugin['name'], allowed_ips),
            methods=['POST']
        )

    return app


# Retrieve global configuration
global_config = {}
with Config(CONFIG_URL) as config:
    global_config = config.read()

# Set up logging for the web service
logging_setup(global_config)

# Create the Flask application instance
app = create_app()
