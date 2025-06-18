# API
## Endpoints

There is an API in place so other services can access the web interface when required.

| Endpoint           | Methods                  | Description                                    |
| ------------------ | ------------------------ | ---------------------------------------------- |
| /api/health        | GET                      | Check the health of the container              |
| /api/plugins       | GET, POST, PATCH, DELETE | Plugin CRUD operations                         |
| /api/config        | GET, PATCH               | Retrieve and update global configuration       |
</br></br>

> [!NOTE]  
> The API for plugins and configuration is for JS functions to access when loading/saving configuration information from the web page.
> The WebUI still needs to interact with the **Core Service** which manages plugins and configuration.
</br></br>


## Responses

Unless otherwise specified, all endpoints have a standard JSON response, including a '200 OK' message if everything is successful.

A successful response:
```json
{
    'result': 'success'
}
```

An error:
```json
{
    "result": "error",
    "error": "A description of the error"
}
```
</br></br>


### Health

This is for checking that Flask is responding from the localhost, so Docker can see if this is up.

This just returns a '200 OK' response.
</br></br>


## Endpoint Details
### Plugins

This API will interact with the Core Service, which manages plugins.

**GET** Request: Returns configuration information (dictionary) for a specific plugin.

Returns:
```JSON
{
    "result": "success",
    "plugin": "<[dict]>
}
```
</br></br>


**POST** Request: Adds a new plugin.

This expects the message body to contain configuration information about the plugin.

A '201 Created' message is returned on success.
</br></br>


**PATCH** Request: Updates an existing plugin's configuration.

This expects the message body to contain configuration information about the plugin.
</br></br>


**DELETE** Request: Deletes a plugin.

This just requires the name of a plugin in the request body.
</br></br>


### Config

This API is also for sharing information with the web interface. This required interaction with the **Core Service**.


A **GET** request is used to populate the /config page.

A successful response will contain a dictionary of configuration information:
```JSON
{
    "result": "success",
    "config": "<[dict]>
}
```
</br></br>


A **PATCH** request is to update the configuration. The body of the request needs to contain the configuration information.

