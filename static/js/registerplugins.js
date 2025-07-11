/*
==========================================================================
    registerplugins.js
    - Used in plugins.html
    - Handles the registration and configuration of plugins
    - Allows adding, updating, and deleting plugins
==========================================================================
*/


/**
 * Function to update the plugin configuration
 * 
 * @param {number} index - The index of the plugin in the list
 */
function updatePlugin(index) {
    const modal = document.getElementById('modal-' + index);
    const form = modal.querySelector('form');
    
    // Create the JSON to send in the body
    const data = {
        plugin_name: form.original_name.value,
        name: form.name.value,
        description: form.description.value,
        webhook: {
            url: form.url.value,
            secret: form.secret.value,
            'auth-type': form.authType.value,
            'allowed-ip': form.ip.value.split(',').map(ip => ip.trim())
        }
    };

    // API call - PATCH to the web-interface
    fetch('/api/plugins', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    
    // Handle the response
    .then(response => response.json().then(json => ({
        ok: response.ok,
        result: json.result,
        message: json.message || null
    })))
    .then(({ ok, result, message }) => {
        const isSuccess = ok && result === 'success';
        showConfigMessage(
            isSuccess
                ? (message || 'Plugin updated!')
                : (message || 'Failed to update plugin.'),
            isSuccess ? 'success' : 'fail'
        );

        setTimeout(() => {
            modal.style.display = 'none';
            location.reload();
        }, 2600);
    });
}


/**
 * Function to register a new plugin
 */
function registerPlugin() {
    const modal = document.getElementById('modal-register');
    const form = modal.querySelector('form');
    
    // Create the JSON to send in the body
    const data = {
        name: form.name.value,
        description: form.description.value,
        webhook: {
            url: form.url.value,
            secret: form.secret.value,
            'auth-type': form.authType.value,
            'allowed-ip': form.ip.value.split(',').map(ip => ip.trim())
        }
    };

    // API call - POST to the web-interface
    fetch('/api/plugins', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    
    // Handle the response
    .then(response => response.json().then(json => ({
        ok: response.ok,
        result: json.result,
        message: json.message || null
    })))
    .then(({ ok, result, message }) => {
        const isSuccess = ok && result === 'success';
        showConfigMessage(
            isSuccess
                ? (message || 'Plugin added!')
                : (message || 'Failed to add plugin.'),
            isSuccess ? 'success' : 'fail'
        );

        setTimeout(() => {
            modal.style.display = 'none';
            location.reload();
        }, 2600);
    });
}


/**
 * Function to delete a new plugin
 * 
 * @param {string} name - The name of the plugin to delete
 */
function deletePlugin(name) {
    // Create the JSON to send in the body
    const data = {
        name: name,
    };

    // API call - DELETE to the web-interface
    fetch('/api/plugins', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    
    // Handle the response
    .then(response => response.json().then(json => ({
        ok: response.ok,
        result: json.result,
        message: json.message || null
    })))
    .then(({ ok, result, message }) => {
        const isSuccess = ok && result === 'success';
        showConfigMessage(
            isSuccess
                ? (message || 'Plugin deleted!')
                : (message || 'Failed to delete plugin.'),
            isSuccess ? 'success' : 'fail'
        );

        setTimeout(() => {
            location.reload();
        }, 2600);
    });
}


/**
 * Displays a message to the user indicating success or failure of the save operation.
 * 
 * @param {string} message - The message to display.
 * @param {string} type - The type of message ('success' or 'fail').
 */
function showConfigMessage(message, type) {
    const msgDiv = document.getElementById('config-message');
    
    msgDiv.textContent = message;
    msgDiv.style.display = 'block';
    msgDiv.style.background = type === 'success' ? '#4CAF50' : '#f44336'; // green or red
    msgDiv.style.color = '#fff';
    msgDiv.style.opacity = '1';
    msgDiv.style.transition = 'opacity 0.8s';

    /* Display the message for 2 seconds, then fade out */
    setTimeout(() => {
        msgDiv.style.opacity = '0';
    }, 1800);

    setTimeout(() => {
        msgDiv.style.display = 'none';
        msgDiv.style.opacity = '1';
    }, 2600);
}


/**
 * Clears the form fields in a modal.
 * Used to reset the form when the user cancels or closes the modal.
 * 
 * @param {*} modalId - The ID of the modal to clear the form in.
 */
function clearForm(modalId) {
    const modal = document.getElementById(modalId);
    const form = modal.querySelector('form');
    if (form) {
        form.reset(); // Resets all form fields to their default values
    }
}


/**
 * Function to confirm and delete a plugin
 * 
 * @param {string} name - The name of the plugin to delete
 */
function confirmDeletePlugin(name) {
    const confirmation = confirm(`Are you sure you want to delete the plugin "${name}"?`);
    if (confirmation) {
        deletePlugin(name);
    }
}