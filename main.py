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
from config import PluginConfig

# Create the Flask application
app = Flask(__name__)

# Load the plugin configuration
plugin_list = PluginConfig()


@app.route('/config')
def config():
    return render_template(
        'config.html',
        title="Config"
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
    return render_template(
        'alerts.html',
        title="Alerts"
    )


@app.route('/plugins')
def plugins():
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

    data = request.json

    # POST is used to add a new plugin
    if request.method == 'POST':
        result = plugin_list.register(data)

    # PATCH is used to update an existing plugin
    elif request.method == 'PATCH':
        result = plugin_list.update_config(data)

    # DELETE is used to remove a plugin
    elif request.method == 'DELETE':
        result = plugin_list.delete(data['name'])

    if not result:
        return flask.jsonify(
            {
                'result': 'error',
                'message': 'Failed to update configuration'
            }
        )

    return flask.jsonify(
        {
            'result': 'success'
        }
    )


if __name__ == "__main__":
    # Run the application
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
    )
