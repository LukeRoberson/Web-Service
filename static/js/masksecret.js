/*
==========================================================================
    masksecret.js
    - Used whenever a secret needs to be masked (config, plugins, etc.)
    - Places an eye icon next to the input field
    - Toggles the visibility of the secret when clicked
==========================================================================
*/

/**
 * 
 * @param {*} inputId - The ID of the input field to toggle visibility for
 * @param {*} btn - The button element that toggles visibility
 */
function toggleSecretVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        btn.innerHTML = '<i class="fa fa-eye-slash"></i>';
    } else {
        input.type = "password";
        btn.innerHTML = '<i class="fa fa-eye"></i>';
    }
}
