/*
==========================================================================
    dark-head.js
    - Used in the head of base.html
    - Enables dark mode based on user preference
    - Checks localStorage for dark mode preference
    - Works alongside dark.js
==========================================================================
*/

if (localStorage.getItem('darkMode') === 'true') {
    document.documentElement.classList.add('dark-mode');
}
