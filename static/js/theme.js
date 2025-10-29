document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');

    // Function to update icons based on the current theme
    const updateIcons = () => {
        if (document.documentElement.classList.contains('dark')) {
            darkIcon.classList.remove('hidden');
            lightIcon.classList.add('hidden');
        } else {
            darkIcon.classList.add('hidden');
            lightIcon.classList.remove('hidden');
        }
    };

    // Set initial theme and icons
    // The initial theme is set by an inline script in base.html to prevent FOUC
    updateIcons();

    // Add click listener to the button
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            // Toggle the 'dark' class on the html element
            document.documentElement.classList.toggle('dark');

            // Update localStorage
            if (document.documentElement.classList.contains('dark')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }

            // Update icons
            updateIcons();
        });
    }
});
