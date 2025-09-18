
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

let currentUserRole = 'admin'; // o 'employee'

function initializeApp() {
    try {
        lucide.createIcons();
    } catch (e) {
        console.error("Lucide icons could not be created:", e);
    }
    
    setupMobileMenu();
    setupNotificationPanel();
    updateUserUI();
    setupNavigation();
    // setupGlobalEventListeners(); // Se necesitará adaptar a Django
}

// --- LÓGICA DE LA APLICACIÓN ---



function setupMobileMenu() {
    const openBtn = document.getElementById('open-mobile-menu');
    const closeBtn = document.getElementById('close-mobile-menu');
    const overlay = document.getElementById('mobile-overlay');
    
    if (openBtn && closeBtn && overlay) {
        [openBtn, closeBtn, overlay].forEach(el => el.addEventListener('click', toggleMobileMenu));
    }
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('mobile-sidebar');
    const overlay = document.getElementById('mobile-overlay');
    if (sidebar && overlay) {
        sidebar.classList.toggle('sidebar-mobile-open');
        sidebar.classList.toggle('sidebar-mobile-closed');
        overlay.classList.toggle('hidden');
    }
}

function setupNotificationPanel() {
    const toggleBtn = document.getElementById('notification-toggle');
    const panel = document.getElementById('notification-panel');
    if (!toggleBtn || !panel) return;

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && !toggleBtn.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });
}

function updateUserUI() {
    // This function is intentionally left empty. 
    // All UI updates related to user role and identity are handled by server-side Django templates
    // to ensure consistency after page reloads.
}

function setupNavigation() {
    // Lógica para resaltar el link activo basado en la URL actual
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const linkPath = link.getAttribute('href');
        const isActive = linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath));
        if (isActive) {
            link.classList.add('bg-red-600', 'text-white', 'dark:bg-red-700');
            link.classList.remove('text-gray-600', 'dark:text-gray-300', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Funciones de notificación para poder reusarlas
function showNotification(type, title, message, duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notificationId = `notif-${Date.now()}`;
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = 'notification bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 flex items-start gap-4 border-l-4';

    const icons = {
        success: { icon: 'check-circle-2', color: 'border-green-500', iconColor: 'text-green-500' },
        error: { icon: 'x-circle', color: 'border-red-500', iconColor: 'text-red-500' },
        warning: { icon: 'alert-triangle', color: 'border-yellow-500', iconColor: 'text-yellow-500' },
        info: { icon: 'info', color: 'border-blue-500', iconColor: 'text-blue-500' }
    };

    const config = icons[type] || icons.info;
    notification.classList.add(config.color);

    notification.innerHTML = `
        <div class="flex-shrink-0">
            <i data-lucide="${config.icon}" class="${config.iconColor}"></i>
        </div>
        <div class="flex-1">
            <p class="font-semibold text-sm text-gray-900 dark:text-white">${title}</p>
            <p class="text-sm text-gray-600 dark:text-gray-400">${message}</p>
        </div>
        <div class="flex-shrink-0">
            <button onclick="closeNotification('${notificationId}')" class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 -mt-1 -mr-1"><i data-lucide="x" class="w-4 h-4"></i></button>
        </div>
    `;

    container.appendChild(notification);
    lucide.createIcons();

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function closeNotification(notificationId) {
    const notification = document.getElementById(notificationId);
    if (notification) {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }
}
