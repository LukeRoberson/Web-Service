/*
==========================================================================
    saveconfig.js
    - Used in config.html
    - Gets configuration from the UI
    - Makes an API call to save the configuration
==========================================================================
*/


/**
 * Saves the configuration from the specified form.
 * This gets configuration from each category (not the entire page).
 * Form data is sent to the server via a PATCH request.
 * There is no checking to see if the form data has changed.
 * 
 * @param {string} formId - The ID of the form to save.
 */
function saveConfig(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const data = {};

    // Determine the category based on the form ID
    // Web-interface uses this to determine which category to save
    let category = "";
    if (formId === "azure-form") {
        category = "azure";
    } else if (formId === "auth-form") {
        category = "authentication";
    } else if (formId === "teams-form") {
        category = "teams";
    } else if (formId === "sql-form") {
        category = "sql";
    } else if (formId === "web-form") {
        category = "web";
    }

    // Convert FormData to a plain object
    formData.forEach((value, key) => {
        // For checkboxes, set true/false
        const input = form.elements[key];
        if (input && input.type === "checkbox") {
            data[key] = input.checked;
        } else {
            data[key] = value;
        }
    });
    data.category = category;

    // Explicitly set web_debug (even if unchecked)
    // By default, web_debug is not sent in the request if 'false'
    if (formId === "web-form") {
        const debugCheckbox = form.elements['web_debug'];
        data['web_debug'] = debugCheckbox ? debugCheckbox.checked : false;
    }

    // API call to save the configuration
    fetch('/api/config', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            alert('Configuration saved!');
        } else {
            alert('Failed to save configuration.');
        }
    });
}
