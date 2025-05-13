# Overview

The web interface for the application

Uses Flask as the web server, and HTML/CSS/TypeScript for the UI


## Modules

| Module | Usage                    |
| ------ | ------------------------ |
| Flask  | Web framework            |
| PyYAML | Read and save YAML files |


## Container

To build the container (replace 'username' with a real name):

```
docker build -t <username>/web-interface:latest .
```


</br></br>
To run the container:

```
docker run -p 80:5000 web-interface
```




</br></br>
---

# Folder Structure

| Folder     | Usage                          |
| ---------- | ------------------------------ |
| /          | Main location for python files |
| /templates | HTML template files            |
| /static    | CSS files                      |
| /config    | YAML config files              |


</br></br>
---

# Python Files

| File      | Usage                               |
| --------- | ----------------------------------- |
| main.py   | Main file for the app. Starts Flask |
| config.py | Manages app configuration           |


</br></br>
---

# Configuration Files

| File         | Usage                                     |
| ------------ | ----------------------------------------- |
| global.yaml  | Global configuration items                |
| plugins.yaml | A list of plugins and their configuration |


</br></br>
---

# Web UI Files
## HTML Templates

| File         | Usage                                 |
| ------------ | ------------------------------------- |
| base.html    | Base template. Implements the nav bar |
| about.html   | Information about the app as a whole  |
| alerts.html  | Live alerts from the app and plugins  |
| config.html  | Configuration for the app             |
| plugins.html | Manage plugins (add, remove, config)  |


## Style Sheets

| File      | Usage                          |
| --------- | ------------------------------ |
| style.css | Base style sheet for all pages |
