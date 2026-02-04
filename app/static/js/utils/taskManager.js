/**
 * Task management for the Music Cover Generator application.
 * Handles task polling, status updates, and callback history.
 */

class TaskManager {
    constructor() {
        this.currentTaskId = null;
        this.isPolling = false;
        this.pollingTimeout = null;
        
        // DOM Elements (will be initialized by the main app)
        this.taskStatus = null;
        this.taskId = null;
        this.statusBadge = null;
        this.statusProgress = null;
        this.statusText = null;
        this.startTime = null;
        this.statusCode = null;
        this.audioId = null;
        this.statusMessage = null;
        this.callbackType = null;
        this.results = null;
        this.refreshStatusBtn = null;
    }

    /**
     * Initialize task manager with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.taskStatus = elements.taskStatus;
        this.taskId = elements.taskId;
        this.statusBadge = elements.statusBadge;
        this.statusProgress = elements.statusProgress;
        this.statusText = elements.statusText;
        this.startTime = elements.startTime;
        this.statusCode = elements.statusCode;
        this.audioId = elements.audioId;
        this.statusMessage = elements.statusMessage;
        this.callbackType = elements.callbackType;
        this.results = elements.results;
        this.refreshStatusBtn = elements.refreshStatusBtn;

        if (this.refreshStatusBtn) {
            this.refreshStatusBtn.addEventListener('click', this.refreshTaskStatus.bind(this));
        }
    }

    /**
     * Set the current task ID and start polling.
     * @param {string} taskId - The task ID to track
     */
    setCurrentTask(taskId) {
        this.currentTaskId = taskId;
        this.taskId.textContent = taskId;
        this.startTime.textContent = new Date().toLocaleTimeString();
        
        if (this.taskStatus) {
            this.taskStatus.classList.remove('hidden');
        }
        
        this.pollTaskStatus();
    }

    /**
     * Poll task status with enhanced callback data handling.
     */
    pollTaskStatus() {
        if (!this.currentTaskId || this.isPolling) return;
        
        this.isPolling = true;
        const pollInterval = 5000; // 5 seconds
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/task-status/${this.currentTaskId}`);
                const result = await response.json();
                
                if (response.ok) {
                    // Extract data from the API response structure
                    const data = result.data || {};
                    const status = data.status || 'Unknown';
                    const message = result.msg || '';
                    const code = result.code || '';
                    
                    // Update status display
                    this._updateStatusDisplay(status, message, code, data);
                    
                    // Check if task is complete
                    if (status === 'SUCCESS' || status === 'FAILED' || status === 'GENERATE_AUDIO_FAILED') {
                        this.isPolling = false;
                        clearTimeout(this.pollingTimeout);
                        
                        if (status === 'SUCCESS') {
                            let sunoData = null;
                            if (data.response && data.response.sunoData) {
                                sunoData = data.response.sunoData;
                            } else if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                                // Use tracks from data.data (standard Kie API response)
                                sunoData = data.data;
                            }
                            
                            if (sunoData && sunoData.length > 0) {
                                // Also fetch callback history for this task
                                this.fetchCallbackHistory(this.currentTaskId);
                                
                                // Trigger callback for successful generation
                                if (this.onGenerationComplete) {
                                    this.onGenerationComplete(sunoData);
                                }
                            }
                        } else if (status === 'FAILED' || status === 'GENERATE_AUDIO_FAILED') {
                            window.NotificationSystem?.showError(`Generation failed: ${message || 'Unknown error'}`);
                        }
                    } else {
                        // Continue polling
                        this.pollingTimeout = setTimeout(poll, pollInterval);
                    }
                } else {
                    throw new Error(result.error || 'Failed to get task status');
                }
            } catch (error) {
                console.error('Polling error:', error);
                this.isPolling = false;
                window.NotificationSystem?.showError(`Failed to poll task status: ${error.message}`);
            }
        };
        
        poll();
    }

    /**
     * Update status display elements.
     * @private
     */
    _updateStatusDisplay(status, message, code, data) {
        if (this.statusBadge) this.statusBadge.textContent = status;
        if (this.statusText) this.statusText.textContent = message;
        if (this.statusCode) this.statusCode.textContent = code;
        if (this.statusMessage) this.statusMessage.textContent = message;
        
        // Update progress based on status
        let progressValue = 0;
        if (status === 'PENDING') progressValue = 25;
        else if (status === 'TEXT_SUCCESS') progressValue = 40;
        else if (status === 'GENERATE_AUDIO_FAILED') progressValue = 50;
        else if (status === 'SUCCESS') progressValue = 100;
        else if (status === 'FAILED') progressValue = 100;
        
        if (this.statusProgress) this.statusProgress.value = progressValue;
        
        // Update other fields
        if (this.taskId) this.taskId.textContent = this.currentTaskId;
        // Handle both taskId (camelCase) and task_id (snake_case) from API responses
        const audioTaskId = data.taskId || data.task_id || '';
        if (this.audioId) this.audioId.textContent = audioTaskId;
        if (this.callbackType) this.callbackType.textContent = data.type || '';
    }

    /**
     * Fetch callback history for a specific task.
     * @param {string} taskId - The task ID to fetch history for
     */
    async fetchCallbackHistory(taskId) {
        try {
            const response = await fetch(`/api/history`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                const history = result.history || [];
                const taskCallbacks = history.filter(entry => entry.task_id === taskId);
                
                if (taskCallbacks.length > 0) {
                    // Sort by timestamp (newest first)
                    taskCallbacks.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                    
                    // Display callback information
                    const latestCallback = taskCallbacks[0];
                    if (latestCallback.processed_data) {
                        if (this.onCallbackInfo) {
                            this.onCallbackInfo(latestCallback.processed_data);
                        }
                    }
                    
                    // Show callback history summary
                    if (taskCallbacks.length > 1) {
                        if (this.onCallbackHistory) {
                            this.onCallbackHistory(taskCallbacks);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching callback history:', error);
        }
    }

    /**
     * Refresh task status manually.
     */
    refreshTaskStatus() {
        if (!this.currentTaskId) {
            window.NotificationSystem?.showError('No active task to refresh');
            return;
        }
        
        if (this.refreshStatusBtn) {
            this.refreshStatusBtn.disabled = true;
            this.refreshStatusBtn.innerHTML = '<span class="material-symbols-outlined mr-1">sync</span> Refreshing...';
        }
        
        // Clear any existing polling timeout
        if (this.pollingTimeout) {
            clearTimeout(this.pollingTimeout);
            this.pollingTimeout = null;
        }
        
        // Force a status check
        this.isPolling = false;
        
        // Call pollTaskStatus which will fetch and update
        this.pollTaskStatus();
        
        // Re-enable button after a short delay
        setTimeout(() => {
            if (this.refreshStatusBtn) {
                this.refreshStatusBtn.disabled = false;
                this.refreshStatusBtn.innerHTML = '<span class="material-symbols-outlined mr-1">refresh</span> Refresh';
            }
        }, 1000);
    }

    /**
     * Get the current task ID.
     * @returns {string|null} The current task ID or null
     */
    getCurrentTaskId() {
        return this.currentTaskId;
    }

    /**
     * Check if a task is currently being polled.
     * @returns {boolean} True if polling is active
     */
    isPollingActive() {
        return this.isPolling;
    }

    /**
     * Stop polling for the current task.
     */
    stopPolling() {
        this.isPolling = false;
        if (this.pollingTimeout) {
            clearTimeout(this.pollingTimeout);
            this.pollingTimeout = null;
        }
    }

    /**
     * Reset task manager state.
     */
    reset() {
        this.stopPolling();
        this.currentTaskId = null;
        
        if (this.taskStatus) this.taskStatus.classList.add('hidden');
        if (this.results) this.results.classList.add('hidden');
    }

    /**
     * Set callback for when generation is complete.
     * @param {Function} callback - Callback function with sunoData parameter
     */
    setOnGenerationComplete(callback) {
        this.onGenerationComplete = callback;
    }

    /**
     * Set callback for when callback info is available.
     * @param {Function} callback - Callback function with callbackData parameter
     */
    setOnCallbackInfo(callback) {
        this.onCallbackInfo = callback;
    }

    /**
     * Set callback for when callback history is available.
     * @param {Function} callback - Callback function with callbacks parameter
     */
    setOnCallbackHistory(callback) {
        this.onCallbackHistory = callback;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TaskManager;
} else {
    window.TaskManager = TaskManager;
}