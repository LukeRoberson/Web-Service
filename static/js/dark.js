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
    const root = document.documentElement;
    
    // Load preference
    if (localStorage.getItem('darkMode') === 'true') {
        root.classList.add('dark-mode');
        toggle.checked = true;
    } else {
        root.classList.remove('dark-mode');
        toggle.checked = false;
    }

    toggle.addEventListener('change', function() {
        if (toggle.checked) {
            root.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
        } else {
            root.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'false');
        }
    });
});

