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
            'allowed-ip': form.ip.value.split(',').map(ip => ip.trim())
        }
    };

    // API call - PATCH to the web-interface
    fetch('/api/plugins', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(response => response.json())
    
    // Handle the response
    .then(result => {
        if (result.result === 'success') {
            alert('Saved!');
            modal.style.display = 'none';
            
            // Reload the page to reflect changes
            location.reload();
        } else {
            alert('Save failed!');
        }
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
            'allowed-ip': form.ip.value.split(',').map(ip => ip.trim())
        }
    };

    // API call - POST to the web-interface
    fetch('/api/plugins', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(response => response.json())
    
    // Handle the response
    .then(result => {
        if (result.result === 'success') {
            alert('Saved!');
            modal.style.display = 'none';
            
            // Reload the page to reflect changes
            location.reload();
        } else {
            alert('Save failed!');
        }
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
    }).then(response => response.json())
    
    // Handle the response
    .then(result => {
        if (result.result === 'success') {
            alert('Deleted!');
            
            // Reload the page to reflect changes
            location.reload();
        } else {
            alert('Delete failed!');
        }
    });
}
