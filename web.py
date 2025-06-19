"""
Module: web.py

Provides the web routes for the web service. This is the WebUI that users
    interact with.

Functions:
    - verify_auth_token:
        Verify an authentication token from the security service.
    - mask_secrets:
        Mask secrets in plugin configurations for display.
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
    - /tools:
        Tools page for useful utilities.

Dependencies:
    - Flask: For creating the web application.
    - itsdangerous: For token verification.
    - requests: For making HTTP requests to external services.
    - urllib.parse: For parsing URLs.
    - logging: For logging errors and warnings.
    - functools: For creating decorators.
    - typing: For type hinting and annotations.
    - copy: For deep copying objects.

Custom Dependencies:
    - systemlog: For logging system messages.
"""

# Standard library imports
from flask import (
    Blueprint,
    Response,
    current_app,
    request,
    session,
    render_template,
    jsonify,
    redirect,
    make_response,
)
from functools import wraps
from itsdangerous import URLSafeTimedSerializer
import logging
from typing import Optional, Callable, Any, cast
import requests
from urllib.parse import urlparse, urlencode
import copy

# Custom imports
from systemlog import system_log
from sdk import Config, PluginManager


TOKEN_URL = "http://security:5100/api/token"
CHAT_LIST_URL = "http://teams:5100/api/chat_list"
CRYPTO_URL = "http://security:5100/api/crypto"
CONTAINER_URL = "http://core:5100/api/containers"
PLUGINS_URL = "http://core:5100/api/plugins"
LIVE_ALERTS_URL = "http://logging:5100/api/livealerts"
CONFIG_URL = "http://core:5100/api/config"


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


def mask_secrets(
    plugins
) -> list:
    """
    Mask the secrets in the plugin configuration.
        This is to prevent sensitive information from being displayed
        in the web UI.

    Args:
        plugins (list): A list of plugin configurations.

    Returns:
        list: A list of plugin configurations with secrets masked.
    """

    masked = []
    for plugin in plugins:
        plugin_copy = copy.deepcopy(plugin)
        plugin_copy['webhook']['secret'] = '********'
        masked.append(plugin_copy)

    return masked


def protected(
    f: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Decorator to protect a route with authentication.
    Checks if the user is logged in and has admin permissions.

    Uses a local session for user information.
        If the user is not in the session, it checks for a
            token in the request.
        If a token is found, it verifies the token and stores
            the user in the session.
        If the user is not authenticated, it redirects to the auth page.

    Args:
        f (callable): The function to decorate.

    Returns:
        callable: The decorated function that checks authentication.
    """

    @wraps(f)
    def decorated_function(
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """
        Inner function to handle the authentication check.
        Checks if the user is in the session or providing a token.
        If the user is authenticated, it calls the original function.
        If the user is not authenticated, it redirects to the auth page.

        Args:
            *args: Positional arguments for the original function.
            **kwargs: Keyword arguments for the original function.

        Returns:
            Response: The response from the original function if authenticated,
        """

        # Check if there's a token in the request
        token = request.args.get('token')

        # User is providing a token, but is not in the session yet
        #   They have authenticated and been given a token
        #   Verify that the token is valid
        if 'user' not in session and token:
            # Get the secret key from the app config
            secret_key = current_app.config.get('SECRET_KEY', '')

            # Verify the token
            user = verify_auth_token(token, secret_key)

            # If the token is valid, store the user in the session
            if user:
                session['user'] = user

                # Strip token from URL after successful authentication
                clean_url = request.base_url

                if args:
                    clean_url += '?' + urlencode(args)

                # Simple redirection to the original URL without the token
                return make_response(
                    f"""
                    <html>
                      <head>
                        <script>
                          window.location.replace("{clean_url}");
                        </script>
                      </head>
                      <body>
                        Redirecting...
                      </body>
                    </html>
                    """
                )

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
            return cast(
                Response,
                redirect(
                    f"/auth?redirect={request.url}"
                )
            )

        # User is already authenticated (user is in the session)
        return f(*args, **kwargs)

    return decorated_function


@web_routes.route(
    '/',
    methods=['GET']
)
def index() -> str:
    '''
    Just so a home page exists.
    Some external security services require a home page to be present.

    Returns:
        str: A simple message indicating the home page.
    '''

    return "I'd like to speak to the manager!"


@web_routes.route(
    '/close',
    methods=['GET']
)
def close() -> Response:
    '''
    The page to display when the service account has logged in.
    This just tells them that the service account is logged in
        and they can close the page.

    Returns:
        Response: A redirect to the home page.
    '''

    # Redirect to the home page
    return make_response(
        render_template(
            'close.html',
            title="Close",
        )
    )


@web_routes.route(
    '/config',
    methods=['GET']
)
@protected
def config() -> Response:
    '''
    Route to display the configuration page.
    Gets global configuration and passes it to the template.

    Returns:
        Rendered template for the configuration page.
    '''

    # Get the config object
    app_config = {}
    with Config(CONFIG_URL) as config:
        app_config = config.read()

    return make_response(
        render_template(
            'config.html',
            title="Config",
            config=app_config,
        )
    )


@web_routes.route(
    '/about',
    methods=['GET']
)
@protected
def about() -> Response:
    '''
    Route to display the about page.
    Displays various useful information about the application
    Allows the user to see if the Azure service account is authenticated.
        Also provides a link to the service account login page.

    Returns:
        Rendered template for the about page with application information.
    '''

    # Make an API call to the container service to get container info
    try:
        container_response = requests.get(CONTAINER_URL, timeout=3)
        container_status = container_response.json()['services']

    except Exception as e:
        logging.error("Error fetching container info: %s", e)
        container_status = None

    # Get the URL that was entered and extract the domain part
    entered_url = request.url
    parsed_url = urlparse(entered_url)
    entered_domain = parsed_url.hostname

    # Check if the Azure service account is authenticated
    response = None
    try:
        response = requests.get(TOKEN_URL, timeout=3)

    except Exception as e:
        logging.error(
            "Failed to check Azure service account authentication: %s", e
        )

    if response and response.status_code == 200:
        logging.debug("/about: Azure service account is authenticated")
        logged_in = True

    else:
        logging.warning("/about: Azure service account is not authenticated")
        logged_in = False

    # Get the login URL for the service account
    service_login_url = f"https://{entered_domain}/login?prompt=login"

    # Get the service account from the global config
    app_config = {}
    with Config(CONFIG_URL) as config:
        app_config = config.read()

    service_account = app_config['teams']['user']

    # Get plugin information (with secrets masked)
    plugin_list = []
    with PluginManager(PLUGINS_URL) as plugin_manager:
        plugin_list = plugin_manager.read()

    masked_plugin_list = mask_secrets(plugin_list)

    return make_response(
        render_template(
            'about.html',
            title="About",
            service_account=service_account,
            logged_in=logged_in,
            service_login_url=service_login_url,
            container_status=container_status,
            full_config=app_config,
            full_plugins=masked_plugin_list,
        )
    )


@web_routes.route(
    '/alerts',
    methods=['GET']
)
@protected
def alerts() -> Response:
    '''
    Route to display the alerts page.
    Gets the recent alerts from the logger and passes them to the template.

    The alerts are paginated, with a default page size of 200.
    The total number of alerts and pages is calculated.
    The page number is taken from the request arguments, defaulting to 1.

    Returns:
        Rendered template for the alerts page with recent alerts and filters.
    '''

    search = request.args.get('search', '').strip()
    system_only = request.args.get('system_only') == '1'
    source = request.args.get('source', '')
    group = request.args.get('group', '')
    category = request.args.get('category', '')
    alert = request.args.get('alert', '')
    severity = request.args.get('severity', '')
    page_number = request.args.get('page', 1, type=int)
    page_size = 200

    params = {
        'search': search if search else None,
        'system_only': system_only if system_only else None,
        'source': source if source else None,
        'group': group if group else None,
        'category': category if category else None,
        'alert': alert if alert else None,
        'severity': severity if severity else None,
        'page': page_number if page_number else None,
        'page_size': page_size if page_size else None,
    }

    # API call to get live alerts
    try:
        response = requests.get(LIVE_ALERTS_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            total_pages = data.get('total_pages')
            total_logs = data.get('total_logs')
        else:
            alerts = []
            total_logs = 0
            total_pages = 1
            logging.warning("Failed to fetch alerts: %s", response.text)

    except Exception as e:
        alerts = []
        total_logs = 0
        total_pages = 1
        logging.error("Error accessing the live alerts API: %s", e)

    # Extract unique values for each field
    source_list = sorted({event[1] for event in alerts})
    group_list = sorted({event[2] for event in alerts})
    category_list = sorted({event[3] for event in alerts})
    alert_list = sorted({event[4] for event in alerts})

    return make_response(
        render_template(
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
    )


@web_routes.route(
    '/plugins',
    methods=['GET']
)
@protected
def plugins() -> Response:
    '''
    Route to display the plugins page.
    Gets the plugin list object from the core service.
    Passes the plugin configuration to the template.

    Returns:
        Rendered template for the plugins page with plugin configuration.
    '''

    # Fetch the plugin list from the core API
    try:
        response = requests.get(
            PLUGINS_URL,
            headers={"X-Plugin-Name": "all"},
            timeout=3
        )
        if response.status_code == 200:
            plugin_list = response.json()['plugins']
            logging.debug("Fetched plugins from API: %s", plugin_list)

        else:
            plugin_list = {}
            logging.warning(
                "Failed to fetch plugins from API:\n %s",
                response.text
            )

    except Exception as e:
        plugin_list = {}
        logging.error("Error accessing the plugins API: %s", e)

    logging.debug("Plugin list loaded: %s", plugin_list)

    return make_response(
        render_template(
            'plugins.html',
            title="Plugins",
            plugins=plugin_list,
        )
    )


@web_routes.route(
    '/tools',
    methods=['GET', 'POST']
)
@protected
def tools() -> Response:
    '''
    Route to display the tools page.
    Includes utilities of use.

    Methods:
        GET: Display the tool page as normal
        POST: Process the form submission to encrypt/decrypt

    Returns:
        Rendered template for the tools page.
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
            return make_response(
                render_template(
                    'tools.html',
                    encrypt_encrypted=encrypt_encrypted,
                    encrypt_salt=encrypt_salt,
                    encrypt_error=encrypt_error,
                    decrypt_plain=decrypt_plain,
                    decrypt_error=decrypt_error,
                )
            )

        try:
            response = requests.post(
                CRYPTO_URL,
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

    # Fetch the chat list from the Teams API
    chat_list = []
    try:
        response = requests.get(CHAT_LIST_URL, timeout=5)

        # Check the response
        if response.status_code == 200:
            logging.debug("/tools: Chat list response: %s", response.text)
            chat_list = response.json().get('chats', [])

        # Bad response from the API
        else:
            logging.warning("Failed to fetch chat list: %s", response.text)

    # API error handling
    except Exception as e:
        logging.error("Error accessing the chat list API:\n%s", e)

    # Display the page
    return make_response(
        render_template(
            'tools.html',
            encrypt_encrypted=encrypt_encrypted,
            encrypt_salt=encrypt_salt,
            encrypt_error=encrypt_error,
            decrypt_plain=decrypt_plain,
            decrypt_error=decrypt_error,
            chat_list=chat_list,
        )
    )


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
