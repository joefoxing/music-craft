/**
 * ActivityFeed component for the Music Cover Generator application.
 * Displays recent user activities from history and template usage.
 */

class ActivityFeed {
    constructor() {
        this.allActivities = [];
        this.filteredActivities = [];
        
        // DOM Elements (will be initialized by the main app)
        this.feedContainer = null;
        this.loadingState = null;
        this.emptyState = null;
        this.errorState = null;
        this.refreshBtn = null;
        this.filterSelect = null;
        this.searchInput = null;
        this.statsTotal = null;
        this.statsToday = null;
        this.statsTemplates = null;
        this.statsSuccess = null;
        
        // Pagination
        this.currentPage = 1;
        this.pageSize = 10;
        this.hasMore = true;
        
        // Callbacks
        this.onActivityClick = null;
        this.onTemplateApply = null;
    }

    /**
     * Initialize activity feed with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.feedContainer = elements.feedContainer;
        this.loadingState = elements.loadingState;
        this.emptyState = elements.emptyState;
        this.errorState = elements.errorState;
        this.refreshBtn = elements.refreshBtn;
        this.filterSelect = elements.filterSelect;
        this.searchInput = elements.searchInput;
        this.statsTotal = elements.statsTotal;
        this.statsToday = elements.statsToday;
        this.statsTemplates = elements.statsTemplates;
        this.statsSuccess = elements.statsSuccess;

        this._setupEventListeners();
    }

    /**
     * Set up event listeners.
     * @private
     */
    _setupEventListeners() {
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadActivities());
        }

        if (this.filterSelect) {
            this.filterSelect.addEventListener('change', () => this.filterActivities());
        }

        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => this.searchActivities());
        }

        // Infinite scroll
        if (this.feedContainer) {
            this.feedContainer.addEventListener('scroll', () => this.handleScroll());
        }
    }

    /**
     * Show loading state.
     */
    showLoading() {
        if (this.loadingState) this.loadingState.classList.remove('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.feedContainer) this.feedContainer.classList.add('hidden');
    }

    /**
     * Show empty state.
     */
    showEmpty() {
        if (this.loadingState) {
            this.loadingState.classList.add('hidden');
            this.loadingState.style.display = 'none';
        }
        if (this.emptyState) {
            this.emptyState.classList.remove('hidden');
            this.emptyState.style.display = 'block';
        }
        if (this.errorState) {
            this.errorState.classList.add('hidden');
            this.errorState.style.display = 'none';
        }
        if (this.feedContainer) {
            this.feedContainer.classList.add('hidden');
            this.feedContainer.style.display = 'none';
        }
    }

    /**
     * Show error state.
     * @param {string} message - Error message to display
     */
    showError(message) {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) {
            this.errorState.classList.remove('hidden');
            const errorMessage = this.errorState.querySelector('.error-message');
            if (errorMessage && message) {
                errorMessage.textContent = message;
            }
        }
        if (this.feedContainer) this.feedContainer.classList.add('hidden');
    }

    /**
     * Show content state.
     */
    showContent() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.feedContainer) {
            this.feedContainer.classList.remove('hidden');
        }
    }

    /**
     * Load activities from API.
     * @param {boolean} reset - Whether to reset pagination
     */
    async loadActivities(reset = true) {
        console.log('Loading activities...');
        
        if (reset) {
            this.currentPage = 1;
            this.hasMore = true;
            this.showLoading();
        }

        try {
            const response = await fetch(`/api/user-activity?page=${this.currentPage}&limit=${this.pageSize}`);
            console.log('Activity API response status:', response.status);
            const data = await response.json();
            console.log('Activity API response data:', data);
            
            if (response.ok && data.success) {
                const activities = data.activities || [];
                console.log('Activities loaded:', activities.length);
                
                if (reset) {
                    this.allActivities = activities;
                } else {
                    this.allActivities = [...this.allActivities, ...activities];
                }
                
                this.filteredActivities = [...this.allActivities];
                this.hasMore = activities.length === this.pageSize;
                
                this.updateStats();
                this.renderActivities();
                
                if (this.allActivities.length === 0) {
                    console.log('No activities, showing empty state');
                    this.showEmpty();
                } else {
                    console.log('Activities found, showing content');
                    this.showContent();
                }
            } else {
                console.log('API returned error:', data.error);
                throw new Error(data.error || 'Failed to load activities');
            }
        } catch (error) {
            console.error('Error loading activities:', error);
            this.showError(`Failed to load activities: ${error.message}`);
        }
    }

    /**
     * Update statistics.
     */
    updateStats() {
        if (!this.allActivities.length) {
            if (this.statsTotal) this.statsTotal.textContent = '0';
            if (this.statsToday) this.statsToday.textContent = '0';
            if (this.statsTemplates) this.statsTemplates.textContent = '0';
            if (this.statsSuccess) this.statsSuccess.textContent = '0';
            return;
        }
        
        const today = new Date().toISOString().split('T')[0];
        const todayCount = this.allActivities.filter(activity => {
            const activityDate = new Date(activity.timestamp).toISOString().split('T')[0];
            return activityDate === today;
        }).length;
        
        const templateCount = this.allActivities.filter(activity => 
            activity.type === 'template_used'
        ).length;
        
        const successCount = this.allActivities.filter(activity => 
            activity.status === 'success'
        ).length;
        
        if (this.statsTotal) this.statsTotal.textContent = this.allActivities.length;
        if (this.statsToday) this.statsToday.textContent = todayCount;
        if (this.statsTemplates) this.statsTemplates.textContent = templateCount;
        if (this.statsSuccess) this.statsSuccess.textContent = successCount;
    }

    /**
     * Render activity cards.
     */
    renderActivities() {
        if (!this.feedContainer) {
            console.error('feedContainer is null');
            return;
        }
        
        if (this.currentPage === 1) {
            this.feedContainer.innerHTML = '';
        }
        
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const activitiesToRender = this.filteredActivities.slice(startIndex, startIndex + this.pageSize);
        
        activitiesToRender.forEach(activity => {
            const card = this.createActivityCard(activity);
            this.feedContainer.appendChild(card);
        });
        
        // Remove loading indicator if exists
        const loadingIndicator = this.feedContainer.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Add loading indicator if there are more activities
        if (this.hasMore && this.filteredActivities.length === this.allActivities.length) {
            const indicator = document.createElement('div');
            indicator.className = 'loading-indicator text-center py-4 text-slate-500 dark:text-slate-400';
            indicator.innerHTML = '<span class="material-symbols-outlined animate-spin mr-2">sync</span> Loading more...';
            this.feedContainer.appendChild(indicator);
        }
    }

    /**
     * Create an activity card element.
     * @param {Object} activity - Activity object
     * @returns {HTMLElement} Activity card element
     */
    createActivityCard(activity) {
        const card = document.createElement('div');
        card.className = 'activity-card bg-white dark:bg-surface-dark rounded-xl border border-slate-200 dark:border-border-dark p-4 hover:shadow-lg transition-all';
        card.dataset.id = activity.id;
        
        // Format timestamp
        const timestamp = new Date(activity.timestamp);
        const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = timestamp.toLocaleDateString();
        
        // Determine activity type icon and color
        const { icon, colorClass, bgColorClass } = this.getActivityTypeInfo(activity.type);
        
        // Determine status badge
        let statusBadge = '';
        if (activity.status === 'success') {
            statusBadge = '<span class="inline-block px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">Success</span>';
        } else if (activity.status === 'error') {
            statusBadge = '<span class="inline-block px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Error</span>';
        }
        
        // Build card HTML
        const cardHTML = `
            <div class="flex flex-col gap-3">
                <div class="flex items-start gap-3">
                    <div class="flex-shrink-0 w-10 h-10 rounded-full ${bgColorClass} flex items-center justify-center">
                        <span class="material-symbols-outlined ${colorClass}">${icon}</span>
                    </div>
                    
                    <div class="flex-1 min-w-0">
                        <div class="flex items-start justify-between mb-1">
                            <h4 class="font-bold text-slate-900 dark:text-white truncate">${activity.title}</h4>
                            ${statusBadge}
                        </div>
                        
                        <p class="text-sm text-slate-600 dark:text-slate-400 mb-2">${activity.description}</p>
                        
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                                <span class="material-symbols-outlined text-sm">schedule</span>
                                <span>${dateStr} at ${timeStr}</span>
                                <span class="mx-1">•</span>
                                <span>${this.formatTimeAgo(timestamp)}</span>
                            </div>
                            
                            ${this.getActionButtons(activity)}
                        </div>
                    </div>
                </div>
                
                ${this.getActivityMetadata(activity)}
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners for action buttons
        this.setupCardEventListeners(card, activity);
        
        return card;
    }

    /**
     * Get activity type information.
     * @param {string} type - Activity type
     * @returns {Object} Icon, color, and background color
     */
    getActivityTypeInfo(type) {
        const types = {
            'cover_generated': {
                icon: 'music_note',
                colorClass: 'text-purple-600 dark:text-purple-400',
                bgColorClass: 'bg-purple-100 dark:bg-purple-900/30'
            },
            'template_used': {
                icon: 'content_copy',
                colorClass: 'text-blue-600 dark:text-blue-400',
                bgColorClass: 'bg-blue-100 dark:bg-blue-900/30'
            },
            'history_entry': {
                icon: 'history',
                colorClass: 'text-green-600 dark:text-green-400',
                bgColorClass: 'bg-green-100 dark:bg-green-900/30'
            },
            'error_occurred': {
                icon: 'error',
                colorClass: 'text-red-600 dark:text-red-400',
                bgColorClass: 'bg-red-100 dark:bg-red-900/30'
            },
            'default': {
                icon: 'notifications',
                colorClass: 'text-slate-600 dark:text-slate-400',
                bgColorClass: 'bg-slate-100 dark:bg-slate-800'
            }
        };
        
        return types[type] || types.default;
    }

    /**
     * Get action buttons for activity.
     * @param {Object} activity - Activity object
     * @returns {string} HTML for action buttons
     */
    getActionButtons(activity) {
        let buttons = '';
        
        if (activity.type === 'template_used' && activity.template_id && this.onTemplateApply) {
            buttons = `
                <button class="reuse-template-btn text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1 px-3 py-1 rounded border border-primary/20 hover:bg-primary/5 transition-colors">
                    <span class="material-symbols-outlined text-sm">content_copy</span>
                    Reuse Template
                </button>
            `;
        } else if (activity.task_id) {
            buttons = `
                <button class="view-details-btn text-xs text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white font-medium flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">visibility</span>
                    View Details
                </button>
            `;
        }
        
        return buttons;
    }

    /**
     * Get activity metadata.
     * @param {Object} activity - Activity object
     * @returns {string} HTML for metadata
     */
    getActivityMetadata(activity) {
        let metadata = '';
        
        if (activity.metadata) {
            const metaItems = [];
            
            if (activity.metadata.tracks_count) {
                metaItems.push(`
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-slate-500 text-sm">queue_music</span>
                        <span class="text-xs text-slate-600 dark:text-slate-400">${activity.metadata.tracks_count} tracks</span>
                    </div>
                `);
            }
            
            if (activity.metadata.duration) {
                metaItems.push(`
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-slate-500 text-sm">schedule</span>
                        <span class="text-xs text-slate-600 dark:text-slate-400">${activity.metadata.duration}</span>
                    </div>
                `);
            }
            
            if (activity.metadata.template_name) {
                metaItems.push(`
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-slate-500 text-sm">content_copy</span>
                        <span class="text-xs text-slate-600 dark:text-slate-400">${activity.metadata.template_name}</span>
                    </div>
                `);
            }
            
            if (metaItems.length > 0) {
                metadata = `
                    <div class="mt-3 pt-3 border-t border-slate-100 dark:border-border-dark">
                        <div class="flex items-center gap-4">
                            ${metaItems.join('')}
                        </div>
                    </div>
                `;
            }
        }
        
        return metadata;
    }

    /**
     * Setup event listeners for card buttons.
     * @param {HTMLElement} card - Activity card element
     * @param {Object} activity - Activity object
     */
    setupCardEventListeners(card, activity) {
        // View details button
        const viewDetailsBtn = card.querySelector('.view-details-btn');
        if (viewDetailsBtn && this.onActivityClick) {
            viewDetailsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.onActivityClick(activity);
            });
        }
        
        // Reuse template button
        const reuseTemplateBtn = card.querySelector('.reuse-template-btn');
        if (reuseTemplateBtn && this.onTemplateApply && activity.template_id) {
            reuseTemplateBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.onTemplateApply(activity.template_id);
            });
        }
        
        // Whole card click
        if (this.onActivityClick) {
            card.addEventListener('click', () => {
                this.onActivityClick(activity);
            });
        }
    }

    /**
     * Format time ago.
     * @param {Date} date - Date to format
     * @returns {string} Formatted time ago string
     */
    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return `${Math.floor(diffDays / 7)}w ago`;
    }

    /**
     * Filter activities by type.
     */
    filterActivities() {
        if (!this.filterSelect) return;
        
        const filterValue = this.filterSelect.value;
        
        if (filterValue === 'all') {
            this.filteredActivities = [...this.allActivities];
        } else if (filterValue === 'templates') {
            this.filteredActivities = this.allActivities.filter(activity => 
                activity.type === 'template_used'
            );
        } else if (filterValue === 'covers') {
            this.filteredActivities = this.allActivities.filter(activity => 
                activity.type === 'cover_generated'
            );
        } else if (filterValue === 'today') {
            const today = new Date().toISOString().split('T')[0];
            this.filteredActivities = this.allActivities.filter(activity => {
                const activityDate = new Date(activity.timestamp).toISOString().split('T')[0];
                return activityDate === today;
            });
        }
        
        this.currentPage = 1;
        this.renderActivities();
    }

    /**
     * Search activities.
     */
    searchActivities() {
        if (!this.searchInput) return;
        
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        
        if (!searchTerm) {
            this.filteredActivities = [...this.allActivities];
        } else {
            this.filteredActivities = this.allActivities.filter(activity => {
                const title = (activity.title || '').toLowerCase();
                const description = (activity.description || '').toLowerCase();
                const taskId = (activity.task_id || '').toLowerCase();
                const templateName = (activity.metadata?.template_name || '').toLowerCase();
                
                return title.includes(searchTerm) ||
                       description.includes(searchTerm) ||
                       taskId.includes(searchTerm) ||
                       templateName.includes(searchTerm);
            });
        }
        
        this.currentPage = 1;
        this.renderActivities();
    }

    /**
     * Handle scroll for infinite loading.
     */
    handleScroll() {
        if (!this.feedContainer || !this.hasMore) return;
        
        const { scrollTop, scrollHeight, clientHeight } = this.feedContainer;
        const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100;
        
        if (isNearBottom) {
            this.loadMoreActivities();
        }
    }

    /**
     * Load more activities.
     */
    async loadMoreActivities() {
        if (!this.hasMore) return;
        
        this.currentPage++;
        await this.loadActivities(false);
    }

    /**
     * Set callback for activity click.
     * @param {Function} callback - Callback function with activity parameter
     */
    setOnActivityClick(callback) {
        this.onActivityClick = callback;
    }

    /**
     * Set callback for template apply.
     * @param {Function} callback - Callback function with templateId parameter
     */
    setOnTemplateApply(callback) {
        this.onTemplateApply = callback;
    }

    /**
     * Get all activities.
     * @returns {Array} All activities
     */
    getAllActivities() {
        return this.allActivities;
    }

    /**
     * Get filtered activities.
     * @returns {Array} Filtered activities
     */
    getFilteredActivities() {
        return this.filteredActivities;
    }

    /**
     * Clear all activities.
     */
    clearActivities() {
        this.allActivities = [];
        this.filteredActivities = [];
        this.currentPage = 1;
        this.hasMore = true;
        
        if (this.feedContainer) {
            this.feedContainer.innerHTML = '';
        }
        
        this.updateStats();
        this.showEmpty();
    }

    /**
     * Add a new activity to the feed.
     * @param {Object} activity - Activity object
     */
    addActivity(activity) {
        // Add timestamp if not present
        if (!activity.timestamp) {
            activity.timestamp = new Date().toISOString();
        }
        
        // Add to beginning of arrays
        this.allActivities.unshift(activity);
        this.filteredActivities.unshift(activity);
        
        // Update UI
        this.updateStats();
        
        if (this.currentPage === 1) {
            this.renderActivities();
        }
        
        // Show content if was empty
        if (this.allActivities.length === 1) {
            this.showContent();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActivityFeed;
} else {
    window.ActivityFeed = ActivityFeed;
}