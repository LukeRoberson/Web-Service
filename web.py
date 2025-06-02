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
import requests

from systemlog import system_log


LOCAL_DOMAIN = 'karen.lakemac.nsw.gov.au'


# Create a Flask blueprint for the web routes
web_routes = Blueprint(
    'web_routes',
    __name__,
    template_folder='templates',
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
        logging.warning("Invalid or expired token")
        system_log.log(
            message="Invalid or expired authentication token",
            alert="authentication",
            severity="warning",
        )
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

    # Check if the Azure service account is authenticated
    response = requests.get("http://security:5100/api/token", timeout=3)
    if response.status_code == 200:
        logging.debug("Azure service account is authenticated")
        logged_in = True
    else:
        logging.warning("Azure service account is not authenticated")
        logged_in = False

    service_login_url = f"https://{LOCAL_DOMAIN}/login?prompt=login"

    return render_template(
        'about.html',
        title="About",
        flask_version=flask_version,
        python_version=sys.version,
        debug_mode=True,
        service_account=current_app.config['GLOBAL_CONFIG']['teams']['user'],
        logged_in=logged_in,
        service_login_url=service_login_url,
    )


@web_routes.route('/alerts')
@protected
def alerts():
    '''
    Route to display the alerts page.
    Gets the recent alerts from the logger and passes them to the template.

    The alerts are paginated, with a default page size of 200.
    The total number of alerts and pages is calculated.
    The page number is taken from the request arguments, defaulting to 1.
    '''

    # Get the logger object from the current app config
    logger = current_app.config['LOGGER']

    # Check search and filter parameters
    search = request.args.get('search', '').strip()
    system_only = request.args.get('system_only') == '1'
    source = request.args.get('source', '')
    group = request.args.get('group', '')
    category = request.args.get('category', '')
    alert = request.args.get('alert', '')
    severity = request.args.get('severity', '')

    # If system_only is set and group is not, set group to 'service'
    if not group and system_only:
        group = 'service'

    # Manage pagination for alerts
    page_size = 200
    total_logs = logger.count_alerts(
        search=search,
        source=source,
        group=group,
        category=category,
        alert=alert,
        severity=severity,
    )
    total_pages = (total_logs + page_size - 1) // page_size

    # Get the page number to display, or default to 1
    page_number = request.args.get('page', 1, type=int)

    # Collect a list of alerts
    alerts = logger.get_recent_alerts(
        offset=(page_number - 1) * page_size,
        limit=page_size,
        search=search,
        source=source,
        group=group,
        category=category,
        alert=alert,
        severity=severity,
    )

    # Extract unique values for each field
    source_list = sorted({event[1] for event in alerts})
    group_list = sorted({event[2] for event in alerts})
    category_list = sorted({event[3] for event in alerts})
    alert_list = sorted({event[4] for event in alerts})

    return render_template(
        'alerts.html',
        title="Alerts",
        alerts=alerts,
        page=page_number,
        total_logs=total_logs,
        total_pages=total_pages,
        source_list=source_list,
        group_list=group_list,
        category_list=category_list,
        alert_list=alert_list,
        severity_list=['debug', 'info', 'warning', 'error', 'critical'],
        request=request,
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


@web_routes.route(
    '/tools',
    methods=['GET', 'POST']
)
@protected
def tools():
    '''
    Route to display the tools page.
    Provides a simple encryption/decryption tool

    Methods:
        GET: Display the tool page as normal
        POST: Process the form submission to encrypt/decrypt
    '''

    encrypt_encrypted = encrypt_salt = encrypt_error = None
    decrypt_plain = decrypt_error = None

    # Process the form submission
    if request.method == 'POST':
        # Get strings from the form
        plain = request.form.get('plaintext', '')
        encrypted = request.form.get('encrypted', '')
        salt = request.form.get('salt', '')

        operation = None
        if plain and not encrypted:
            operation = 'encrypt'
        elif encrypted and salt and not plain:
            operation = 'decrypt'
        else:
            error = "Need either 'plain-text' or 'encrypted' with 'salt'"
            logging.error(error)
            return render_template(
                'tools.html',
                encrypt_encrypted=encrypt_encrypted,
                encrypt_salt=encrypt_salt,
                encrypt_error=encrypt_error,
                decrypt_plain=decrypt_plain,
                decrypt_error=decrypt_error,
            )

        try:
            response = requests.post(
                'http://security:5100/api/crypto',
                json={
                    'type': operation,
                    'plain-text': plain,
                    'encrypted': encrypted,
                    'salt': salt,
                },
                timeout=5
            )

            data = response.json()
            if data.get('result') == 'success':
                if operation == 'encrypt':
                    # If encrypting, get the encrypted string and salt
                    encrypt_encrypted = data.get('encrypted')
                    encrypt_salt = data.get('salt')

                elif operation == 'decrypt':
                    # If decrypting, get the decrypted string
                    decrypt_plain = data.get('decrypted')

            else:
                if operation == 'encrypt':
                    encrypt_error = data.get('error', 'Unknown error')
                    logging.error("Encryption failed: %s", data.get('error'))
                else:
                    decrypt_error = data.get('error', 'Unknown error')
                    logging.error("Decryption failed: %s", data.get('error'))

        except Exception as e:
            if operation == 'encrypt':
                encrypt_error = str(e)
            else:
                decrypt_error = str(e)

    # Display the page
    return render_template(
        'tools.html',
        encrypt_encrypted=encrypt_encrypted,
        encrypt_salt=encrypt_salt,
        encrypt_error=encrypt_error,
        decrypt_plain=decrypt_plain,
        decrypt_error=decrypt_error,
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
