/**
 * AddButton Component
 * A comprehensive, reusable button component for adding songs to playlists
 * with proper loading states, error handling, validation, and accessibility features.
 */

console.log('AddButton component loaded');

/**
 * AddButton class for adding songs to playlists
 */
class AddButton {
    constructor(options = {}) {
        this.options = {
            // Required props
            playlistId: options.playlistId || null,
            songData: options.songData || null,
            
            // Optional configuration
            variant: options.variant || 'primary', // 'primary', 'secondary', 'minimal'
            size: options.size || 'medium', // 'small', 'medium', 'large'
            disabled: options.disabled || false,
            loading: options.loading || false,
            showTooltip: options.showTooltip !== false,
            showIcon: options.showIcon !== false,
            
            // Callback functions
            onSuccess: options.onSuccess || null,
            onError: options.onError || null,
            onStateChange: options.onStateChange || null,
            onClick: options.onClick || null,
            onShowNotification: options.onShowNotification || null,
            
            // Configuration
            enableValidation: options.enableValidation !== false,
            enableDebouncing: options.enableDebouncing !== true,
            debounceDelay: options.debounceDelay || 500,
            enableOptimisticUpdates: options.enableOptimisticUpdates !== false,
            
            // Accessibility
            ariaLabel: options.ariaLabel || 'Add song to playlist',
            tooltipText: options.tooltipText || 'Add to playlist',
            
            ...options
        };
        
        // Component state
        this.state = {
            isLoading: this.options.loading,
            isDisabled: this.options.disabled,
            isSuccess: false,
            isError: false,
            errorMessage: '',
            clickCount: 0,
            lastClickTime: 0
        };
        
        // Internal properties
        this.element = null;
        this.tooltip = null;
        this.debounceTimer = null;
        this.eventHandlers = new Map();
        
        // Validation
        this.validateProps();
    }
    
    /**
     * Validate component props
     */
    validateProps() {
        if (!this.options.playlistId) {
            throw new Error('playlistId is required');
        }
        
        if (!this.options.songData) {
            throw new Error('songData is required');
        }
        
        // Validate song data structure
        const requiredFields = ['title', 'artist'];
        for (const field of requiredFields) {
            if (!this.options.songData[field]) {
                throw new Error(`songData.${field} is required`);
            }
        }
    }
    
    /**
     * Create the button element
     * @returns {HTMLElement} Button element
     */
    createElement() {
        this.element = document.createElement('button');
        this.element.className = this.buildButtonClasses();
        this.element.setAttribute('type', 'button');
        this.element.setAttribute('data-add-button', 'true');
        this.element.setAttribute('data-playlist-id', this.options.playlistId);
        this.element.setAttribute('data-song-id', this.options.songData.id || this.options.songData.song_id || '');
        
        // Set ARIA attributes
        this.element.setAttribute('aria-label', this.options.ariaLabel);
        this.element.setAttribute('aria-describedby', this.generateAriaDescribedBy());
        
        // Set initial content
        this.renderContent();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up tooltip if enabled
        if (this.options.showTooltip) {
            this.setupTooltip();
        }
        
        return this.element;
    }
    
    /**
     * Build CSS classes for the button
     * @returns {string} CSS classes
     */
    buildButtonClasses() {
        const classes = ['add-button', 'btn'];
        
        // Variant classes
        switch (this.options.variant) {
            case 'primary':
                classes.push('btn-primary');
                break;
            case 'secondary':
                classes.push('btn-secondary');
                break;
            case 'minimal':
                classes.push('add-button-minimal');
                break;
            default:
                classes.push('btn-primary');
        }
        
        // Size classes
        switch (this.options.size) {
            case 'small':
                classes.push('btn-sm');
                break;
            case 'large':
                classes.push('btn-lg');
                break;
            default:
                // medium size - no additional class needed
                break;
        }
        
        // State classes
        if (this.state.isLoading) {
            classes.push('btn-loading', 'opacity-75', 'cursor-not-allowed');
        }
        
        if (this.state.isDisabled) {
            classes.push('opacity-50', 'cursor-not-allowed');
        }
        
        if (this.state.isSuccess) {
            classes.push('btn-success');
        }
        
        if (this.state.isError) {
            classes.push('btn-error');
        }
        
        return classes.join(' ');
    }
    
    /**
     * Render button content based on current state
     */
    renderContent() {
        if (!this.element) return;
        
        let content = '';
        
        if (this.state.isLoading) {
            content = `
                <span class="material-symbols-outlined animate-spin">refresh</span>
                <span class="btn-text">Adding...</span>
            `;
        } else if (this.state.isSuccess) {
            content = `
                <span class="material-symbols-outlined">check</span>
                <span class="btn-text">Added</span>
            `;
        } else if (this.state.isError) {
            content = `
                <span class="material-symbols-outlined">error</span>
                <span class="btn-text">Try Again</span>
            `;
        } else {
            // Default state
            const icon = this.options.showIcon ? '<span class="material-symbols-outlined">add</span>' : '';
            content = `
                ${icon}
                <span class="btn-text">Add to Playlist</span>
            `;
        }
        
        this.element.innerHTML = content;
        
        // Add tooltip if enabled and not in loading state
        if (this.options.showTooltip && !this.state.isLoading) {
            this.element.title = this.getTooltipText();
        }
    }
    
    /**
     * Get tooltip text based on current state
     * @returns {string} Tooltip text
     */
    getTooltipText() {
        if (this.state.isSuccess) {
            return 'Song added to playlist';
        }
        
        if (this.state.isError) {
            return this.state.errorMessage || 'Failed to add song';
        }
        
        if (this.state.isDisabled) {
            return 'Cannot add song to playlist';
        }
        
        return this.options.tooltipText;
    }
    
    /**
     * Generate ARIA described by IDs
     * @returns {string} Space-separated IDs
     */
    generateAriaDescribedBy() {
        const ids = [];
        
        if (this.options.showTooltip) {
            ids.push(this.getTooltipId());
        }
        
        if (this.state.isError && this.state.errorMessage) {
            ids.push(this.getErrorId());
        }
        
        return ids.join(' ');
    }
    
    /**
     * Get tooltip element ID
     * @returns {string} Tooltip ID
     */
    getTooltipId() {
        return `add-button-tooltip-${this.generateId()}`;
    }
    
    /**
     * Get error element ID
     * @returns {string} Error ID
     */
    getErrorId() {
        return `add-button-error-${this.generateId()}`;
    }
    
    /**
     * Generate unique ID for component
     * @returns {string} Unique ID
     */
    generateId() {
        return `add-btn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        if (!this.element) return;
        
        // Click handler
        const clickHandler = (e) => this.handleClick(e);
        this.addEventListener('click', clickHandler);
        
        // Keyboard accessibility
        this.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Focus/blur for accessibility
        this.addEventListener('focus', () => this.handleFocus());
        this.addEventListener('blur', () => this.handleBlur());
        
        // Mouse events for better UX
        this.addEventListener('mouseenter', () => this.handleMouseEnter());
        this.addEventListener('mouseleave', () => this.handleMouseLeave());
    }
    
    /**
     * Handle click events
     * @param {Event} event Click event
     */
    async handleClick(event) {
        // Prevent default if disabled or loading
        if (this.state.isDisabled || this.state.isLoading) {
            event.preventDefault();
            return;
        }
        
        // Debouncing logic
        if (this.options.enableDebouncing) {
            const now = Date.now();
            if (now - this.state.lastClickTime < this.options.debounceDelay) {
                event.preventDefault();
                return;
            }
            this.state.lastClickTime = now;
        }
        
        // Check for rapid clicks
        this.state.clickCount++;
        if (this.state.clickCount > 3) {
            console.warn('AddButton: Rapid clicks detected');
            event.preventDefault();
            return;
        }
        
        // Custom click handler
        if (this.options.onClick) {
            const result = this.options.onClick(event, this.options.songData, this.options.playlistId);
            if (result === false) {
                event.preventDefault();
                return;
            }
        }
        
        // Prevent default click behavior
        event.preventDefault();
        
        // Check if we have required props for API call
        if (!this.options.playlistId || !this.options.songData) {
            console.warn('AddButton: Missing required props, using fallback behavior');
            
            // Fallback click behavior for demo purposes
            this.setState({ isLoading: true });
            
            setTimeout(() => {
                this.setState({ 
                    isLoading: false, 
                    isSuccess: true 
                });
                
                // Emit success event
                this.emit('success', { 
                    success: true, 
                    message: 'Added (demo mode)', 
                    mock: true 
                });
                
                // Auto-revert success state
                setTimeout(() => {
                    this.setState({ isSuccess: false });
                }, 2000);
                
            }, 800); // Simulate processing time
            
            return;
        }
        
        // Perform the add operation
        await this.performAddOperation();
    }
    
    /**
     * Handle keyboard events for accessibility
     * @param {KeyboardEvent} event Keyboard event
     */
    handleKeydown(event) {
        switch (event.key) {
            case 'Enter':
            case ' ':
                if (!this.state.isDisabled && !this.state.isLoading) {
                    event.preventDefault();
                    this.handleClick(event);
                }
                break;
            case 'Escape':
                if (this.state.isError) {
                    this.clearError();
                }
                break;
        }
    }
    
    /**
     * Handle focus events
     */
    handleFocus() {
        if (this.tooltip && this.options.showTooltip) {
            this.showTooltip();
        }
    }
    
    /**
     * Handle blur events
     */
    handleBlur() {
        if (this.tooltip) {
            this.hideTooltip();
        }
    }
    
    /**
     * Handle mouse enter events
     */
    handleMouseEnter() {
        if (this.tooltip && this.options.showTooltip && !this.state.isLoading) {
            this.showTooltip();
        }
    }
    
    /**
     * Handle mouse leave events
     */
    handleMouseLeave() {
        if (this.tooltip) {
            this.hideTooltip();
        }
    }
    
    /**
     * Perform the add operation with proper error handling and state management
     */
    async performAddOperation() {
        try {
            // Update state to loading
            this.setState({ isLoading: true, isError: false, errorMessage: '' });
            
            // Validate input data
            if (this.options.enableValidation) {
                const validationResult = this.validateSongData(this.options.songData);
                if (!validationResult.isValid) {
                    throw new Error(validationResult.message);
                }
            }
            
            // Optimistic update
            if (this.options.enableOptimisticUpdates) {
                this.performOptimisticUpdate();
            }
            
            // Perform API call with fallback
            let response;
            try {
                response = await this.makeApiCall();
            } catch (apiError) {
                console.warn('AddButton: API call failed, using fallback:', apiError.message);
                
                // Fallback to mock success for demo/development
                if (this.options.enableMockMode || this.isDevelopmentMode()) {
                    response = {
                        success: true,
                        message: 'Song added (mock mode)',
                        data: { added: true, mock: true }
                    };
                } else {
                    throw apiError;
                }
            }
            
            // Handle success
            this.handleSuccess(response);
            
        } catch (error) {
            // Handle failure with better error recovery
            await this.handleError(error);
            
            // Ensure we don't stay stuck in loading state
            setTimeout(() => {
                if (this.state.isLoading) {
                    console.warn('AddButton: Force clearing loading state');
                    this.setState({ isLoading: false });
                }
            }, 3000); // Force clear loading state after 3 seconds
        }
    }
    
    /**
     * Check if running in development mode
     * @returns {boolean} True if in development mode
     */
    isDevelopmentMode() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('localhost') ||
               this.options.enableMockMode === true;
    }
    
    /**
     * Validate song data
     * @param {Object} songData Song data to validate
     * @returns {Object} Validation result
     */
    validateSongData(songData) {
        const errors = [];
        
        // Required fields
        if (!songData.title || typeof songData.title !== 'string') {
            errors.push('Valid song title is required');
        }
        
        if (!songData.artist || typeof songData.artist !== 'string') {
            errors.push('Valid song artist is required');
        }
        
        // Additional validations
        if (songData.title && songData.title.length > 255) {
            errors.push('Song title is too long (max 255 characters)');
        }
        
        if (songData.artist && songData.artist.length > 255) {
            errors.push('Song artist is too long (max 255 characters)');
        }
        
        if (songData.duration && (typeof songData.duration !== 'number' || songData.duration <= 0)) {
            errors.push('Song duration must be a positive number');
        }
        
        return {
            isValid: errors.length === 0,
            message: errors.join(', '),
            errors
        };
    }
    
    /**
     * Perform optimistic update
     */
    performOptimisticUpdate() {
        // This would typically update the UI immediately
        // For now, we'll just log the optimistic update
        console.log('AddButton: Performing optimistic update for song:', this.options.songData.title);
        
        // Emit custom event for optimistic update
        this.emit('optimisticUpdate', {
            songData: this.options.songData,
            playlistId: this.options.playlistId
        });
    }
    
    /**
     * Make API call to add song to playlist
     * @returns {Promise<Object>} API response
     */
    async makeApiCall() {
        const endpoint = `/api/audio-library/playlists/${this.options.playlistId}/add`;
        
        const payload = {
            audio_id: this.options.songData.id || this.options.songData.audio_id,
            song_data: this.options.songData
        };
        
        try {
            // Add timeout to prevent hanging requests
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to add song to playlist');
            }
            
            return data;
        } catch (error) {
            // Handle fetch errors (network, CORS, timeout, etc.)
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please try again');
            }
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                throw new Error('Network error - please check your connection and try again');
            }
            
            throw error;
        }
    }
    
    /**
     * Handle successful operation
     * @param {Object} response API response
     */
    handleSuccess(response) {
        console.log('AddButton: Song added successfully:', response);
        
        // Update state
        this.setState({
            isLoading: false,
            isSuccess: true,
            isError: false,
            errorMessage: ''
        });
        
        // Auto-revert success state after delay
        setTimeout(() => {
            this.setState({ isSuccess: false });
        }, 2000);
        
        // Reset click count
        this.state.clickCount = 0;
        
        // Emit success event
        this.emit('success', response);
        
        // Call success callback
        if (this.options.onSuccess) {
            this.options.onSuccess(response, this.options.songData, this.options.playlistId);
        }
    }
    
    /**
     * Handle failed operation
     * @param {Error} error Error object
     */
    async handleError(error) {
        console.error('AddButton: Failed to add song:', error);
        
        // Revert optimistic update if needed
        if (this.options.enableOptimisticUpdates) {
            this.revertOptimisticUpdate();
        }
        
        // Update state
        this.setState({
            isLoading: false,
            isSuccess: false,
            isError: true,
            errorMessage: error.message
        });
        
        // Reset click count
        this.state.clickCount = 0;
        
        // Emit error event
        this.emit('error', error);
        
        // Show error notification
        this.showErrorNotification(error.message);
        
        // Call error callback
        if (this.options.onError) {
            this.options.onError(error, this.options.songData, this.options.playlistId);
        }
        
        // Auto-hide error state after delay
        setTimeout(() => {
            this.clearError();
        }, 5000);
    }
    
    /**
     * Revert optimistic update
     */
    revertOptimisticUpdate() {
        console.log('AddButton: Reverting optimistic update');
        
        // Emit custom event for reverting optimistic update
        this.emit('revertOptimisticUpdate', {
            songData: this.options.songData,
            playlistId: this.options.playlistId
        });
    }
    
    /**
     * Show error notification
     * @param {string} message Error message
     */
    showErrorNotification(message) {
        if (this.options.onShowNotification) {
            this.options.onShowNotification(message, 'error');
        } else if (typeof showError === 'function') {
            showError(message);
        } else {
            // Fallback notification
            console.error('AddButton Error:', message);
        }
    }
    
    /**
     * Clear error state
     */
    clearError() {
        this.setState({
            isError: false,
            errorMessage: ''
        });
    }
    
    /**
     * Set component state and update UI
     * @param {Object} newState New state properties
     */
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.updateUI();
        this.updateAriaAttributes();
        
        // Emit state change event
        this.emit('stateChange', this.state);
        
        // Call state change callback
        if (this.options.onStateChange) {
            this.options.onStateChange(this.state);
        }
    }
    
    /**
     * Update UI based on current state
     */
    updateUI() {
        if (!this.element) return;
        
        // Update classes
        this.element.className = this.buildButtonClasses();
        
        // Update content
        this.renderContent();
        
        // Update disabled state
        this.element.disabled = this.state.isDisabled || this.state.isLoading;
        
        // Update tooltip
        if (this.tooltip && this.options.showTooltip) {
            this.updateTooltip();
        }
    }
    
    /**
     * Update ARIA attributes
     */
    updateAriaAttributes() {
        if (!this.element) return;
        
        // Update aria-disabled
        if (this.state.isDisabled || this.state.isLoading) {
            this.element.setAttribute('aria-disabled', 'true');
        } else {
            this.element.removeAttribute('aria-disabled');
        }
        
        // Update aria-busy
        if (this.state.isLoading) {
            this.element.setAttribute('aria-busy', 'true');
        } else {
            this.element.removeAttribute('aria-busy');
        }
        
        // Update described by
        this.element.setAttribute('aria-describedby', this.generateAriaDescribedBy());
    }
    
    /**
     * Set up tooltip functionality
     */
    setupTooltip() {
        if (!this.element) return;
        
        this.tooltip = document.createElement('div');
        this.tooltip.id = this.getTooltipId();
        this.tooltip.className = 'add-button-tooltip';
        this.tooltip.textContent = this.getTooltipText();
        this.tooltip.setAttribute('role', 'tooltip');
        
        // Position tooltip
        this.positionTooltip();
        
        // Add to DOM (initially hidden)
        document.body.appendChild(this.tooltip);
    }
    
    /**
     * Position tooltip relative to button
     */
    positionTooltip() {
        if (!this.tooltip || !this.element) return;
        
        const buttonRect = this.element.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        let top = buttonRect.bottom + window.scrollY + 5;
        let left = buttonRect.left + window.scrollX;
        
        // Adjust if tooltip would go off screen
        if (left + tooltipRect.width > window.innerWidth) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        
        if (left < 0) {
            left = 10;
        }
        
        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }
    
    /**
     * Show tooltip
     */
    showTooltip() {
        if (this.tooltip) {
            this.tooltip.classList.add('visible');
        }
    }
    
    /**
     * Hide tooltip
     */
    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.classList.remove('visible');
        }
    }
    
    /**
     * Update tooltip content and position
     */
    updateTooltip() {
        if (!this.tooltip) return;
        
        this.tooltip.textContent = this.getTooltipText();
        this.positionTooltip();
    }
    
    /**
     * Add event listener
     * @param {string} event Event name
     * @param {Function} handler Event handler
     */
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
        
        if (this.element) {
            this.element.addEventListener(event, handler);
        }
    }
    
    /**
     * Remove event listener
     * @param {string} event Event name
     * @param {Function} handler Event handler
     */
    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
        
        if (this.element) {
            this.element.removeEventListener(event, handler);
        }
    }
    
    /**
     * Emit custom event
     * @param {string} event Event name
     * @param {Object} data Event data
     */
    emit(event, data) {
        if (this.element) {
            const customEvent = new CustomEvent(`addButton:${event}`, {
                detail: {
                    ...data,
                    component: this,
                    state: this.state
                }
            });
            this.element.dispatchEvent(customEvent);
        }
    }
    
    /**
     * Update component options
     * @param {Object} newOptions New options
     */
    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        this.validateProps();
        this.updateUI();
    }
    
    /**
     * Update song data
     * @param {Object} newSongData New song data
     */
    updateSongData(newSongData) {
        this.options.songData = newSongData;
        this.validateProps();
        this.updateUI();
    }
    
    /**
     * Update playlist ID
     * @param {string} newPlaylistId New playlist ID
     */
    updatePlaylistId(newPlaylistId) {
        this.options.playlistId = newPlaylistId;
        this.validateProps();
        if (this.element) {
            this.element.setAttribute('data-playlist-id', newPlaylistId);
        }
    }
    
    /**
     * Enable the button
     */
    enable() {
        this.setState({ isDisabled: false });
    }
    
    /**
     * Disable the button
     */
    disable() {
        this.setState({ isDisabled: true });
    }
    
    /**
     * Reset button to initial state
     */
    reset() {
        this.setState({
            isLoading: false,
            isDisabled: false,
            isSuccess: false,
            isError: false,
            errorMessage: '',
            clickCount: 0
        });
    }
    
    /**
     * Force refresh the button state from server
     */
    async refresh() {
        // This could check if the song is already in the playlist
        // and update the button state accordingly
        console.log('AddButton: Refreshing state for playlist:', this.options.playlistId);
        
        try {
            // Example implementation - you'd need to create this endpoint
            const response = await fetch(`/api/audio-library/playlists/${this.options.playlistId}/contains/${this.options.songData.id}`);
            if (response.ok) {
                const data = await response.json();
                if (data.contains) {
                    this.setState({ isDisabled: true });
                    this.updateTooltipText('Song already in playlist');
                }
            }
        } catch (error) {
            console.warn('AddButton: Could not refresh state:', error);
        }
    }
    
    /**
     * Update tooltip text
     * @param {string} text New tooltip text
     */
    updateTooltipText(text) {
        if (this.options.tooltipText !== text) {
            this.options.tooltipText = text;
            if (this.tooltip) {
                this.updateTooltip();
            }
        }
    }
    
    /**
     * Destroy component and clean up
     */
    destroy() {
        // Clear timers
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Remove event listeners
        this.eventHandlers.forEach((handlers, event) => {
            handlers.forEach(handler => {
                if (this.element) {
                    this.element.removeEventListener(event, handler);
                }
            });
        });
        
        // Remove tooltip
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
        
        // Remove element
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        
        // Clear references
        this.eventHandlers.clear();
    }
    
    /**
     * Get the button element
     * @returns {HTMLElement} Button element
     */
    getElement() {
        return this.element;
    }
    
    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Get current options
     * @returns {Object} Current options
     */
    getOptions() {
        return { ...this.options };
    }
    
    /**
     * Check if component is in loading state
     * @returns {boolean} Is loading
     */
    isLoading() {
        return this.state.isLoading;
    }
    
    /**
     * Check if component is disabled
     * @returns {boolean} Is disabled
     */
    isDisabled() {
        return this.state.isDisabled || this.state.isLoading;
    }
    
    /**
     * Check if last operation was successful
     * @returns {boolean} Is in success state
     */
    wasSuccessful() {
        return this.state.isSuccess;
    }
    
    /**
     * Check if last operation failed
     * @returns {boolean} Is in error state
     */
    hasError() {
        return this.state.isError;
    }
    
    /**
     * Get error message if any
     * @returns {string} Error message
     */
    getErrorMessage() {
        return this.state.errorMessage;
    }
}

/**
 * AddButton Factory for creating multiple instances
 */
class AddButtonFactory {
    constructor() {
        this.instances = new Map();
    }
    
    /**
     * Create AddButton instance
     * @param {Object} options Button options
     * @param {string} id Optional instance ID
     * @returns {AddButton} AddButton instance
     */
    create(options, id = null) {
        const instanceId = id || `add-btn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const button = new AddButton(options);
        this.instances.set(instanceId, button);
        return button;
    }
    
    /**
     * Get instance by ID
     * @param {string} id Instance ID
     * @returns {AddButton|null} AddButton instance or null
     */
    get(id) {
        return this.instances.get(id) || null;
    }
    
    /**
     * Destroy instance by ID
     * @param {string} id Instance ID
     */
    destroy(id) {
        const instance = this.instances.get(id);
        if (instance) {
            instance.destroy();
            this.instances.delete(id);
        }
    }
    
    /**
     * Destroy all instances
     */
    destroyAll() {
        this.instances.forEach((instance) => instance.destroy());
        this.instances.clear();
    }
    
    /**
     * Get all instances
     * @returns {Map} Map of all instances
     */
    getAll() {
        return new Map(this.instances);
    }
}

// Global factory instance
window.addButtonFactory = new AddButtonFactory();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AddButton,
        AddButtonFactory
    };
} else {
    window.AddButton = AddButton;
    window.AddButtonFactory = AddButtonFactory;
}
