# WebUI Service

The web interface for the application.

Uses Flask as the web framework, and HTML/CSS/JS for the UI.

uWSGI is used as the web server.
</br></br>

> [!NOTE]  
> Additional documentation can be found in the **docs** folder
</br></br>



----
# Project Organization
## Python Files

| File          | Provided Function                                             |
| ------------- | ------------------------------------------------------------- |
| main.py       | Entry point to the service, load configuration, set up routes |
| web.py        | Web routes for the main web page                              |
| api.py        | API endpoints for this service                                |
| livealerts.py | Manage live alerts which are shown on the 'alerts' page       |
</br></br>


## Folder Structure

| Folder      | Usage                          |
| ----------- | ------------------------------ |
| /           | Main location for python files |
| /templates  | HTML template files            |
| /static/css | CSS files                      |
| /static/js  | JavaScript files               |
</br></br>



----
# Web Server
## NGINX

The frontend of the application as a whole is an NGINX container. This adds security to the web interface, including:
* Certificates
* Secure Ciphers
* HSTS and other best practices
</br></br>


## uWSGI

In the containerised environment, uWSGI is the web server. This means the uWSGI module starts the web service and listens for requests.

Requests from outside the stack reach NGINX, which then proxies the requests to the web-interface service using the WSGI protocol.

Requests between containers, which is required for API calls, do not get proxied through NGINX. These are sent directly between containers using the HTTP protocol.
</br></br>


## Webhook Proxy

Webhooks are sent from outside services, which flow through the NGINX front end to the Web UI service. As plugins are loaded, their destination URLs for webhooks are recorded.

The WebUI dynamically creates routes for these webhook URLs. When webhooks are received, they are proxied to the plugin.

> [!NOTE]  
> This should ideally be done directly on the NGINX front-end. However, this requires a premium license (to use the API to dynamically create routes).
</br></br>



----
# Security

Access to the web interface requires authentication. This is managed using an IDP (Azure).

When opening a page for the first time, the user must authenticate with Azure. Their session is stored so they're not challenges on every page.

Azure manages advanced features, such as SSO and MFA. Interaction with Azure is managed by the **Security Service**.

> [!NOTE]  
> Usernames and passwords for web-interface users are not stored in this application.
</br></br>


