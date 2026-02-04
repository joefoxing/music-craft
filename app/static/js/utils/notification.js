/**
 * Notification system for the Music Cover Generator application.
 * Provides consistent error and success notifications.
 */

class NotificationSystem {
    /**
     * Show an error notification.
     * @param {string} message - The error message to display
     * @param {number} duration - Duration in milliseconds (default: 5000)
     */
    static showError(message, duration = 5000) {
        console.error('Error:', message);
        this._showNotification(message, 'error', duration);
    }

    /**
     * Show a success notification.
     * @param {string} message - The success message to display
     * @param {number} duration - Duration in milliseconds (default: 5000)
     */
    static showSuccess(message, duration = 5000) {
        console.log('Success:', message);
        this._showNotification(message, 'success', duration);
    }

    /**
     * Show an info notification.
     * @param {string} message - The info message to display
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    static showInfo(message, duration = 3000) {
        console.log('Info:', message);
        this._showNotification(message, 'info', duration);
    }

    /**
     * Show a warning notification.
     * @param {string} message - The warning message to display
     * @param {number} duration - Duration in milliseconds (default: 4000)
     */
    static showWarning(message, duration = 4000) {
        console.warn('Warning:', message);
        this._showNotification(message, 'warning', duration);
    }

    /**
     * Internal method to create and display a notification.
     * @private
     */
    static _showNotification(message, type, duration) {
        // Create notification element
        const notification = document.createElement('div');
        
        // Set base classes
        notification.className = 'fixed top-4 right-4 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md transition-all duration-300 transform translate-x-full opacity-0';
        
        // Set type-specific styling
        const typeConfig = {
            error: {
                bg: 'bg-red-500',
                icon: 'error',
                iconColor: 'text-white'
            },
            success: {
                bg: 'bg-green-500',
                icon: 'check_circle',
                iconColor: 'text-white'
            },
            info: {
                bg: 'bg-blue-500',
                icon: 'info',
                iconColor: 'text-white'
            },
            warning: {
                bg: 'bg-yellow-500',
                icon: 'warning',
                iconColor: 'text-white'
            }
        };
        
        const config = typeConfig[type] || typeConfig.info;
        notification.classList.add(config.bg);
        
        // Create notification content
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="material-symbols-outlined mr-2 ${config.iconColor}">${config.icon}</span>
                <span class="font-medium flex-1">${message}</span>
                <button class="ml-auto text-white hover:text-gray-200 transition-colors" 
                        onclick="this.parentElement.parentElement.remove()">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
            notification.classList.add('translate-x-0', 'opacity-100');
        });
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('translate-x-0', 'opacity-100');
                notification.classList.add('translate-x-full', 'opacity-0');
                
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);
        
        // Add click handler for close button
        const closeBtn = notification.querySelector('button');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('translate-x-0', 'opacity-100');
            notification.classList.add('translate-x-full', 'opacity-0');
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        });
    }

    /**
     * Clear all notifications.
     */
    static clearAll() {
        const notifications = document.querySelectorAll('[class*="fixed top-4 right-4"]');
        notifications.forEach(notification => {
            notification.remove();
        });
    }

    /**
     * Show a loading notification that can be programmatically removed.
     * @param {string} message - The loading message
     * @returns {Function} A function to remove the loading notification
     */
    static showLoading(message = 'Loading...') {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md';
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="material-symbols-outlined mr-2 animate-spin">sync</span>
                <span class="font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Return a function to remove the loading notification
        return () => {
            if (notification.parentElement) {
                notification.remove();
            }
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
} else {
    window.NotificationSystem = NotificationSystem;
}