/**
 * Track Options Component
 * A modular, reusable component for track actions (Add to Library, View Details, etc.)
 */
class TrackOptions {
    constructor() {
        this.activeMenu = null;
        this.activeContainer = null;
        this.handleClickOutside = this.handleClickOutside.bind(this);
        document.addEventListener('click', this.handleClickOutside);
    }

    /**
     * Create the track options menu button and dropdown
     * @param {Object} track - Track data object
     * @returns {HTMLElement} Container element with button and menu
     */
    render(track) {
        const container = document.createElement('div');
        container.className = 'relative inline-block text-left track-options-container';

        // 1. Create Trigger Button (Kebab Icon)
        const button = document.createElement('button');
        button.className = 'p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400 focus:outline-none';
        button.innerHTML = '<span class="material-symbols-outlined">more_vert</span>';
        button.setAttribute('aria-label', 'Track Options');
        button.onclick = (e) => {
            e.stopPropagation();
            this.toggleMenu(menu, container);
        };

        // 2. Create Dropdown Menu
        const menu = document.createElement('div');
        menu.className = 'template-context-menu absolute right-0 mt-2 w-48 bg-white dark:bg-surface-dark rounded-lg shadow-xl z-[2000] hidden origin-top-right';
        
        // Menu Items
        const menuItems = [
            {
                icon: 'library_add',
                text: 'Add to Library',
                action: () => this.addToLibrary(track),
                class: 'text-primary'
            },
            {
                icon: 'visibility',
                text: 'View Details',
                action: () => this.viewDetails(track)
            },
            {
                icon: 'settings',
                text: 'Studio Settings',
                action: () => window.location.href = '/' // Assuming root is studio
            },
            {
                icon: 'person',
                text: 'User Profile',
                action: () => window.location.href = '/profile' // Need to confirm route, but safer to use simple link
            }
        ];

        menuItems.forEach(item => {
            const btn = document.createElement('button');
            btn.className = `context-menu-item w-full text-left px-4 py-2 text-sm flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 ${item.class || ''}`;
            btn.innerHTML = `<span class="material-symbols-outlined text-lg">${item.icon}</span>${item.text}`;
            btn.onclick = (e) => {
                e.stopPropagation();
                item.action();
                this.closeMenu(menu, container);
            };
            menu.appendChild(btn);
        });

        container.appendChild(button);
        container.appendChild(menu);

        return container;
    }

    /**
     * Toggle menu visibility
     * @param {HTMLElement} menu 
     * @param {HTMLElement} container
     */
    toggleMenu(menu, container) {
        // Close any other open menus first
        if (this.activeMenu && this.activeMenu !== menu) {
            this.closeMenu(this.activeMenu, this.activeContainer);
        }

        const isHidden = menu.classList.contains('hidden');
        if (isHidden) {
            // Calculate position relative to viewport
            const rect = container.getBoundingClientRect();
            
            // Move menu to body to avoid stacking context issues
            document.body.appendChild(menu);
            
            // Show first to measure dimensions
            menu.classList.remove('hidden');
            
            const menuWidth = menu.offsetWidth || 192; // Fallback to w-48 (12rem)
            
            // Position absolutely on the page
            menu.style.position = 'absolute';
            menu.style.top = `${rect.bottom + window.scrollY + 5}px`; // 5px gap
            menu.style.left = `${rect.right + window.scrollX - menuWidth}px`; // Align right edge
            menu.style.zIndex = "9999"; // Very high z-index
            
            menu.classList.add('animate-slide-in');
            
            this.activeMenu = menu;
            this.activeContainer = container;
        } else {
            this.closeMenu(menu, container);
        }
    }

    /**
     * Close the menu
     * @param {HTMLElement} menu
     * @param {HTMLElement} container
     */
    closeMenu(menu, container) {
        if (!menu) return;
        
        menu.classList.add('hidden');
        menu.classList.remove('animate-slide-in');
        
        // Reset styles added for portal positioning
        menu.style.position = '';
        menu.style.top = '';
        menu.style.left = '';
        menu.style.zIndex = '';
        
        // Move back to original container if provided
        const cont = container || this.activeContainer;
        if (cont && !cont.contains(menu)) {
            cont.appendChild(menu);
        }

        if (this.activeMenu === menu) {
            this.activeMenu = null;
            this.activeContainer = null;
        }
    }

    /**
     * Handle click outside to close menu
     * @param {Event} e 
     */
    handleClickOutside(e) {
        if (this.activeMenu && !e.target.closest('.track-options-container')) {
            this.closeMenu(this.activeMenu, this.activeContainer);
        }
    }

    /**
     * Add track to library (persistence logic)
     * @param {Object} track 
     */
    async addToLibrary(track) {
        if (!track) return;

        // Show toast/notification
        if (window.NotificationSystem) {
            window.NotificationSystem.showInfo('Adding track to library...');
        } else {
            console.log('Adding track to library...');
        }

        try {
            // Prepare audio library entry data
            const audioUrl = track.audioUrl || track.audio_url ||
                             (track.audio_urls && track.audio_urls.generated) ||
                             track.sourceAudioUrl || track.source_audio_url ||
                             (track.audio_urls && track.audio_urls.source) ||
                             track.streamAudioUrl || track.stream_audio_url ||
                             (track.audio_urls && track.audio_urls.source_stream) ||
                             track.download_url || '';
            const libraryData = {
                title: track.title || 'Untitled Track',
                artist: track.artist || 'Unknown Artist',
                album: track.album || '',
                genre: track.genre || 'Unknown',
                duration: track.duration || 0,
                file_size: track.file_size || 0,
                source_type: track.source_type || 'history',
                audio_url: audioUrl,
                metadata: {
                    original_data: track,
                    added_via: 'track_options'
                }
            };

            const response = await fetch('/api/audio-library', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(libraryData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                if (window.NotificationSystem) {
                    window.NotificationSystem.showSuccess('Track added to library successfully!');
                } else {
                    alert('Track added to library successfully!');
                }
                
                // Notify other components that library has been updated
                const newAudioItem = data.data.audio_item;
                // Notify other components that library has been updated
                const updateEvent = new CustomEvent('audioLibraryUpdated', {
                    detail: { action: 'added', track: newAudioItem }
                });
                document.dispatchEvent(updateEvent);
            } else {
                throw new Error(data.error || 'Failed to add track to library');
            }
        } catch (error) {
            console.error('Error adding to library:', error);
            if (window.NotificationSystem) {
                window.NotificationSystem.showError(`Failed to add to library: ${error.message}`);
            } else {
                alert(`Failed to add to library: ${error.message}`);
            }
        }
    }

    /**
     * View Details Action
     * Uses existing modal logic if available, or dispatches event
     * @param {Object} track 
     */
    viewDetails(track) {
        // Dispatch a custom event that HistoryManager or other components can listen to
        const event = new CustomEvent('viewTrackDetails', { detail: track });
        document.dispatchEvent(event);
        
        // Also try standard global method if it exists (legacy support)
        if (window.showTrackDetails) {
            window.showTrackDetails(track);
        }
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TrackOptions;
} else {
    window.TrackOptions = TrackOptions;
}
