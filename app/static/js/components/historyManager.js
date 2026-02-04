/**
 * History manager for the Music Cover Generator application.
 * Handles loading, filtering, and displaying callback history.
 */

class HistoryManager {
    constructor() {
        this.allHistory = [];
        this.filteredHistory = [];
        
        // DOM Elements (will be initialized by the main app)
        this.historyContainer = null;
        this.loadingState = null;
        this.emptyState = null;
        this.errorState = null;
        this.statsTotal = null;
        this.statsToday = null;
        this.statsSuccess = null;
        this.statsFailed = null;
        this.refreshBtn = null;
        this.cleanupBtn = null;
        this.filterSelect = null;
        this.searchInput = null;
        this.historyModal = null;
        this.modalCloseBtn = null;
        this.modalContent = null;
    }

    /**
     * Initialize history manager with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.historyContainer = elements.historyContainer;
        this.loadingState = elements.loadingState;
        this.emptyState = elements.emptyState;
        this.errorState = elements.errorState;
        this.statsTotal = elements.statsTotal;
        this.statsToday = elements.statsToday;
        this.statsSuccess = elements.statsSuccess;
        this.statsFailed = elements.statsFailed;
        this.refreshBtn = elements.refreshBtn;
        this.cleanupBtn = elements.cleanupBtn;
        this.filterSelect = elements.filterSelect;
        this.searchInput = elements.searchInput;
        this.historyModal = elements.historyModal;
        this.modalCloseBtn = elements.modalCloseBtn;
        this.modalContent = elements.modalContent;

        this._setupEventListeners();
    }

    /**
     * Set up event listeners.
     * @private
     */
    _setupEventListeners() {
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadHistory());
        }

        if (this.cleanupBtn) {
            this.cleanupBtn.addEventListener('click', () => this.cleanupHistory());
        }

        if (this.filterSelect) {
            this.filterSelect.addEventListener('change', () => this.filterHistory());
        }

        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => this.searchHistory());
        }

        if (this.modalCloseBtn) {
            this.modalCloseBtn.addEventListener('click', () => this.closeModal());
        }
    }

    /**
     * Show loading state.
     */
    showLoading() {
        if (this.loadingState) this.loadingState.classList.remove('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.historyContainer) this.historyContainer.classList.add('hidden');
    }

    /**
     * Show empty state.
     */
    showEmpty() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.remove('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.historyContainer) this.historyContainer.classList.add('hidden');
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
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage && message) {
                errorMessage.textContent = message;
            }
        }
        if (this.historyContainer) this.historyContainer.classList.add('hidden');
    }

    /**
     * Show content state.
     */
    showContent() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.historyContainer) {
            this.historyContainer.classList.remove('hidden');
        }
    }

    /**
     * Load history from API.
     */
    async loadHistory() {
        console.log('Loading history...');
        this.showLoading();
        
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.allHistory = data.history || [];
                this.filteredHistory = [...this.allHistory];
                
                this.updateStats();
                this.renderHistory();
                
                if (this.allHistory.length === 0) {
                    this.showEmpty();
                } else {
                    this.showContent();
                }
            } else {
                throw new Error(data.error || 'Failed to load history');
            }
        } catch (error) {
            console.error('Error loading history:', error);
            this.showError(`Failed to load history: ${error.message}`);
        }
    }

    /**
     * Update statistics.
     */
    updateStats() {
        if (!this.allHistory.length) {
            if (this.statsTotal) this.statsTotal.textContent = '0';
            if (this.statsToday) this.statsToday.textContent = '0';
            if (this.statsSuccess) this.statsSuccess.textContent = '0';
            if (this.statsFailed) this.statsFailed.textContent = '0';
            return;
        }
        
        const today = new Date().toISOString().split('T')[0];
        const todayCount = this.allHistory.filter(entry => {
            const entryDate = new Date(entry.timestamp).toISOString().split('T')[0];
            return entryDate === today;
        }).length;
        
        const successCount = this.allHistory.filter(entry =>
            entry.status_code === 200 || entry.status === 'success'
        ).length;
        
        const failedCount = this.allHistory.filter(entry =>
            entry.status_code && entry.status_code !== 200
        ).length;
        
        if (this.statsTotal) this.statsTotal.textContent = this.allHistory.length;
        if (this.statsToday) this.statsToday.textContent = todayCount;
        if (this.statsSuccess) this.statsSuccess.textContent = successCount;
        if (this.statsFailed) this.statsFailed.textContent = failedCount;
    }

    /**
     * Render history cards.
     */
    renderHistory() {
        if (!this.historyContainer) {
            console.error('historyContainer is null');
            return;
        }
        
        this.historyContainer.innerHTML = '';
        
        this.filteredHistory.forEach(entry => {
            const card = this.createHistoryCard(entry);
            this.historyContainer.appendChild(card);
        });
    }

    /**
     * Create a history card element using the unified card system.
     * @param {Object} entry - History entry object
     * @returns {HTMLElement} History card element
     */
    createHistoryCard(entry) {
        // Create a new HistoryCard instance
        const card = new HistoryCard({
            id: `history-card-${entry.id}`,
            data: entry,
            variant: 'default',
            clickable: true,
            hoverable: true
        });
        
        // Set up callbacks
        card.setCallbacks({
            onAction: (action, data, event) => {
                if (action === 'view-details' && this.onShowEntryDetails) {
                    this.onShowEntryDetails(data);
                }
            }
        });
        
        // Create and return the card element
        return card.createElement();
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
     * Filter history by status.
     */
    filterHistory() {
        if (!this.filterSelect) return;
        
        const filterValue = this.filterSelect.value;
        
        if (filterValue === 'all') {
            this.filteredHistory = [...this.allHistory];
        } else if (filterValue === 'success') {
            this.filteredHistory = this.allHistory.filter(entry => 
                entry.status_code === 200 || entry.status === 'success'
            );
        } else if (filterValue === 'failed') {
            this.filteredHistory = this.allHistory.filter(entry => 
                entry.status_code && entry.status_code !== 200
            );
        } else if (filterValue === 'today') {
            const today = new Date().toISOString().split('T')[0];
            this.filteredHistory = this.allHistory.filter(entry => {
                const entryDate = new Date(entry.timestamp).toISOString().split('T')[0];
                return entryDate === today;
            });
        }
        
        this.renderHistory();
    }

    /**
     * Search history.
     */
    searchHistory() {
        if (!this.searchInput) return;
        
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        
        if (!searchTerm) {
            this.filteredHistory = [...this.allHistory];
        } else {
            this.filteredHistory = this.allHistory.filter(entry => {
                const taskId = (entry.task_id || '').toLowerCase();
                const statusMessage = (entry.status_message || '').toLowerCase();
                const callbackType = (entry.callback_type || '').toLowerCase();
                
                return taskId.includes(searchTerm) || 
                       statusMessage.includes(searchTerm) || 
                       callbackType.includes(searchTerm);
            });
        }
        
        this.renderHistory();
    }

    /**
     * Cleanup old history (15+ days).
     */
    async cleanupHistory() {
        if (!confirm('Clean up history entries older than 15 days? This action cannot be undone.')) {
            return;
        }
        
        if (this.cleanupBtn) {
            this.cleanupBtn.disabled = true;
            this.cleanupBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Cleaning...';
        }
        
        try {
            const response = await fetch('/api/history/cleanup?days=15&auto=true', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (response.ok && data.success) {
                alert(`History cleanup completed. Removed ${data.removed_count} entries older than 15 days. ${data.remaining_count} entries remain.`);
                this.loadHistory(); // Reload history
            } else {
                throw new Error(data.error || 'Cleanup failed');
            }
        } catch (error) {
            console.error('Error cleaning up history:', error);
            alert(`Cleanup failed: ${error.message}`);
        } finally {
            if (this.cleanupBtn) {
                this.cleanupBtn.disabled = false;
                this.cleanupBtn.innerHTML = '<span class="material-symbols-outlined mr-2">delete</span> Cleanup';
            }
        }
    }

    /**
     * Close modal.
     */
    closeModal() {
        if (this.historyModal) {
            this.historyModal.classList.add('hidden');
        }
    }

    /**
     * Get all history entries.
     * @returns {Array} All history entries
     */
    getAllHistory() {
        return this.allHistory;
    }

    /**
     * Get filtered history entries.
     * @returns {Array} Filtered history entries
     */
    getFilteredHistory() {
        return this.filteredHistory;
    }

    /**
     * Set callback for showing entry details.
     * @param {Function} callback - Callback function with entry parameter
     */
    setOnShowEntryDetails(callback) {
        this.onShowEntryDetails = callback;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HistoryManager;
} else {
    window.HistoryManager = HistoryManager;
}