"""
Main module for starting the web service and setting up the routes.

Usage:
    Run this module to start the web application.

Example:
    $ python main.py
"""

from flask import Flask, render_template
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


if __name__ == "__main__":
    # Run the application
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
    )
