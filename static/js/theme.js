
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');

    const updateIcons = (theme) => {
        if (darkIcon && lightIcon) {
            darkIcon.classList.toggle('hidden', theme !== 'dark');
            lightIcon.classList.toggle('hidden', theme === 'dark');
        }
    };

    const initialTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    updateIcons(initialTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            const newTheme = isDark ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme);
            updateIcons(newTheme);
        });
    }
});
