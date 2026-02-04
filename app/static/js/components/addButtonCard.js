/**
 * AddButtonCard Component
 * A specialized card that integrates the AddButton component with the unified card system
 * for displaying songs with add-to-playlist functionality.
 */

console.log('AddButtonCard component loaded');

/**
 * AddButtonCard class that extends BaseCard with AddButton functionality
 */
class AddButtonCard extends BaseCard {
    constructor(options = {}) {
        // Initialize with default options
        super({
            variant: 'song',
            size: 'medium',
            ...options
        });
        
        // AddButton-specific options
        this.addButtonOptions = {
            playlistId: options.playlistId || null,
            songData: options.songData || options.data || null,
            variant: options.addButtonVariant || 'primary',
            size: options.addButtonSize || 'small',
            showTooltip: options.showAddButtonTooltip !== false,
            showIcon: options.showAddButtonIcon !== false,
            enableValidation: options.enableAddButtonValidation !== false,
            enableDebouncing: options.enableAddButtonDebouncing || false,
            enableOptimisticUpdates: options.enableAddButtonOptimisticUpdates !== false,
            onSuccess: options.onAddSuccess || null,
            onError: options.onAddError || null,
            ...options.addButtonOptions
        };
        
        // Component state
        this.state = {
            ...this.state,
            isAddingToPlaylist: false,
            addButtonInstance: null,
            playlistOptions: options.playlistOptions || [],
            selectedPlaylistId: options.selectedPlaylistId || null,
            showPlaylistSelector: options.showPlaylistSelector || false
        };
        
        // Initialize AddButton
        this.initializeAddButton();
    }
    
    /**
     * Initialize the AddButton component
     */
    initializeAddButton() {
        if (!this.addButtonOptions.songData || !this.addButtonOptions.playlistId) {
            console.warn('AddButtonCard: Missing songData or playlistId for AddButton');
            return;
        }
        
        try {
            this.state.addButtonInstance = new AddButton(this.addButtonOptions);
            
            // Set up AddButton event listeners
            this.setupAddButtonEventListeners();
            
        } catch (error) {
            console.error('AddButtonCard: Failed to initialize AddButton:', error);
        }
    }
    
    /**
     * Set up event listeners for the AddButton
     */
    setupAddButtonEventListeners() {
        if (!this.state.addButtonInstance) return;
        
        // Listen for AddButton state changes
        this.state.addButtonInstance.addEventListener('addButton:stateChange', (event) => {
            this.handleAddButtonStateChange(event.detail);
        });
        
        // Listen for AddButton success
        this.state.addButtonInstance.addEventListener('addButton:success', (event) => {
            this.handleAddButtonSuccess(event.detail);
        });
        
        // Listen for AddButton error
        this.state.addButtonInstance.addEventListener('addButton:error', (event) => {
            this.handleAddButtonError(event.detail);
        });
        
        // Listen for optimistic updates
        this.state.addButtonInstance.addEventListener('addButton:optimisticUpdate', (event) => {
            this.handleOptimisticUpdate(event.detail);
        });
        
        // Listen for revert optimistic updates
        this.state.addButtonInstance.addEventListener('addButton:revertOptimisticUpdate', (event) => {
            this.handleRevertOptimisticUpdate(event.detail);
        });
    }
    
    /**
     * Create the card element with AddButton integration
     * @returns {HTMLElement} Card element
     */
    createElement() {
        // Create base card element
        const card = super.createElement();
        card.classList.add('add-button-card');
        card.dataset.cardType = 'add-button-card';
        
        // Add song-specific styling
        if (this.options.songData || this.options.data) {
            this.renderSongContent(card);
        }
        
        // Add AddButton if available
        if (this.state.addButtonInstance) {
            this.renderAddButton(card);
        }
        
        // Set up playlist selector if enabled
        if (this.state.showPlaylistSelector) {
            this.renderPlaylistSelector(card);
        }
        
        return card;
    }
    
    /**
     * Render song-specific content
     * @param {HTMLElement} card - Card element
     */
    renderSongContent(card) {
        const songData = this.options.songData || this.options.data;
        
        // Create song info container
        const songInfo = document.createElement('div');
        songInfo.className = 'add-button-card-song-info';
        
        // Song title
        const title = document.createElement('h3');
        title.className = 'add-button-card-title';
        title.textContent = songData.title || 'Unknown Title';
        title.setAttribute('data-song-title', 'true');
        
        // Song artist
        const artist = document.createElement('p');
        artist.className = 'add-button-card-artist';
        artist.textContent = songData.artist || 'Unknown Artist';
        
        // Song metadata (duration, genre, etc.)
        const metadata = document.createElement('div');
        metadata.className = 'add-button-card-metadata';
        
        if (songData.duration) {
            const duration = document.createElement('span');
            duration.className = 'add-button-card-duration';
            duration.textContent = this.formatDuration(songData.duration);
            duration.setAttribute('data-duration', 'true');
            metadata.appendChild(duration);
        }
        
        if (songData.genre) {
            const genre = document.createElement('span');
            genre.className = 'add-button-card-genre';
            genre.textContent = songData.genre;
            metadata.appendChild(genre);
        }
        
        // Album info if available
        if (songData.album) {
            const album = document.createElement('span');
            album.className = 'add-button-card-album';
            album.textContent = songData.album;
            metadata.appendChild(album);
        }
        
        songInfo.appendChild(title);
        songInfo.appendChild(artist);
        songInfo.appendChild(metadata);
        
        // Add to card
        card.appendChild(songInfo);
    }
    
    /**
     * Render AddButton in the card
     * @param {HTMLElement} card - Card element
     */
    renderAddButton(card) {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'add-button-card-button-container';
        
        // Create AddButton element
        const addButtonElement = this.state.addButtonInstance.createElement();
        addButtonElement.classList.add('add-button-card-button');
        
        buttonContainer.appendChild(addButtonElement);
        card.appendChild(buttonContainer);
    }
    
    /**
     * Render playlist selector
     * @param {HTMLElement} card - Card element
     */
    renderPlaylistSelector(card) {
        const selectorContainer = document.createElement('div');
        selectorContainer.className = 'add-button-card-playlist-selector';
        
        // Create playlist select dropdown
        const select = document.createElement('select');
        select.className = 'add-button-card-playlist-select';
        select.setAttribute('aria-label', 'Select playlist');
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a playlist...';
        select.appendChild(defaultOption);
        
        // Add playlist options
        this.state.playlistOptions.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.id || playlist.playlist_id;
            option.textContent = playlist.name || playlist.metadata?.name || 'Unnamed Playlist';
            select.appendChild(option);
        });
        
        // Set selected value
        if (this.state.selectedPlaylistId) {
            select.value = this.state.selectedPlaylistId;
        }
        
        // Add event listener
        select.addEventListener('change', (event) => {
            this.handlePlaylistSelection(event.target.value);
        });
        
        selectorContainer.appendChild(select);
        card.appendChild(selectorContainer);
    }
    
    /**
     * Handle AddButton state changes
     * @param {Object} stateData - State change data
     */
    handleAddButtonStateChange(stateData) {
        this.state.isAddingToPlaylist = stateData.state.isLoading;
        
        // Update card styling based on AddButton state
        if (this.element) {
            this.element.classList.toggle('adding-to-playlist', stateData.state.isLoading);
            this.element.classList.toggle('add-success', stateData.state.isSuccess);
            this.element.classList.toggle('add-error', stateData.state.isError);
        }
        
        // Emit state change event
        this.emit('addButtonStateChange', stateData);
        
        // Call callback if provided
        if (this.options.onAddButtonStateChange) {
            this.options.onAddButtonStateChange(stateData);
        }
    }
    
    /**
     * Handle AddButton success
     * @param {Object} successData - Success event data
     */
    handleAddButtonSuccess(successData) {
        console.log('AddButtonCard: Song added successfully:', successData);
        
        // Add success animation
        if (this.element) {
            this.element.classList.add('add-success-animation');
            setTimeout(() => {
                this.element?.classList.remove('add-success-animation');
            }, 600);
        }
        
        // Emit success event
        this.emit('addSuccess', successData);
        
        // Call success callback
        if (this.options.onAddSuccess) {
            this.options.onAddSuccess(successData.response, successData.songData, successData.playlistId);
        }
        
        // Refresh playlist data if needed
        if (this.options.refreshAfterSuccess !== false) {
            this.refreshPlaylistData();
        }
    }
    
    /**
     * Handle AddButton error
     * @param {Object} errorData - Error event data
     */
    handleAddButtonError(errorData) {
        console.error('AddButtonCard: AddButton error:', errorData);
        
        // Add error styling
        if (this.element) {
            this.element.classList.add('add-error-animation');
            setTimeout(() => {
                this.element?.classList.remove('add-error-animation');
            }, 600);
        }
        
        // Emit error event
        this.emit('addError', errorData);
        
        // Call error callback
        if (this.options.onAddError) {
            this.options.onAddError(errorData.error, errorData.songData, errorData.playlistId);
        }
    }
    
    /**
     * Handle optimistic update
     * @param {Object} updateData - Optimistic update data
     */
    handleOptimisticUpdate(updateData) {
        console.log('AddButtonCard: Performing optimistic update:', updateData);
        
        // Emit optimistic update event
        this.emit('optimisticUpdate', updateData);
        
        // Update UI optimistically
        if (this.element) {
            this.element.classList.add('optimistic-update');
        }
        
        // Call callback if provided
        if (this.options.onOptimisticUpdate) {
            this.options.onOptimisticUpdate(updateData);
        }
    }
    
    /**
     * Handle revert optimistic update
     * @param {Object} updateData - Revert update data
     */
    handleRevertOptimisticUpdate(updateData) {
        console.log('AddButtonCard: Reverting optimistic update:', updateData);
        
        // Emit revert event
        this.emit('revertOptimisticUpdate', updateData);
        
        // Remove optimistic styling
        if (this.element) {
            this.element.classList.remove('optimistic-update');
        }
        
        // Call callback if provided
        if (this.options.onRevertOptimisticUpdate) {
            this.options.onRevertOptimisticUpdate(updateData);
        }
    }
    
    /**
     * Handle playlist selection
     * @param {string} playlistId - Selected playlist ID
     */
    handlePlaylistSelection(playlistId) {
        this.state.selectedPlaylistId = playlistId;
        
        // Update AddButton playlist ID
        if (this.state.addButtonInstance && playlistId) {
            this.state.addButtonInstance.updatePlaylistId(playlistId);
        }
        
        // Emit selection event
        this.emit('playlistSelection', { playlistId });
        
        // Call callback if provided
        if (this.options.onPlaylistSelection) {
            this.options.onPlaylistSelection(playlistId);
        }
    }
    
    /**
     * Update playlist options
     * @param {Array} playlists - Array of playlist objects
     */
    updatePlaylistOptions(playlists) {
        this.state.playlistOptions = playlists || [];
        
        // Re-render playlist selector if visible
        if (this.state.showPlaylistSelector && this.element) {
            const existingSelector = this.element.querySelector('.add-button-card-playlist-selector');
            if (existingSelector) {
                existingSelector.remove();
            }
            this.renderPlaylistSelector(this.element);
        }
    }
    
    /**
     * Refresh playlist data from server
     */
    async refreshPlaylistData() {
        try {
            const response = await fetch('/api/audio-library/playlists');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.updatePlaylistOptions(data.data.playlists || []);
                }
            }
        } catch (error) {
            console.warn('AddButtonCard: Failed to refresh playlist data:', error);
        }
    }
    
    /**
     * Manually trigger add operation
     * @param {string} playlistId - Optional playlist ID override
     */
    async addToPlaylist(playlistId = null) {
        if (!this.state.addButtonInstance) {
            console.warn('AddButtonCard: AddButton not initialized');
            return;
        }
        
        const targetPlaylistId = playlistId || this.state.selectedPlaylistId;
        if (!targetPlaylistId) {
            console.warn('AddButtonCard: No playlist selected');
            return;
        }
        
        // Update playlist ID if different
        if (this.state.addButtonInstance.options.playlistId !== targetPlaylistId) {
            this.state.addButtonInstance.updatePlaylistId(targetPlaylistId);
        }
        
        // Trigger add operation
        await this.state.addButtonInstance.performAddOperation();
    }
    
    /**
     * Enable the card (and AddButton)
     */
    enable() {
        super.enable();
        
        if (this.state.addButtonInstance) {
            this.state.addButtonInstance.enable();
        }
    }
    
    /**
     * Disable the card (and AddButton)
     */
    disable() {
        super.disable();
        
        if (this.state.addButtonInstance) {
            this.state.addButtonInstance.disable();
        }
    }
    
    /**
     * Reset the card to initial state
     */
    reset() {
        super.reset();
        
        if (this.state.addButtonInstance) {
            this.state.addButtonInstance.reset();
        }
        
        this.state.isAddingToPlaylist = false;
    }
    
    /**
     * Destroy the card and clean up
     */
    destroy() {
        // Destroy AddButton instance
        if (this.state.addButtonInstance) {
            this.state.addButtonInstance.destroy();
            this.state.addButtonInstance = null;
        }
        
        super.destroy();
    }
    
    /**
     * Get AddButton instance
     * @returns {AddButton|null} AddButton instance
     */
    getAddButton() {
        return this.state.addButtonInstance;
    }
    
    /**
     * Get current state including AddButton state
     * @returns {Object} Combined state
     */
    getState() {
        const baseState = super.getState();
        const addButtonState = this.state.addButtonInstance ? 
            this.state.addButtonInstance.getState() : null;
        
        return {
            ...baseState,
            ...this.state,
            addButtonState
        };
    }
    
    /**
     * Format duration helper
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration
     */
    formatDuration(seconds) {
        if (!seconds) return '--:--';
        
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * AddButtonCardFactory for creating multiple instances
 */
class AddButtonCardFactory {
    constructor() {
        this.instances = new Map();
    }
    
    /**
     * Create AddButtonCard instance
     * @param {Object} options - Card options
     * @param {string} id - Optional instance ID
     * @returns {AddButtonCard} Card instance
     */
    create(options, id = null) {
        const instanceId = id || `add-btn-card-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const card = new AddButtonCard(options);
        this.instances.set(instanceId, card);
        return card;
    }
    
    /**
     * Get instance by ID
     * @param {string} id - Instance ID
     * @returns {AddButtonCard|null} Card instance
     */
    get(id) {
        return this.instances.get(id) || null;
    }
    
    /**
     * Destroy instance by ID
     * @param {string} id - Instance ID
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

// Export globally
window.AddButtonCard = AddButtonCard;
window.AddButtonCardFactory = AddButtonCardFactory;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AddButtonCard,
        AddButtonCardFactory
    };
}