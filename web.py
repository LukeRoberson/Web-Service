"""
Web module.
    Provides routes for the web UI.

Functions:
    - verify_auth_token:
        Verify an authentication token from the security service.
    - protected:
        Decorator to protect a route with authentication.

Blueprint lists routes for the web UI. This is registered in main.py

Routes:
    - /:
        Very simple page, just to satisfy external security services.
    - /config:
        Configuration of the application.
    - /about:
        About page with application information.
    - /alerts:
        Alerts page to display recent alerts.
    - /plugins:
        Plugins page to manage plugins.
"""


from flask import (
    Blueprint,
    current_app,
    request,
    session,
    render_template,
    jsonify,
    redirect,
    __version__ as flask_version,
)

from functools import wraps
from itsdangerous import URLSafeTimedSerializer

import logging
from typing import Optional
import sys


# Set up logging
logging.basicConfig(level=logging.INFO)

# Create a Flask blueprint for the web routes
web_routes = Blueprint(
    'web_routes',
    __name__,
)


def verify_auth_token(
    token: str,
    secret_key: str,
    max_age: int = 3600
) -> Optional[str]:
    '''
    Verify the authentication token.

    Uses a serializer from the itsdangerous library to verify the token.

    Args:
        token (str): The token to verify.
        secret_key (str): The secret key used to sign the token.
        max_age (int): The maximum age of the token in seconds.

    Returns:
        Optional[str]: The user associated with the token if valid,
    '''

    # Create the serializer
    serializer = URLSafeTimedSerializer(secret_key)

    # Try to load the token
    try:
        data = serializer.loads(token, max_age=max_age)

        # If the token is valid, return the user
        return data['user']

    # If there's a bad signature or the token is expired, return None
    except Exception:
        logging.debug("Invalid or expired token")
        return None


def protected(f):
    '''
    Decorator to protect a route with authentication.
    Checks if the user is logged in and has admin permissions.

    Uses a local session for user information.
        If the user is not in the session, it checks for a
            token in the request.
        If a token is found, it verifies the token and stores
            the user in the session.
        If the user is not authenticated, it redirects to the auth page.
    '''

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if there's a token in the request
        token = request.args.get('token')

        # User is providing a token, but is not in the session yet
        #   They have authenticated and been given a token
        #   Verify that the token is valid
        if 'user' not in session and token:
            # Get the secret key from the app config
            secret_key = current_app.config.get('SECRET_KEY')

            # Verify the token
            user = verify_auth_token(token, secret_key)

            # If the token is valid, store the user in the session
            if user:
                session['user'] = user

            # If token validation failed
            else:
                return jsonify(
                    {
                        'result': 'error',
                        'message': 'Invalid token'
                    }
                )

        # User is not authenticated
        #   Neither in the session nor providing a token
        elif "user" not in session:
            return redirect(
                f"/auth?redirect={request.url}"
            )

        # User is already authenticated (user is in the session)
        return f(*args, **kwargs)

    return decorated_function


@web_routes.route('/')
def index():
    '''
    Just so a home page exists.
    Some external security services require a home page to be present.
    '''

    return "I'd like to speak to the manager!"


@web_routes.route('/config')
@protected
def config():
    '''
    Route to display the configuration page.
    Gets global configuration and passes it to the template.
    '''

    # Get the config object and refresh contents
    app_config = current_app.config['GLOBAL_CONFIG']
    app_config.load_config()
    logging.info("Config loaded: %s", app_config.config)

    return render_template(
        'config.html',
        title="Config",
        config=app_config.config,
    )


@web_routes.route('/about')
@protected
def about():
    '''
    Route to display the about page.
    Displays Flask version, Python version, and debug mode status.
    '''

    return render_template(
        'about.html',
        title="About",
        flask_version=flask_version,
        python_version=sys.version,
        debug_mode=True
    )


@web_routes.route('/alerts')
@protected
def alerts():
    '''
    Route to display the alerts page.
    Gets the recent alerts from the logger and passes them to the template.
    '''

    # Get the logger object from the current app config
    logger = current_app.config['ALERT_LOGGER']

    # Collect a list of alerts
    alerts = logger.get_recent_alerts()

    return render_template(
        'alerts.html',
        title="Alerts",
        alerts=alerts,
    )


@web_routes.route('/plugins')
@protected
def plugins():
    '''
    Route to display the plugins page.
    Gets the plugin list object from the app config and refreshes its contents.
    Passes the plugin configuration to the template.
    '''

    # Get the plugin list object, and refresh its contents
    plugin_list = current_app.config['PLUGIN_LIST']
    plugin_list.load_config()
    logging.info("Plugin list loaded: %s", plugin_list.config)

    return render_template(
        'plugins.html',
        title="Plugins",
        plugins=plugin_list.config,
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
