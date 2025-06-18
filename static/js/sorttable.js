/*
==========================================================================
    sorttable.js
    - Simple client-side table sorting for alerts/logs tables
    - Used in alerts.html
    - Allows sorting by clicking on column headers
    - Handles string and date columns (first column is treated as date)
    - Reformats timestamps to local time
==========================================================================
*/

/**
 * Sorts the table by the specified column index.
 * 
 * @param {number} n - The column index to sort by (0-based).
 */
function sortTable(n) {
    // 'switching' implements a bubble sort algorithm
    // While it's true, we keep comparing adjacent rows and 'switching' them if needed
    let table = document.querySelector("table");
    let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    switching = true;
    
    // Set the sorting direction to ascending
    dir = "asc"; 

    // Continually compare adjacent rows until no more switches are needed
    while (switching) {
        // If there is no switch after a complete pass, then the table is sorted
        switching = false;
        rows = table.rows;
        
        // Loop through all table rows (except the first, which contains headers)
        for (i = 1; i < (rows.length - 1); i++) {
            // Get the two rows to compare
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            let xContent = x.textContent || x.innerText;
            let yContent = y.textContent || y.innerText;

            // Try to parse as date if sorting the first column
            if (n === 0) {
                xContent = Date.parse(xContent) || xContent;
                yContent = Date.parse(yContent) || yContent;
            }

            // Compare the two rows based on the specified direction
            if (dir == "asc") {
                if (xContent > yContent) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if (xContent < yContent) {
                    shouldSwitch = true;
                    break;
                }
            }
        }

        // If a switch is needed, perform it and mark that a switch has occurred
        // Otherwise, if no switch has occurred and the direction is "asc", set it to "desc"
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount ++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}


/**
 * Formats timestamps in the table to local time.
 * This function is called when the document is fully loaded.
 */
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.alert-timestamp').forEach(function(td) {
        var epoch = parseInt(td.getAttribute('data-epoch'), 10);
        if (!isNaN(epoch)) {
            // Convert to milliseconds for JS Date
            var date = new Date(epoch * 1000);
            // Format as local string
            td.textContent = date.toLocaleString();
        }
    });
});