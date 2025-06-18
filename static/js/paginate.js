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
    // Parse current query parameters
    const params = new URLSearchParams(window.location.search);

    // Set the new page number
    params.set('page', page);

    // Update the URL with all filters preserved
    window.location.search = '?' + params.toString();
}
