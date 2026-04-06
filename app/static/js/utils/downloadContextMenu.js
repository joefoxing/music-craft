/**
 * Download Context Menu Component
 * Reusable context menu for download buttons with convert to WAV option
 */

class DownloadContextMenu {
    constructor() {
        this.currentMenu = null;
        this.currentButton = null;
    }

    /**
     * Create and attach context menu to a download button
     * @param {HTMLElement} button - The download button
     * @param {Object} options - Configuration options
     *   - taskId: Required for KIE API conversion
     *   - audioId: Required for KIE API conversion
     *   - filename: Download filename without extension
     *   - onConvertClick: Custom callback for convert action
     */
    attachToButton(button, options = {}) {
        if (!button) return;

        // Create context menu HTML
        const menu = this.createMenuElement(options);
        
        // Insert menu as sibling to button
        button.parentElement.style.position = 'relative';
        button.parentElement.insertBefore(menu, button.nextSibling);

        // Attach click handler to button
        button.addEventListener('contextmenu', (e) => this.showMenu(e, menu, options));
        
        // Also allow toggle with a small dropdown arrow if button has icon
        this.addMenuToggle(button, menu, options);

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!menu.contains(e.target) && !button.contains(e.target)) {
                this.hideMenu(menu);
            }
        });
    }

    /**
     * Create the context menu DOM element
     * @param {Object} options - Menu options
     * @returns {HTMLElement} Menu element
     */
    createMenuElement(options) {
        const menu = document.createElement('div');
        menu.className = 'download-context-menu absolute right-0 top-full mt-1 bg-white dark:bg-[#1a1a22] border border-slate-200 dark:border-[#2a2a36] rounded-lg shadow-xl z-50 hidden min-w-[200px]';
        menu.innerHTML = `
            <div class="py-1">
                <button class="download-as-mp3 w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-[#23232e] flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined text-sm">download</span>
                    <span>Download MP3</span>
                </button>
                <button class="convert-to-wav w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-[#23232e] flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined text-sm">audio_file</span>
                    <span>Convert to WAV</span>
                </button>
            </div>
        `;

        // Set up button handlers
        const mp3Btn = menu.querySelector('.download-as-mp3');
        const wavBtn = menu.querySelector('.convert-to-wav');

        if (mp3Btn) {
            mp3Btn.addEventListener('click', () => {
                this.hideMenu(menu);
                if (options.onMP3Click) {
                    options.onMP3Click();
                } else {
                    // Trigger the original download button click
                    const origBtn = menu.parentElement.querySelector('[data-download-btn], .btn-download, .download-audio-btn, .song-download-btn');
                    if (origBtn) origBtn.click();
                }
            });
        }

        if (wavBtn) {
            wavBtn.addEventListener('click', () => {
                this.hideMenu(menu);
                this.handleWavConversion(options);
            });
        }

        return menu;
    }

    /**
     * Add a menu toggle button/icon next to the download button
     * @param {HTMLElement} button - Original button
     * @param {HTMLElement} menu - Menu element
     * @param {Object} options - Options
     */
    addMenuToggle(button, menu, options) {
        // Create a small container with both button and menu toggle
        const container = button.parentElement;
        
        // You can optionally add a dropdown arrow or create a separate menu toggle button
        // For now, we'll rely on right-click and the MP3 button click
    }

    /**
     * Handle WAV conversion
     * @param {Object} options - Conversion options
     */
    async handleWavConversion(options) {
        const { taskId, audioId, filename = 'converted' } = options;

        // Check if service is available and configured
        if (!window.WavConversionService || !window.WavConversionService.isConfigured()) {
            window.NotificationSystem?.showError('WAV conversion is not available. API not configured.');
            return;
        }

        if (!taskId || !audioId) {
            window.NotificationSystem?.showError('Unable to convert: missing task or audio ID');
            return;
        }

        try {
            window.NotificationSystem?.showInfo('Starting WAV conversion...');

            await window.WavConversionService.convertToWav(
                taskId,
                audioId,
                filename,
                (progress) => {
                    if (progress.status === 'completed') {
                        window.NotificationSystem?.showSuccess('WAV conversion complete! Download started.');
                    } else if (progress.status === 'error') {
                        window.NotificationSystem?.showError(`Conversion error: ${progress.message}`);
                    }
                }
            );
        } catch (error) {
            console.error('WAV conversion error:', error);
            window.NotificationSystem?.showError(`Conversion failed: ${error.message}`);
        }
    }

    /**
     * Show the context menu
     * @param {Event} event - Right-click event
     * @param {HTMLElement} menu - Menu element
     * @param {Object} options - Options
     */
    showMenu(event, menu, options) {
        event.preventDefault();
        event.stopPropagation();

        // Hide previous menu if open
        if (this.currentMenu && this.currentMenu !== menu) {
            this.hideMenu(this.currentMenu);
        }

        menu.classList.remove('hidden');
        this.currentMenu = menu;
    }

    /**
     * Hide the context menu
     * @param {HTMLElement} menu - Menu element
     */
    hideMenu(menu) {
        if (menu) {
            menu.classList.add('hidden');
        }
    }

    /**
     * Destroy and clean up a menu
     * @param {HTMLElement} menu - Menu element
     */
    destroyMenu(menu) {
        if (menu) {
            menu.remove();
        }
    }
}

// Create singleton instance
window.DownloadContextMenu = new DownloadContextMenu();
