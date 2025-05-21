/*
==========================================================================
    autorefresh.js
    - Used to automatically refresh the page every 10 seconds
    - Used in alerts.html
    - Lets the table of alerts/logs be refreshed automatically
==========================================================================
*/

// Holds the interval ID for auto-refresh so it can be cleared later
let autoRefreshInterval = null;


// Wait for the DOM to be fully loaded before accessing elements
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('autoRefreshToggle');

    // Restore toggle state from localStorage if previously set
    if (localStorage.getItem('autoRefresh') === 'on') {
        toggle.checked = true;
        startAutoRefresh();
    }

    // Listen for changes to the auto-refresh toggle
    toggle.addEventListener('change', function() {
        if (toggle.checked) {
            localStorage.setItem('autoRefresh', 'on');
            startAutoRefresh();
        } else {
            localStorage.setItem('autoRefresh', 'off');
            stopAutoRefresh();
        }
    });
});


/**
 * Starts the auto-refresh interval (reloads the page every 10 seconds).
 * Clears any existing interval before starting a new one.
 */
function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(function() {
        location.reload();
    }, 10000); // 10 seconds
}


/**
 * Stops the auto-refresh interval if it is running.
 */
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}
