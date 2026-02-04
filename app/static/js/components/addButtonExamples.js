/**
 * AddButton Component Usage Examples
 * Comprehensive examples demonstrating various ways to use the AddButton component
 */

// Import required components
// Note: In a real environment, these would be imported properly
// import { AddButton, AddButtonCard, AddButtonFactory } from './addButton.js';
// import { CardFactory } from './cardFactory.js';

console.log('AddButton Examples loaded');

/**
 * Example 1: Basic AddButton Usage
 * Demonstrates the simplest way to create and use an AddButton
 */
class BasicAddButtonExample {
    constructor() {
        this.initialize();
    }

    async initialize() {
        console.log('=== Basic AddButton Example ===');
        
        // Sample song data
        const songData = {
            id: 'song-001',
            title: 'Amazing Song',
            artist: 'Great Artist',
            duration: 180,
            genre: 'Rock'
        };

        // Create AddButton
        const addButton = new AddButton({
            playlistId: 'playlist-123',
            songData: songData
        });

        // Create DOM element
        const buttonElement = addButton.createElement();
        
        // Add to page
        const container = document.getElementById('basic-example');
        if (container) {
            container.appendChild(buttonElement);
        }

        // Add event listeners
        addButton.addEventListener('addButton:success', (event) => {
            console.log('Song added successfully:', event.detail);
        });

        addButton.addEventListener('addButton:error', (event) => {
            console.error('Failed to add song:', event.detail.error);
        });
    }
}

/**
 * Example 2: AddButton with Callbacks
 * Shows how to use callback functions for custom handling
 */
class CallbackAddButtonExample {
    constructor() {
        this.initialize();
    }

    async initialize() {
        console.log('=== AddButton with Callbacks Example ===');
        
        const songData = {
            id: 'song-002',
            title: 'Callback Song',
            artist: 'Callback Artist',
            album: 'Callback Album',
            duration: 210
        };

        const addButton = new AddButton({
            playlistId: 'playlist-456',
            songData: songData,
            
            // Success callback
            onSuccess: (response, songData, playlistId) => {
                this.handleSuccess(response, songData, playlistId);
            },
            
            // Error callback
            onError: (error, songData, playlistId) => {
                this.handleError(error, songData, playlistId);
            },
            
            // State change callback
            onStateChange: (state) => {
                this.handleStateChange(state);
            }
        });

        const buttonElement = addButton.createElement();
        const container = document.getElementById('callback-example');
        if (container) {
            container.appendChild(buttonElement);
        }
    }

    handleSuccess(response, songData, playlistId) {
        console.log('Success! Song added:', songData.title);
        
        // Custom success handling
        this.showNotification(`Successfully added "${songData.title}" to playlist!`, 'success');
        
        // Update UI
        this.updateSongStatus(songData.id, 'added');
        
        // Refresh playlist display
        this.refreshPlaylistDisplay(playlistId);
    }

    handleError(error, songData, playlistId) {
        console.error('Error adding song:', error.message);
        
        // Custom error handling
        let errorMessage = 'Failed to add song to playlist';
        
        if (error.message.includes('already in playlist')) {
            errorMessage = 'This song is already in the playlist';
        } else if (error.message.includes('permission')) {
            errorMessage = 'You don\'t have permission to add songs to this playlist';
        } else if (error.message.includes('not found')) {
            errorMessage = 'Playlist not found';
        }
        
        this.showNotification(errorMessage, 'error');
    }

    handleStateChange(state) {
        console.log('Button state changed:', state);
        
        // Update UI based on state
        const button = document.querySelector('[data-song-id="song-002"]');
        if (button) {
            button.disabled = state.isLoading || state.isDisabled;
            
            if (state.isLoading) {
                button.classList.add('loading');
            } else {
                button.classList.remove('loading');
            }
        }
    }

    showNotification(message, type) {
        // Implementation depends on your notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Example with a simple alert for demonstration
        if (type === 'error') {
            alert(message);
        }
    }

    updateSongStatus(songId, status) {
        // Update song status in the UI
        const songElement = document.querySelector(`[data-song-id="${songId}"]`);
        if (songElement) {
            songElement.classList.add(`status-${status}`);
        }
    }

    refreshPlaylistDisplay(playlistId) {
        // Refresh the playlist display
        console.log(`Refreshing playlist display for: ${playlistId}`);
    }
}

/**
 * Example 3: Multiple AddButtons with Factory
 * Demonstrates creating multiple buttons efficiently using the factory pattern
 */
class FactoryAddButtonExample {
    constructor() {
        this.factory = new AddButtonFactory();
        this.initialize();
    }

    async initialize() {
        console.log('=== Factory AddButton Example ===');
        
        // Sample songs
        const songs = [
            {
                id: 'song-003',
                title: 'Factory Song 1',
                artist: 'Factory Artist 1',
                duration: 195
            },
            {
                id: 'song-004',
                title: 'Factory Song 2',
                artist: 'Factory Artist 2',
                duration: 220
            },
            {
                id: 'song-005',
                title: 'Factory Song 3',
                artist: 'Factory Artist 3',
                duration: 180
            }
        ];

        // Create multiple AddButtons using factory
        const buttons = new Map();
        songs.forEach((song, index) => {
            const buttonId = `factory-button-${index}`;
            
            const button = this.factory.create({
                playlistId: 'playlist-789',
                songData: song,
                variant: 'secondary',
                size: 'small',
                onSuccess: (response, songData, playlistId) => {
                    this.handleFactorySuccess(response, songData, buttonId);
                },
                onError: (error, songData, playlistId) => {
                    this.handleFactoryError(error, songData, buttonId);
                }
            }, buttonId);
            
            buttons.set(buttonId, button);
            
            // Create DOM elements and add to page
            const buttonElement = button.createElement();
            buttonElement.dataset.buttonId = buttonId;
            
            const container = document.getElementById('factory-example');
            if (container) {
                container.appendChild(buttonElement);
            }
        });

        // Store reference for later use
        this.buttons = buttons;
    }

    handleFactorySuccess(response, songData, buttonId) {
        console.log(`Song ${songData.title} added successfully via button ${buttonId}`);
        
        // Disable the specific button that was used
        const button = this.factory.get(buttonId);
        if (button) {
            button.disable();
        }
        
        // Update UI
        this.updateSongStatus(songData.id, 'added');
        
        // Update statistics
        this.updateStatistics();
    }

    handleFactoryError(error, songData, buttonId) {
        console.error(`Failed to add song ${songData.title} via button ${buttonId}:`, error);
        
        // Show error for specific button
        this.showNotification(`Failed to add "${songData.title}"`, 'error');
    }

    updateSongStatus(songId, status) {
        const songElement = document.querySelector(`[data-song-id="${songId}"]`);
        if (songElement) {
            songElement.classList.add(`status-${status}`);
        }
    }

    updateStatistics() {
        // Update success statistics
        const successCount = this.factory.getAll().size;
        console.log(`Total successful additions: ${successCount}`);
    }

    showNotification(message, type) {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    // Clean up all buttons
    destroy() {
        this.factory.destroyAll();
    }
}

/**
 * Example 4: AddButton with Card Integration
 * Shows how to use AddButtonCard for integrated song display and add functionality
 */
class AddButtonCardExample {
    constructor() {
        this.initialize();
    }

    async initialize() {
        console.log('=== AddButton Card Example ===');
        
        const songData = {
            id: 'song-006',
            title: 'Card Song',
            artist: 'Card Artist',
            album: 'Card Album',
            duration: 165,
            genre: 'Pop'
        };

        // Create AddButtonCard
        const addButtonCard = new AddButtonCard({
            songData: songData,
            playlistId: 'playlist-card',
            variant: 'primary',
            size: 'medium',
            showPlaylistSelector: true,
            
            // Callbacks
            onAddSuccess: (response, songData, playlistId) => {
                this.handleCardSuccess(response, songData, playlistId);
            },
            onAddError: (error, songData, playlistId) => {
                this.handleCardError(error, songData, playlistId);
            },
            onPlaylistSelection: (playlistId) => {
                this.handlePlaylistSelection(playlistId);
            }
        });

        // Load playlist options
        await this.loadPlaylistOptions(addButtonCard);

        // Create and add to page
        const cardElement = addButtonCard.createElement();
        const container = document.getElementById('card-example');
        if (container) {
            container.appendChild(cardElement);
        }

        // Store reference
        this.addButtonCard = addButtonCard;
    }

    async loadPlaylistOptions(addButtonCard) {
        try {
            // In a real application, this would fetch from your API
            const playlists = [
                { id: 'playlist-1', name: 'My Favorites' },
                { id: 'playlist-2', name: 'Workout Mix' },
                { id: 'playlist-3', name: 'Chill Vibes' }
            ];
            
            addButtonCard.updatePlaylistOptions(playlists);
        } catch (error) {
            console.error('Failed to load playlist options:', error);
        }
    }

    handleCardSuccess(response, songData, playlistId) {
        console.log('Card: Song added successfully', { songData, playlistId });
        
        // Custom success handling for card
        this.showCardNotification(`Added "${songData.title}" to playlist!`, 'success');
        
        // Update card state
        this.addButtonCard.setState({ isSuccess: true });
        
        // Refresh playlist data
        this.refreshPlaylistData(playlistId);
    }

    handleCardError(error, songData, playlistId) {
        console.error('Card: Error adding song:', error);
        
        // Custom error handling for card
        let message = 'Failed to add song';
        if (error.message.includes('already in playlist')) {
            message = 'Song already in this playlist';
        }
        
        this.showCardNotification(message, 'error');
    }

    handlePlaylistSelection(playlistId) {
        console.log('Playlist selected:', playlistId);
        
        // Custom playlist selection handling
        if (playlistId) {
            // Update UI to show selected playlist
            this.updatePlaylistSelection(playlistId);
        }
    }

    updatePlaylistSelection(playlistId) {
        // Update visual indication of selected playlist
        console.log('Updated playlist selection for:', playlistId);
    }

    refreshPlaylistData(playlistId) {
        // Refresh the playlist data display
        console.log('Refreshing data for playlist:', playlistId);
    }

    showCardNotification(message, type) {
        console.log(`[CARD ${type.toUpperCase()}] ${message}`);
    }
}

/**
 * Example 5: Advanced AddButton with Custom Options
 * Demonstrates advanced configuration options and customization
 */
class AdvancedAddButtonExample {
    constructor() {
        this.initialize();
    }

    async initialize() {
        console.log('=== Advanced AddButton Example ===');
        
        const songData = {
            id: 'song-007',
            title: 'Advanced Song',
            artist: 'Advanced Artist',
            album: 'Advanced Album',
            duration: 240,
            genre: 'Electronic',
            metadata: {
                releaseYear: 2023,
                label: 'Advanced Records',
                explicit: false
            }
        };

        // Create advanced AddButton with comprehensive options
        const addButton = new AddButton({
            playlistId: 'playlist-advanced',
            songData: songData,
            
            // Visual options
            variant: 'minimal',
            size: 'large',
            showTooltip: true,
            showIcon: true,
            
            // Behavior options
            enableValidation: true,
            enableDebouncing: true,
            debounceDelay: 1000,
            enableOptimisticUpdates: true,
            
            // Accessibility options
            ariaLabel: 'Add Advanced Song to My Playlist',
            tooltipText: 'Click to add this amazing song to your playlist',
            
            // Custom callbacks
            onSuccess: (response, songData, playlistId) => {
                this.handleAdvancedSuccess(response, songData, playlistId);
            },
            onError: (error, songData, playlistId) => {
                this.handleAdvancedError(error, songData, playlistId);
            },
            onStateChange: (state) => {
                this.handleAdvancedStateChange(state);
            },
            onClick: (event, songData, playlistId) => {
                return this.handleAdvancedClick(event, songData, playlistId);
            }
        });

        // Create and style the button
        const buttonElement = addButton.createElement();
        
        // Add custom styling
        buttonElement.classList.add('custom-advanced-button');
        
        // Add to page
        const container = document.getElementById('advanced-example');
        if (container) {
            container.appendChild(buttonElement);
        }

        // Add comprehensive event listeners
        this.setupAdvancedEventListeners(addButton);
        
        // Store reference
        this.addButton = addButton;
    }

    setupAdvancedEventListeners(addButton) {
        // Listen to all custom events
        addButton.addEventListener('addButton:optimisticUpdate', (event) => {
            console.log('Optimistic update:', event.detail);
            this.showNotification('Adding song...', 'info');
        });

        addButton.addEventListener('addButton:revertOptimisticUpdate', (event) => {
            console.log('Reverting optimistic update:', event.detail);
            this.showNotification('Operation failed, reverting changes', 'warning');
        });

        addButton.addEventListener('addButton:stateChange', (event) => {
            this.logStateChanges(event.detail.state);
        });
    }

    handleAdvancedSuccess(response, songData, playlistId) {
        console.log('Advanced: Success!', { songData, playlistId });
        
        // Advanced success handling
        this.showNotification(`🎉 Successfully added "${songData.title}" to playlist!`, 'success');
        
        // Update analytics
        this.trackAnalytics('song_added', {
            songId: songData.id,
            playlistId: playlistId,
            songGenre: songData.genre,
            duration: songData.duration
        });
        
        // Trigger custom events
        document.dispatchEvent(new CustomEvent('songAddedToPlaylist', {
            detail: { songData, playlistId, response }
        }));
    }

    handleAdvancedError(error, songData, playlistId) {
        console.error('Advanced: Error!', error);
        
        // Advanced error handling with detailed logging
        const errorContext = {
            songId: songData.id,
            playlistId: playlistId,
            errorType: this.categorizeError(error),
            timestamp: new Date().toISOString()
        };
        
        console.error('Error context:', errorContext);
        
        // User-friendly error messages
        let userMessage = 'Failed to add song to playlist';
        switch (errorContext.errorType) {
            case 'duplicate':
                userMessage = 'This song is already in your playlist';
                break;
            case 'permission':
                userMessage = 'You don\'t have permission to modify this playlist';
                break;
            case 'validation':
                userMessage = 'Invalid song data provided';
                break;
            case 'network':
                userMessage = 'Network error. Please check your connection';
                break;
            default:
                userMessage = `Error: ${error.message}`;
        }
        
        this.showNotification(`❌ ${userMessage}`, 'error');
        
        // Track error analytics
        this.trackAnalytics('song_add_failed', errorContext);
    }

    handleAdvancedStateChange(state) {
        console.log('Advanced: State changed', state);
        
        // Advanced state management
        if (state.isLoading) {
            this.showProgressIndicator();
        } else {
            this.hideProgressIndicator();
        }
        
        if (state.isError && state.errorMessage) {
            this.showErrorDetails(state.errorMessage);
        }
    }

    handleAdvancedClick(event, songData, playlistId) {
        console.log('Advanced: Button clicked', { songData, playlistId });
        
        // Custom click handling
        const clickContext = {
            songId: songData.id,
            playlistId: playlistId,
            timestamp: Date.now()
        };
        
        // Log click for analytics
        this.trackAnalytics('add_button_clicked', clickContext);
        
        // Return false to prevent default behavior if needed
        // return false;
        
        return true; // Allow default behavior
    }

    categorizeError(error) {
        const message = error.message.toLowerCase();
        
        if (message.includes('already in playlist')) return 'duplicate';
        if (message.includes('permission') || message.includes('forbidden')) return 'permission';
        if (message.includes('invalid') || message.includes('validation')) return 'validation';
        if (message.includes('network') || message.includes('fetch')) return 'network';
        
        return 'unknown';
    }

    trackAnalytics(event, data) {
        // Implementation depends on your analytics system
        console.log('Analytics:', event, data);
        
        // Example: Google Analytics, Mixpanel, etc.
        // gtag('event', event, data);
        // mixpanel.track(event, data);
    }

    showProgressIndicator() {
        // Show loading indicator
        console.log('Showing progress indicator...');
    }

    hideProgressIndicator() {
        // Hide loading indicator
        console.log('Hiding progress indicator...');
    }

    showErrorDetails(errorMessage) {
        // Show detailed error information
        console.log('Error details:', errorMessage);
    }

    showNotification(message, type) {
        console.log(`[ADVANCED ${type.toUpperCase()}] ${message}`);
    }

    logStateChanges(state) {
        console.log('State changes:', JSON.stringify(state, null, 2));
    }
}

/**
 * Example 6: Playlist Management Integration
 * Shows how to integrate AddButton with a complete playlist management system
 */
class PlaylistManagerExample {
    constructor() {
        this.factory = new AddButtonFactory();
        this.playlists = new Map();
        this.songs = [];
        this.initialize();
    }

    async initialize() {
        console.log('=== Playlist Manager Example ===');
        
        // Load initial data
        await this.loadPlaylists();
        await this.loadSongs();
        
        // Create UI components
        this.createPlaylistDisplay();
        this.createSongList();
        
        // Set up event listeners
        this.setupEventListeners();
    }

    async loadPlaylists() {
        // In a real app, this would fetch from API
        const mockPlaylists = [
            { id: 'pl-1', name: 'My Favorites', songCount: 15 },
            { id: 'pl-2', name: 'Workout Mix', songCount: 23 },
            { id: 'pl-3', name: 'Chill Vibes', songCount: 8 },
            { id: 'pl-4', name: 'Party Playlist', songCount: 31 }
        ];
        
        mockPlaylists.forEach(playlist => {
            this.playlists.set(playlist.id, playlist);
        });
    }

    async loadSongs() {
        // In a real app, this would fetch from API
        const mockSongs = [
            { id: 'song-1', title: 'Song One', artist: 'Artist One', duration: 180 },
            { id: 'song-2', title: 'Song Two', artist: 'Artist Two', duration: 210 },
            { id: 'song-3', title: 'Song Three', artist: 'Artist Three', duration: 195 },
            { id: 'song-4', title: 'Song Four', artist: 'Artist Four', duration: 225 }
        ];
        
        this.songs = mockSongs;
    }

    createPlaylistDisplay() {
        const container = document.getElementById('playlist-manager-example');
        if (!container) return;
        
        // Create playlists section
        const playlistsSection = document.createElement('div');
        playlistsSection.innerHTML = '<h3>My Playlists</h3>';
        
        this.playlists.forEach(playlist => {
            const playlistElement = document.createElement('div');
            playlistElement.className = 'playlist-item';
            playlistElement.innerHTML = `
                <span class="playlist-name">${playlist.name}</span>
                <span class="playlist-count">${playlist.songCount} songs</span>
            `;
            playlistsSection.appendChild(playlistElement);
        });
        
        container.appendChild(playlistsSection);
    }

    createSongList() {
        const container = document.getElementById('playlist-manager-example');
        if (!container) return;
        
        // Create songs section
        const songsSection = document.createElement('div');
        songsSection.innerHTML = '<h3>Available Songs</h3>';
        
        this.songs.forEach(song => {
            const songElement = this.createSongWithAddButton(song);
            songsSection.appendChild(songElement);
        });
        
        container.appendChild(songsSection);
    }

    createSongWithAddButton(song) {
        // Create song element
        const songElement = document.createElement('div');
        songElement.className = 'song-item';
        songElement.dataset.songId = song.id;
        
        songElement.innerHTML = `
            <div class="song-info">
                <span class="song-title">${song.title}</span>
                <span class="song-artist">${song.artist}</span>
                <span class="song-duration">${this.formatDuration(song.duration)}</span>
            </div>
            <div class="song-actions" id="actions-${song.id}">
                <!-- AddButtons will be inserted here -->
            </div>
        `;
        
        // Create AddButton for each playlist
        this.playlists.forEach((playlist, playlistId) => {
            const addButton = this.factory.create({
                playlistId: playlistId,
                songData: song,
                variant: 'minimal',
                size: 'small',
                onSuccess: (response, songData, playlistId) => {
                    this.handlePlaylistAddSuccess(response, songData, playlistId);
                },
                onError: (error, songData, playlistId) => {
                    this.handlePlaylistAddError(error, songData, playlistId);
                }
            }, `song-${song.id}-playlist-${playlistId}`);
            
            const buttonElement = addButton.createElement();
            const actionsContainer = songElement.querySelector(`#actions-${song.id}`);
            actionsContainer.appendChild(buttonElement);
        });
        
        return songElement;
    }

    setupEventListeners() {
        // Listen for custom events
        document.addEventListener('songAddedToPlaylist', (event) => {
            this.handleSongAddedEvent(event.detail);
        });
        
        // Listen for playlist updates
        document.addEventListener('playlistsUpdated', (event) => {
            this.handlePlaylistsUpdated(event.detail);
        });
    }

    handlePlaylistAddSuccess(response, songData, playlistId) {
        console.log(`Song "${songData.title}" added to playlist ${playlistId}`);
        
        // Update playlist song count
        const playlist = this.playlists.get(playlistId);
        if (playlist) {
            playlist.songCount++;
            this.updatePlaylistDisplay(playlistId);
        }
        
        // Disable all AddButtons for this song
        this.disableAddButtonsForSong(songData.id);
        
        // Show success notification
        this.showNotification(`Added "${songData.title}" to ${this.playlists.get(playlistId)?.name}!`, 'success');
        
        // Emit event for other components
        document.dispatchEvent(new CustomEvent('playlistUpdated', {
            detail: { playlistId, songData, action: 'added' }
        }));
    }

    handlePlaylistAddError(error, songData, playlistId) {
        console.error(`Failed to add "${songData.title}" to playlist ${playlistId}:`, error);
        
        // Handle specific error types
        if (error.message.includes('already in playlist')) {
            this.showNotification(`"${songData.title}" is already in this playlist`, 'info');
        } else {
            this.showNotification(`Failed to add "${songData.title}" to playlist`, 'error');
        }
    }

    handleSongAddedEvent(detail) {
        console.log('Song added event received:', detail);
        
        // Update UI based on song addition
        this.updateSongStatus(detail.songData.id, 'added');
    }

    handlePlaylistsUpdated(detail) {
        console.log('Playlists updated event received:', detail);
        
        // Refresh playlist display
        this.refreshPlaylistDisplay();
    }

    updatePlaylistDisplay(playlistId) {
        const playlistElement = document.querySelector(`[data-playlist-id="${playlistId}"]`);
        if (playlistElement) {
            const playlist = this.playlists.get(playlistId);
            const countElement = playlistElement.querySelector('.playlist-count');
            if (countElement && playlist) {
                countElement.textContent = `${playlist.songCount} songs`;
            }
        }
    }

    disableAddButtonsForSong(songId) {
        // Disable all AddButtons for a specific song
        const songElement = document.querySelector(`[data-song-id="${songId}"]`);
        if (songElement) {
            const buttons = songElement.querySelectorAll('.add-button');
            buttons.forEach(button => {
                button.disabled = true;
                button.classList.add('added');
            });
        }
    }

    updateSongStatus(songId, status) {
        const songElement = document.querySelector(`[data-song-id="${songId}"]`);
        if (songElement) {
            songElement.classList.add(`status-${status}`);
        }
    }

    refreshPlaylistDisplay() {
        // Refresh the entire playlist display
        const container = document.getElementById('playlist-manager-example');
        if (container) {
            // Clear and recreate playlists section
            const oldPlaylistsSection = container.querySelector('div:first-child');
            if (oldPlaylistsSection) {
                oldPlaylistsSection.remove();
            }
            this.createPlaylistDisplay();
        }
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    showNotification(message, type) {
        console.log(`[PLAYLIST MANAGER ${type.toUpperCase()}] ${message}`);
        
        // You could implement a proper notification system here
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Clean up
    destroy() {
        this.factory.destroyAll();
    }
}

/**
 * Example 7: Testing and Debugging
 * Shows how to test and debug AddButton components
 */
class TestingAddButtonExample {
    constructor() {
        this.initialize();
    }

    async initialize() {
        console.log('=== Testing AddButton Example ===');
        
        // Create test song data
        const testSongs = this.generateTestSongs();
        
        // Create test buttons with different scenarios
        this.createTestScenarios(testSongs);
        
        // Set up debugging features
        this.setupDebugging();
    }

    generateTestSongs() {
        return [
            {
                id: 'test-song-1',
                title: 'Valid Test Song',
                artist: 'Test Artist',
                duration: 180
            },
            {
                id: 'test-song-2',
                title: '', // Invalid - empty title
                artist: 'Test Artist'
            },
            {
                id: 'test-song-3',
                title: 'Long Song Title That Exceeds The Normal Length Limit',
                artist: 'Test Artist With Very Long Name'
            },
            {
                id: 'test-song-4',
                title: 'Test Song 4',
                artist: 'Test Artist 4',
                duration: -10 // Invalid duration
            }
        ];
    }

    createTestScenarios(songs) {
        const container = document.getElementById('testing-example');
        if (!container) return;
        
        songs.forEach((song, index) => {
            const testElement = document.createElement('div');
            testElement.className = 'test-scenario';
            testElement.innerHTML = `
                <h4>Test Scenario ${index + 1}</h4>
                <p>Song: ${song.title || '[EMPTY TITLE]'}</p>
                <p>Artist: ${song.artist}</p>
                <p>Duration: ${song.duration || 'undefined'}</p>
                <div class="test-result" id="result-${index}"></div>
            `;
            
            container.appendChild(testElement);
            
            // Create AddButton for this test scenario
            try {
                const addButton = new AddButton({
                    playlistId: 'test-playlist',
                    songData: song,
                    onSuccess: (response, songData, playlistId) => {
                        this.handleTestSuccess(index, response, songData);
                    },
                    onError: (error, songData, playlistId) => {
                        this.handleTestError(index, error, songData);
                    }
                });
                
                const buttonElement = addButton.createElement();
                testElement.appendChild(buttonElement);
                
            } catch (error) {
                console.error(`Failed to create AddButton for test ${index}:`, error);
                this.showTestResult(index, 'Failed to create AddButton', 'error');
            }
        });
    }

    setupDebugging() {
        // Add debugging controls
        const debugControls = document.createElement('div');
        debugControls.innerHTML = `
            <h4>Debug Controls</h4>
            <button id="debug-all">Test All Buttons</button>
            <button id="reset-all">Reset All</button>
            <button id="show-state">Show State</button>
            <div id="debug-output"></div>
        `;
        
        const container = document.getElementById('testing-example');
        if (container) {
            container.appendChild(debugControls);
            
            // Add event listeners for debug controls
            document.getElementById('debug-all').addEventListener('click', () => {
                this.debugAllButtons();
            });
            
            document.getElementById('reset-all').addEventListener('click', () => {
                this.resetAllButtons();
            });
            
            document.getElementById('show-state').addEventListener('click', () => {
                this.showDebugState();
            });
        }
    }

    handleTestSuccess(testIndex, response, songData) {
        console.log(`Test ${testIndex} success:`, response);
        this.showTestResult(testIndex, '✅ SUCCESS: Song added successfully', 'success');
    }

    handleTestError(testIndex, error, songData) {
        console.log(`Test ${testIndex} error:`, error);
        const errorType = this.categorizeTestError(error);
        this.showTestResult(testIndex, `❌ ERROR (${errorType}): ${error.message}`, 'error');
    }

    categorizeTestError(error) {
        if (error.message.includes('validation')) return 'VALIDATION';
        if (error.message.includes('network')) return 'NETWORK';
        if (error.message.includes('permission')) return 'PERMISSION';
        return 'UNKNOWN';
    }

    showTestResult(testIndex, message, type) {
        const resultElement = document.getElementById(`result-${testIndex}`);
        if (resultElement) {
            resultElement.textContent = message;
            resultElement.className = `test-result ${type}`;
        }
    }

    debugAllButtons() {
        console.log('=== Debugging All AddButtons ===');
        
        // Find all AddButtons on the page
        const addButtons = document.querySelectorAll('[data-add-button]');
        console.log(`Found ${addButtons.length} AddButtons`);
        
        addButtons.forEach((button, index) => {
            console.log(`AddButton ${index}:`, {
                element: button,
                playlistId: button.dataset.playlistId,
                songId: button.dataset.songId,
                className: button.className,
                disabled: button.disabled
            });
        });
    }

    resetAllButtons() {
        console.log('=== Resetting All AddButtons ===');
        
        // Reset button states
        const addButtons = document.querySelectorAll('[data-add-button]');
        addButtons.forEach(button => {
            button.disabled = false;
            button.className = button.className.replace(/btn-(loading|success|error)/g, '');
        });
        
        // Clear test results
        const results = document.querySelectorAll('.test-result');
        results.forEach(result => {
            result.textContent = '';
            result.className = 'test-result';
        });
        
        console.log('All buttons reset');
    }

    showDebugState() {
        const output = document.getElementById('debug-output');
        if (output) {
            output.innerHTML = '<pre>' + JSON.stringify({
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                addButtonCount: document.querySelectorAll('[data-add-button]').length,
                errors: this.getTestErrors()
            }, null, 2) + '</pre>';
        }
    }

    getTestErrors() {
        const errors = [];
        const errorElements = document.querySelectorAll('.test-result.error');
        errorElements.forEach(element => {
            errors.push(element.textContent);
        });
        return errors;
    }
}

/**
 * Initialize all examples when the page loads
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing AddButton examples...');
    
    // Create containers if they don't exist
    const containers = [
        'basic-example',
        'callback-example', 
        'factory-example',
        'card-example',
        'advanced-example',
        'playlist-manager-example',
        'testing-example'
    ];
    
    containers.forEach(containerId => {
        if (!document.getElementById(containerId)) {
            const container = document.createElement('div');
            container.id = containerId;
            container.className = 'example-container';
            document.body.appendChild(container);
        }
    });
    
    // Initialize examples (comment out ones you don't want to run)
    try {
        new BasicAddButtonExample();
        new CallbackAddButtonExample();
        new FactoryAddButtonExample();
        new AddButtonCardExample();
        new AdvancedAddButtonExample();
        new PlaylistManagerExample();
        new TestingAddButtonExample();
    } catch (error) {
        console.error('Error initializing examples:', error);
    }
});

// Export examples for external use
if (typeof window !== 'undefined') {
    window.AddButtonExamples = {
        BasicAddButtonExample,
        CallbackAddButtonExample,
        FactoryAddButtonExample,
        AddButtonCardExample,
        AdvancedAddButtonExample,
        PlaylistManagerExample,
        TestingAddButtonExample
    };
}