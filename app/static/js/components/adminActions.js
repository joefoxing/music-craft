/**
 * Admin Actions Component
 * Manages the kebab menu actions (Save, Reset Password, Delete) for the Admin interface.
 * 
 * Usage:
 * const adminActions = new AdminActionsManager();
 * adminActions.renderKebabButton(document.getElementById('toolbar-actions'), {
 *     userId: '123',
 *     onSave: () => saveForm(),
 *     onDelete: () => showDeleteModal()
 * });
 */

class AdminActionsManager {
    constructor() {
        this.activeMenu = null;
        this.activeMenuCloseHandler = null;
    }

    /**
     * Renders the kebab button into a container
     * @param {HTMLElement} container - The element to append the button to
     * @param {Object} options - Configuration options
     * @param {Function} options.onSave - Handler for save action
     * @param {Function} options.onDelete - Handler for delete action
     * @param {string} options.userId - ID of the user (required for password reset)
     */
    renderKebabButton(container, options) {
        if (!container) return;

        const button = document.createElement('button');
        // Styling matching existing icon buttons in the app
        button.className = 'p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:cursor-not-allowed';
        button.setAttribute('aria-label', 'More actions');
        button.innerHTML = '<span class="material-symbols-outlined">more_vert</span>';
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showMenu(button, options);
        });
        
        // Keyboard support
        button.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.showMenu(button, options);
            }
        });

        container.appendChild(button);
        return button;
    }

    showMenu(triggerBtn, options) {
        // Close any existing menu first
        this.closeActiveMenu();

        const menu = document.createElement('div');
        menu.className = 'fixed z-[60] bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-1 min-w-[200px] animate-slide-in';
        menu.setAttribute('role', 'menu');
        
        // Position menu (align top-right of menu with bottom-right of button)
        const rect = triggerBtn.getBoundingClientRect();
        let top = rect.bottom + 5;
        let left = rect.right - 200;
        
        // Viewport boundary checks
        if (left < 10) left = 10;
        if (top + 160 > window.innerHeight) top = rect.top - 160; // Flip up if near bottom
        
        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;

        // Menu Content: Save -> Reset Password -> Divider -> Delete
        menu.innerHTML = `
            <button class="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex items-center gap-3 transition-colors" role="menuitem" data-action="save">
                <span class="material-symbols-outlined text-[20px]">save</span>
                <span class="font-medium">Save</span>
            </button>
            <button class="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex items-center gap-3 transition-colors" role="menuitem" data-action="reset-password">
                <span class="material-symbols-outlined text-[20px]">lock_reset</span>
                <span class="font-medium">Reset password</span>
            </button>
            <div class="h-px bg-slate-100 dark:bg-slate-700 my-1" role="separator"></div>
            <button class="w-full text-left px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors" role="menuitem" data-action="delete">
                <span class="material-symbols-outlined text-[20px]">delete</span>
                <span class="font-medium">Delete</span>
            </button>
        `;

        document.body.appendChild(menu);
        this.activeMenu = menu;

        // Bind Actions
        const saveBtn = menu.querySelector('[data-action="save"]');
        const resetBtn = menu.querySelector('[data-action="reset-password"]');
        const deleteBtn = menu.querySelector('[data-action="delete"]');

        saveBtn.addEventListener('click', () => {
            this.closeActiveMenu();
            if (options.onSave) options.onSave();
        });

        resetBtn.addEventListener('click', () => {
            this.closeActiveMenu();
            this.handleResetPassword(options.userId);
        });

        deleteBtn.addEventListener('click', () => {
            this.closeActiveMenu();
            if (options.onDelete) options.onDelete();
        });

        // Close on click outside
        setTimeout(() => {
            const closeHandler = (e) => {
                if (!menu.contains(e.target) && e.target !== triggerBtn) {
                    this.closeActiveMenu();
                }
            };
            document.addEventListener('click', closeHandler);
            this.activeMenuCloseHandler = closeHandler;
        }, 10);

        // Focus first item for accessibility
        saveBtn.focus();
    }

    closeActiveMenu() {
        if (this.activeMenu) {
            this.activeMenu.remove();
            this.activeMenu = null;
        }
        if (this.activeMenuCloseHandler) {
            document.removeEventListener('click', this.activeMenuCloseHandler);
            this.activeMenuCloseHandler = null;
        }
    }

    async handleResetPassword(userId) {
        if (!userId) {
            this.showNotification('User ID is missing', 'error');
            return;
        }

        this.showNotification('Sending password reset email...', 'info');

        try {
            // Assuming standard API pattern based on audioLibrary.js
            const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showNotification('Password reset email sent successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to reset password');
            }
        } catch (error) {
            console.error('Reset password error:', error);
            this.showNotification(error.message || 'An error occurred', 'error');
        }
    }

    showNotification(message, type) {
        // Utilize global notification helpers if available (from app-modular.js or similar)
        if (typeof showSuccess === 'function' && type === 'success') {
            showSuccess(message);
        } else if (typeof showError === 'function' && (type === 'error' || type === 'warning')) {
            showError(message);
        } else {
            // Fallback if global helpers aren't loaded
            console.log(`[${type.toUpperCase()}] ${message}`);
            alert(message);
        }
    }
}

// Make available globally
window.AdminActionsManager = AdminActionsManager;