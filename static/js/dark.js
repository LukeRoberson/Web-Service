/*
==========================================================================
    dark.js
    - Used on the nav bar
    - Toggles the dark mode
==========================================================================
*/

/**
 * Event listener for the dark mode toggle
 * 
 * @param {Event} event - The event object
 * @param {HTMLElement} toggle - The toggle element
 */

document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('darkModeToggle');
    // Load preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        toggle.checked = true;
    }
    toggle.addEventListener('change', function() {
        if (toggle.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'false');
        }
    });
});

