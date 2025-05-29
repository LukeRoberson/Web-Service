/*
==========================================================================
    paginate.js
    - Used in alerts.html
    - Allows pagination of alerts/logs tables
    - Manages navigating through pages of data
==========================================================================
*/

/**
 * Handles pagination of the table by updating the page number in the URL.
 * @param {number} page - The page number to navigate to.
 */
function goToPage(page) {
    window.location.search = `?page=${page}`;
}
