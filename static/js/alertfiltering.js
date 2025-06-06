/*
==========================================================================
    alertfiltering.js
    - Used in alerts.html
    - Provides filtering functionality for alerts/logs tables
==========================================================================
*/


/**
 * Toggles the visibility of the filtering panel.
 * Changes the caret icon direction based on the panel's visibility.
 * 
 * @returns {void}
 */
function toggleFiltering() {
    var panel = document.getElementById('filtering-panel');
    var caret = document.getElementById('filtering-caret');
    if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'block';
        caret.classList.remove('fa-caret-down');
        caret.classList.add('fa-caret-up');
    } else {
        panel.style.display = 'none';
        caret.classList.remove('fa-caret-up');
        caret.classList.add('fa-caret-down');
    }
}
