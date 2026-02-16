/**
 * Song Library Component
 * Manages the user audio library interface and operations
 */

class SongLibrary {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.currentSort = 'created_at_desc';
        this.currentFilters = {};
        this.currentSearch = '';
        this.currentPlayingId = null;
        this.playlists = [];
        this.isLoading = false;
        this.totalPages = 0;
        
        // DOM elements (will be set during initialization)
        this.elements = {};
        
        // Event handlers
        this.debounceTimer = null;
        this.refreshDebounceTimer = null;
        this.activeMenu = null;
        this.activeMenuCloseHandler = null;
        this.lyricsPollingIds = new Set();
    }
    
    initialize(elements) {
        console.log('Initializing Song Library component...');
        
        // Set DOM elements
        this.elements = elements;
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up library update listeners
        this.setupLibraryUpdateListeners();
        
        // Load initial data
        this.loadLibrary();
        
        console.log('Song Library component initialized successfully.');
    }
    
    setupEventListeners() {
        // Refresh button
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => this.refreshLibrary());
        }
        
        // Search input with debounce
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => {
                    this.currentSearch = e.target.value.trim();
                    this.currentPage = 1;
                    this.loadLibrary();
                }, 300);
            });
            
            // Accessibility: announce search results
            this.elements.searchInput.setAttribute('aria-describedby', 'search-help');
        }
        
        // Sort select
        if (this.elements.sortSelect) {
            this.elements.sortSelect.addEventListener('change', (e) => {
                const [sortBy, sortOrder] = e.target.value.split('_');
                this.currentSort = e.target.value;
                this.currentPage = 1;
                this.loadLibrary();
            });
            
            this.elements.sortSelect.setAttribute('aria-label', 'Sort songs by');
        }
        
        // Filter selects
        if (this.elements.genreFilter) {
            this.elements.genreFilter.addEventListener('change', () => this.updateFilters());
            this.elements.genreFilter.setAttribute('aria-label', 'Filter by genre');
        }
        
        if (this.elements.sourceFilter) {
            this.elements.sourceFilter.addEventListener('change', () => this.updateFilters());
            this.elements.sourceFilter.setAttribute('aria-label', 'Filter by source');
        }
        
        // Favorites filter
        if (this.elements.favoritesFilter) {
            this.elements.favoritesFilter.addEventListener('click', () => this.toggleFavoritesFilter());
            this.elements.favoritesFilter.setAttribute('aria-pressed', 'false');
            this.elements.favoritesFilter.setAttribute('aria-label', 'Show favorite songs only');
        }
        
        // Create playlist button
        if (this.elements.createPlaylistBtn) {
            this.elements.createPlaylistBtn.addEventListener('click', () => this.showCreatePlaylistModal());
            this.elements.createPlaylistBtn.setAttribute('aria-label', 'Create new playlist');
        }

        // Your Playlists button - using event delegation for robustness
        // This ensures the click is captured even if the element was replaced or not ready during init
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('#songLibraryYourPlaylistsBtn');
            if (btn) {
                console.log('Your Playlists button clicked (delegated)');
                e.preventDefault();
                this.showYourPlaylistsModal();
            }
        });

        if (this.elements.yourPlaylistsBtn) {
            this.elements.yourPlaylistsBtn.setAttribute('aria-label', 'View your playlists');
        }
        
        // Retry button
        if (this.elements.retryBtn) {
            this.elements.retryBtn.addEventListener('click', () => this.loadLibrary());
            this.elements.retryBtn.setAttribute('aria-label', 'Retry loading library');
        }
        
        // Pagination buttons
        if (this.elements.pagination?.prevBtn) {
            this.elements.pagination.prevBtn.addEventListener('click', () => this.goToPreviousPage());
            this.elements.pagination.prevBtn.setAttribute('aria-label', 'Go to previous page');
        }
        
        if (this.elements.pagination?.nextBtn) {
            this.elements.pagination.nextBtn.addEventListener('click', () => this.goToNextPage());
            this.elements.pagination.nextBtn.setAttribute('aria-label', 'Go to next page');
        }
        
        // Keyboard navigation for pagination
        this.setupPaginationKeyboardNavigation();
    }
    
    setupLibraryUpdateListeners() {
        // Listen for audio library updates from other components
        document.addEventListener('audioLibraryUpdated', (event) => {
            console.log('Audio library updated:', event.detail);
            if (event.detail && event.detail.track && event.detail.action === 'added') {
                this.addSongToDOM(event.detail.track);
            } else {
                // Fallback to refresh for other actions like delete, or if track data is missing
                this.refreshLibrary();
            }
        });
    }
    
    setupPaginationKeyboardNavigation() {
        // Add keyboard navigation for pagination
        if (this.elements.pagination?.container) {
            this.elements.pagination.container.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowLeft' && !this.elements.pagination.prevBtn.disabled) {
                    e.preventDefault();
                    this.goToPreviousPage();
                    this.elements.pagination.prevBtn.focus();
                } else if (e.key === 'ArrowRight' && !this.elements.pagination.nextBtn.disabled) {
                    e.preventDefault();
                    this.goToNextPage();
                    this.elements.pagination.nextBtn.focus();
                }
            });
        }
        
        // Add keyboard navigation for song cards
        if (this.elements.container) {
            this.elements.container.addEventListener('keydown', (e) => {
                if (e.key === ' ' || e.key === 'Enter') {
                    const songCard = e.target.closest('.song-card');
                    if (songCard) {
                        e.preventDefault();
                        const playBtn = songCard.querySelector('.song-play-btn');
                        if (playBtn) {
                            playBtn.click();
                        }
                    }
                }
            });
        }
    }
    
    async loadLibrary() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.itemsPerPage,
                sort_by: this.currentSort.split('_')[0],
                sort_order: this.currentSort.split('_')[1]
            });
            
            // Add search query
            if (this.currentSearch) {
                params.append('search', this.currentSearch);
            }
            
            // Add filters
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value) {
                    params.append(key, value);
                }
            });
            
            // Make API request
            const response = await fetch(`/api/audio-library?${params}`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.renderLibrary(data.data.audio_library);
                this.renderPagination(data.data.pagination);
                this.updateStats(data.data.stats || {});
                this.hideAllStates();
            } else {
                throw new Error(data.error || 'Failed to load library');
            }
            
        } catch (error) {
            console.error('Error loading library:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    renderLibrary(songs) {
        if (!this.elements.container) return;
        
        this.elements.container.innerHTML = '';
        
        if (!songs || songs.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Create song cards
        songs.forEach(song => {
            const songCard = this.createSongCard(song);
            this.elements.container.appendChild(songCard);

            if (this.shouldPollLyricsStatus(song)) {
                this.startLyricsStatusPolling(song.id);
            }
        });
        
        this.elements.container.classList.remove('hidden');
    }

    addSongToDOM(song) {
        if (!this.elements.container) return;

        // Use the existing card creation logic to maintain consistency
        const card = this.createSongCard(song);

        // Now 'card' is a DOM element, so we can set attributes
        card.setAttribute('data-status', 'new');
        card.classList.add('new-song-fade-in'); // Example for a nice animation

        // Add the new song to the top of the library
        this.elements.container.prepend(card);

        // If the library was empty, hide the empty state message
        this.hideAllStates();
        this.elements.container.classList.remove('hidden');

        if (this.shouldPollLyricsStatus(song)) {
            this.startLyricsStatusPolling(song.id);
        }
    }

    shouldPollLyricsStatus(song) {
        const status = song?.lyrics_extraction_status;
        return status === 'queued' || status === 'processing';
    }

    async startLyricsStatusPolling(songId, maxAttempts = 30, intervalMs = 4000) {
        if (!songId || this.lyricsPollingIds.has(songId)) {
            return;
        }

        this.lyricsPollingIds.add(songId);

        try {
            for (let attempt = 0; attempt < maxAttempts; attempt++) {
                await new Promise(resolve => setTimeout(resolve, intervalMs));

                const response = await fetch(`/api/audio-library/${songId}/lyrics-status`);
                const data = await response.json();

                if (!response.ok || !data.success) {
                    break;
                }

                const status = data.data?.lyrics_extraction_status;
                if (status === 'completed' || status === 'failed' || status === 'not_requested') {
                    this.refreshLibrary();
                    break;
                }
            }
        } catch (error) {
            console.error('Lyrics status polling failed:', error);
        } finally {
            this.lyricsPollingIds.delete(songId);
        }
    }
    
    /**
     * Create a song card element using the unified card system.
     * @param {Object} song - Song object
     * @returns {HTMLElement} Song card element
     */
    createSongCard(song) {
        // Create a new SongCard instance
        const card = new SongCard({
            id: `song-card-${song.id}`,
            data: song,
            variant: 'default',
            showControls: true,
            clickable: true,
            hoverable: true
        });
        
        // Set up callbacks for song-specific actions
        card.setCallbacks({
            onAction: (action, data, event) => {
                this.handleSongCardAction(action, data, event);
            }
        });
        
        // Create and return the card element
        return card.createElement();
    }
    
    /**
     * Handle song card actions
     * @param {string} action - Action type
     * @param {Object} song - Song data
     * @param {Event} event - Event object
     */
    handleSongCardAction(action, song, event) {
        switch (action) {
            case 'play-pause':
                this.handlePlayPause(song, event);
                break;
            case 'toggle-favorite':
                this.handleToggleFavorite(song, event);
                break;
            case 'show-menu':
                this.showSongMenu(song, event.target);
                break;
            case 'add':
                this.showAddToPlaylistModal(song);
                break;
            case 'download':
                this.downloadSong(song);
                break;
            case 'edit':
                this.showEditModal(song);
                break;
        }
    }
    
    /**
     * Handle play/pause action
     * @param {Object} song - Song data
     * @param {Event} event - Event object
     */
    handlePlayPause(song, event) {
        const cardElement = event.target.closest('.song-card');
        const audioElement = cardElement?.querySelector('[data-audio-element]');
        const playIcon = cardElement?.querySelector('[data-play-icon]');
        const pauseIcon = cardElement?.querySelector('[data-pause-icon]');
        
        if (audioElement) {
            this.togglePlayPause(song, audioElement, playIcon, pauseIcon);
        }
    }
    
    /**
     * Handle toggle favorite action
     * @param {Object} song - Song data
     * @param {Event} event - Event object
     */
    handleToggleFavorite(song, event) {
        const favoriteBtn = event.target.closest('.song-favorite-btn');
        if (favoriteBtn) {
            this.toggleFavorite(song.id, favoriteBtn);
        }
    }
    
    setupSongCardEventListeners(card, song) {
        // Play/pause button
        const playBtn = card.querySelector('.song-play-btn');
        const playIcon = card.querySelector('[data-play-icon]');
        const pauseIcon = card.querySelector('[data-pause-icon]');
        const audioElement = card.querySelector('[data-audio-element]');
        
        if (playBtn && audioElement) {
            playBtn.setAttribute('aria-label', `Play ${song.title || 'song'}`);
            playBtn.setAttribute('aria-describedby', `song-info-${song.id}`);
            
            playBtn.addEventListener('click', async () => {
                await this.togglePlayPause(song, audioElement, playIcon, pauseIcon);
                
                // Update aria-label based on state
                const isPlaying = !audioElement.paused;
                playBtn.setAttribute('aria-label', `${isPlaying ? 'Pause' : 'Play'} ${song.title || 'song'}`);
            });
            
            // Audio event listeners
            audioElement.addEventListener('loadedmetadata', () => {
                const durationEl = card.querySelector('[data-duration]');
                if (durationEl) {
                    durationEl.textContent = this.formatDuration(audioElement.duration);
                }
            });
            
            audioElement.addEventListener('timeupdate', () => {
                const progressEl = card.querySelector('[data-progress]');
                const currentTimeEl = card.querySelector('.song-current-time');
                
                if (progressEl && audioElement.duration) {
                    const progress = (audioElement.currentTime / audioElement.duration) * 100;
                    progressEl.style.width = `${progress}%`;
                }
                
                if (currentTimeEl) {
                    currentTimeEl.textContent = this.formatDuration(audioElement.currentTime);
                }
            });
            
            audioElement.addEventListener('ended', () => {
                if (playIcon && pauseIcon) {
                    playIcon.classList.remove('hidden');
                    pauseIcon.classList.add('hidden');
                }
                playBtn.setAttribute('aria-label', `Play ${song.title || 'song'}`);
            });
            
            // Progress bar click
            const progressBar = card.querySelector('.song-progress-bar');
            if (progressBar) {
                progressBar.setAttribute('role', 'slider');
                progressBar.setAttribute('aria-label', `Seek in ${song.title || 'song'}`);
                progressBar.setAttribute('aria-valuemin', '0');
                progressBar.setAttribute('aria-valuemax', '100');
                
                progressBar.addEventListener('click', (e) => {
                    if (audioElement.duration) {
                        const rect = progressBar.getBoundingClientRect();
                        const clickX = e.clientX - rect.left;
                        const width = rect.width;
                        const newTime = (clickX / width) * audioElement.duration;
                        audioElement.currentTime = newTime;
                        
                        // Update aria-valuenow
                        const progress = (newTime / audioElement.duration) * 100;
                        progressBar.setAttribute('aria-valuenow', Math.round(progress));
                    }
                });
            }
        }
        
        // Favorite button
        const favoriteBtn = card.querySelector('.song-favorite-btn');
        if (favoriteBtn) {
            favoriteBtn.setAttribute('aria-label', `${song.is_favorite ? 'Remove from' : 'Add to'} favorites`);
            favoriteBtn.setAttribute('aria-pressed', song.is_favorite ? 'true' : 'false');
            
            favoriteBtn.addEventListener('click', () => {
                this.toggleFavorite(song.id, favoriteBtn);
            });
        }
        
        // Menu button (placeholder for future context menu)
        const menuBtn = card.querySelector('.song-menu-btn');
        if (menuBtn) {
            menuBtn.setAttribute('aria-label', `More options for ${song.title || 'song'}`);
            menuBtn.addEventListener('click', () => this.showSongMenu(song, menuBtn));
        }
        
        // Action buttons
        const addToPlaylistBtn = card.querySelector('.song-add-to-playlist-btn');
        if (addToPlaylistBtn) {
            addToPlaylistBtn.setAttribute('aria-label', `Add ${song.title || 'song'} to playlist`);
            addToPlaylistBtn.addEventListener('click', () => this.showAddToPlaylistModal(song));
        }
        
        const downloadBtn = card.querySelector('.song-download-btn');
        if (downloadBtn) {
            downloadBtn.setAttribute('aria-label', `Download ${song.title || 'song'}`);
            downloadBtn.addEventListener('click', () => this.downloadSong(song));
        }
        
        const editBtn = card.querySelector('.song-edit-btn');
        if (editBtn) {
            editBtn.setAttribute('aria-label', `Edit ${song.title || 'song'} metadata`);
            editBtn.addEventListener('click', () => this.showEditModal(song));
        }
        
        // Add song info ID for ARIA descriptions
        card.setAttribute('id', `song-card-${song.id}`);
        const titleEl = card.querySelector('[data-song-title]');
        if (titleEl) {
            titleEl.setAttribute('id', `song-info-${song.id}`);
        }
    }
    
    async togglePlayPause(song, audioElement, playIcon, pauseIcon) {
        const songId = song.id;
        try {
            if (!song.audio_url) {
                this.showNotification('No audio URL available for playback', 'error');
                return;
            }
            // If another song is playing, pause it first.
            if (this.currentPlayingId && this.currentPlayingId !== songId) {
                const currentAudio = document.querySelector(`[data-song-id="${this.currentPlayingId}"]`);
                if (currentAudio) {
                    currentAudio.pause();
                    this.resetPlayButton(this.currentPlayingId);
                }
            }

            if (audioElement.paused) {
                // Check if the source needs to be reloaded.
                // This is important for newly added songs where the src might not be fully recognized.
                if (audioElement.currentSrc !== song.audio_url) {
                    audioElement.src = song.audio_url;
                    audioElement.load();
                }

                const playPromise = audioElement.play();
                if (playPromise !== undefined) {
                    playPromise.then(_ => {
                        // Automatic playback started!
                        this.currentPlayingId = songId;
                        if (playIcon && pauseIcon) {
                            playIcon.classList.add('hidden');
                            pauseIcon.classList.remove('hidden');
                        }
                        this.incrementPlayCount(songId);
                    }).catch(error => {
                        if (error.name === 'AbortError') {
                            // This can happen if the user quickly clicks play/pause again.
                            // The pause action interrupts the play promise. We can safely ignore this.
                            console.log('Playback aborted, likely by user action.');
                        } else {
                            console.error('Error playing audio:', error);
                            this.showNotification('Error playing audio', 'error');
                        }
                    });
                }
            } else {
                audioElement.pause();
                this.currentPlayingId = null;
                if (playIcon && pauseIcon) {
                    playIcon.classList.remove('hidden');
                    pauseIcon.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('General error in togglePlayPause:', error);
            this.showNotification('An unexpected error occurred.', 'error');
        }
    }
    
    resetPlayButton(songId) {
        const card = document.querySelector(`[data-song-id="${songId}"]`)?.closest('.song-card');
        if (card) {
            const playIcon = card.querySelector('[data-play-icon]');
            const pauseIcon = card.querySelector('[data-pause-icon]');
            if (playIcon && pauseIcon) {
                playIcon.classList.remove('hidden');
                pauseIcon.classList.add('hidden');
            }
        }
    }
    
    async toggleFavorite(songId, favoriteBtn) {
        try {
            const response = await fetch(`/api/audio-library/${songId}/favorite`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                const favoriteIcon = favoriteBtn.querySelector('[data-favorite-icon]');
                const notFavoriteIcon = favoriteBtn.querySelector('[data-not-favorite-icon]');
                
                if (data.data.is_favorite) {
                    favoriteIcon?.classList.remove('hidden');
                    notFavoriteIcon?.classList.add('hidden');
                } else {
                    favoriteIcon?.classList.add('hidden');
                    notFavoriteIcon?.classList.remove('hidden');
                }
                
                this.showNotification(
                    data.data.is_favorite ? 'Added to favorites' : 'Removed from favorites',
                    'success'
                );
            } else {
                throw new Error(data.error || 'Failed to toggle favorite');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            this.showNotification('Error updating favorite status', 'error');
        }
    }
    
    async incrementPlayCount(songId) {
        try {
            await fetch(`/api/audio-library/${songId}/play`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error incrementing play count:', error);
        }
    }
    
    updateFilters() {
        this.currentFilters = {};
        
        if (this.elements.genreFilter && this.elements.genreFilter.value) {
            this.currentFilters.genre = this.elements.genreFilter.value;
        }
        
        if (this.elements.sourceFilter && this.elements.sourceFilter.value) {
            this.currentFilters.source_type = this.elements.sourceFilter.value;
        }
        
        this.currentPage = 1;
        this.loadLibrary();
    }
    
    toggleFavoritesFilter() {
        if (this.currentFilters.is_favorite) {
            delete this.currentFilters.is_favorite;
            this.elements.favoritesFilter.classList.remove('bg-red-700');
            this.elements.favoritesFilter.classList.add('bg-red-600');
        } else {
            this.currentFilters.is_favorite = true;
            this.elements.favoritesFilter.classList.remove('bg-red-600');
            this.elements.favoritesFilter.classList.add('bg-red-700');
        }
        
        this.currentPage = 1;
        this.loadLibrary();
    }
    
    renderPagination(pagination) {
        if (!this.elements.pagination) return;
        
        const { page, total_pages, has_next, has_prev } = pagination;
        this.totalPages = total_pages;
        
        // Update previous/next buttons
        if (this.elements.pagination.prevBtn) {
            this.elements.pagination.prevBtn.disabled = !has_prev;
        }
        
        if (this.elements.pagination.nextBtn) {
            this.elements.pagination.nextBtn.disabled = !has_next;
        }
        
        // Render page numbers (show max 5 pages)
        if (this.elements.pagination.pageNumbers) {
            this.elements.pagination.pageNumbers.innerHTML = '';
            
            const startPage = Math.max(1, page - 2);
            const endPage = Math.min(total_pages, page + 2);
            
            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('button');
                const isActive = i === page;
                pageBtn.className = isActive
                    ? 'px-3 py-2 text-sm font-medium rounded-lg bg-primary text-white'
                    : 'px-3 py-2 text-sm font-medium rounded-lg text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800';
                pageBtn.textContent = i;
                pageBtn.addEventListener('click', () => this.goToPage(i));
                this.elements.pagination.pageNumbers.appendChild(pageBtn);
            }
        }
        
        // Show/hide pagination
        if (total_pages > 1) {
            this.elements.pagination.container.classList.remove('hidden');
        } else {
            this.elements.pagination.container.classList.add('hidden');
        }
    }
    
    goToPage(page) {
        if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
            this.currentPage = page;
            this.loadLibrary();
            
            // Scroll to top of library
            this.elements.container?.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.goToPage(this.currentPage - 1);
        }
    }
    
    goToNextPage() {
        if (this.currentPage < this.totalPages) {
            this.goToPage(this.currentPage + 1);
        }
    }
    
    updateStats(stats) {
        if (this.elements.statsTotal) {
            this.elements.statsTotal.textContent = stats.total_count || 0;
        }
        
        if (this.elements.statsFavorites) {
            this.elements.statsFavorites.textContent = stats.favorite_count || 0;
        }
        
        if (this.elements.statsRecent) {
            this.elements.statsRecent.textContent = stats.recent_additions || 0;
        }
        
        if (this.elements.statsPlaylists) {
            // This would need to be loaded separately
            this.elements.statsPlaylists.textContent = '0'; // Placeholder
        }
    }
    
    refreshLibrary() {
        clearTimeout(this.refreshDebounceTimer);
        this.refreshDebounceTimer = setTimeout(() => {
            this.currentPage = 1;
            this.loadLibrary();
        }, 500);
    }
    
    showYourPlaylistsModal() {
        console.log('showYourPlaylistsModal called');
        
        // Prevent multiple modals
        if (document.getElementById('yourPlaylistsModal')) {
            return;
        }

        // Create modal container
        const modal = document.createElement('div');
        modal.id = 'yourPlaylistsModal';
        modal.className = 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4';
        modal.style.opacity = '0';
        modal.style.transition = 'opacity 0.2s ease-out';
        
        modal.innerHTML = `
            <div class="bg-white dark:bg-surface-dark rounded-xl shadow-2xl border border-slate-200 dark:border-border-dark w-full max-w-2xl transform transition-all scale-95 duration-200 h-[80vh] flex flex-col">
                <!-- Modal Header -->
                <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-border-dark flex-shrink-0">
                    <div class="flex items-center gap-3">
                        <div class="p-2 bg-primary/10 rounded-lg">
                            <span class="material-symbols-outlined text-primary">queue_music</span>
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Your Playlists</h3>
                            <p class="text-sm text-slate-500 dark:text-slate-400">Manage your music collections</p>
                        </div>
                    </div>
                    <button class="playlist-modal-close-btn p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close modal">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                
                <!-- Modal Body (Scrollable) -->
                <div class="flex-1 overflow-y-auto p-6 custom-scrollbar" id="yourPlaylistsContainer">
                    <!-- Loading State -->
                    <div id="yourPlaylistsLoading" class="flex flex-col items-center justify-center h-full py-12">
                        <span class="material-symbols-outlined animate-spin text-4xl text-primary mb-4">sync</span>
                        <p class="text-slate-500 dark:text-slate-400">Loading your playlists...</p>
                    </div>
                    
                    <!-- Content will be injected here -->
                    <div id="yourPlaylistsContent" class="hidden grid grid-cols-1 sm:grid-cols-2 gap-4"></div>
                    
                    <!-- Empty State -->
                    <div id="yourPlaylistsEmpty" class="hidden flex flex-col items-center justify-center h-full py-12">
                        <span class="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">playlist_remove</span>
                        <h4 class="text-lg font-medium text-slate-700 dark:text-slate-300">No playlists found</h4>
                        <p class="text-slate-500 dark:text-slate-400 text-center max-w-xs mb-6">You haven't created any playlists yet.</p>
                        <button id="yourPlaylistsCreateBtn" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">add</span>
                            Create New Playlist
                        </button>
                    </div>

                     <!-- Error State -->
                    <div id="yourPlaylistsError" class="hidden flex flex-col items-center justify-center h-full py-12">
                        <span class="material-symbols-outlined text-6xl text-red-300 dark:text-red-900/50 mb-4">error</span>
                        <h4 class="text-lg font-medium text-slate-700 dark:text-slate-300">Failed to load playlists</h4>
                        <p class="text-slate-500 dark:text-slate-400 text-center max-w-xs mb-6" id="yourPlaylistsErrorMessage">An unknown error occurred.</p>
                         <button id="yourPlaylistsRetryBtn" class="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">refresh</span>
                            Try Again
                        </button>
                    </div>
                </div>
                
                <!-- Modal Footer -->
                <div class="flex items-center justify-end gap-3 p-6 border-t border-slate-200 dark:border-border-dark flex-shrink-0">
                    <button class="playlist-modal-close-btn px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Event Listeners
        const closeBtns = modal.querySelectorAll('.playlist-modal-close-btn');
        const createBtn = modal.querySelector('#yourPlaylistsCreateBtn');
        const retryBtn = modal.querySelector('#yourPlaylistsRetryBtn');
        const contentContainer = modal.querySelector('#yourPlaylistsContent');
        
        const closeModal = () => {
             modal.style.opacity = '0';
            modal.querySelector('.bg-white').style.transform = 'scale(0.95)';
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
            }, 200);
        };
        
        closeBtns.forEach(btn => btn.addEventListener('click', closeModal));
        
         // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Playlist click delegation
        if (contentContainer) {
            contentContainer.addEventListener('click', (e) => {
                const playlistCard = e.target.closest('[data-playlist-id]');
                if (playlistCard) {
                    // Check if a button was clicked
                    const btn = e.target.closest('button');
                    if (btn) {
                        // Handle delete button
                        if (btn.classList.contains('delete-playlist-btn')) {
                            const playlistId = btn.getAttribute('data-id');
                            const playlistName = btn.getAttribute('data-name');
                            this.showDeletePlaylistConfirmation(playlistId, playlistName);
                        }
                        // Stop propagation for any button
                        return;
                    }

                    const playlistId = playlistCard.getAttribute('data-playlist-id');
                    this.handlePlaylistClick(playlistId);
                }
            });
        }
        
        // Listen for playlist updates to keep UI in sync
        const updateListener = (e) => {
            if (document.body.contains(modal)) {
                this.loadPlaylistsInModal(modal);
            } else {
                document.removeEventListener('playlistsUpdated', updateListener);
                document.removeEventListener('songAddedToPlaylist', updateListener);
            }
        };

        document.addEventListener('playlistsUpdated', updateListener);
        document.addEventListener('songAddedToPlaylist', updateListener);
        
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                closeModal();
                this.showCreatePlaylistModal();
            });
        }
        
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.loadPlaylistsInModal(modal));
        }

        // Animate modal entrance
        requestAnimationFrame(() => {
            modal.style.opacity = '1';
            modal.querySelector('.bg-white').style.transform = 'scale(1)';
        });
        
        // Load content
        this.loadPlaylistsInModal(modal);
    }

    async loadPlaylistsInModal(modal) {
        const loadingState = modal.querySelector('#yourPlaylistsLoading');
        const contentState = modal.querySelector('#yourPlaylistsContent');
        const emptyState = modal.querySelector('#yourPlaylistsEmpty');
        const errorState = modal.querySelector('#yourPlaylistsError');
        const errorMessage = modal.querySelector('#yourPlaylistsErrorMessage');
        
        // Reset states
        loadingState.classList.remove('hidden');
        contentState.classList.add('hidden');
        emptyState.classList.add('hidden');
        errorState.classList.add('hidden');
        
        try {
            const playlists = await this.loadUserPlaylists();
            
            loadingState.classList.add('hidden');
            
            if (playlists.length === 0) {
                emptyState.classList.remove('hidden');
            } else {
                contentState.classList.remove('hidden');
                this.renderPlaylistsInModal(contentState, playlists);
            }
        } catch (error) {
            loadingState.classList.add('hidden');
            errorState.classList.remove('hidden');
            if (errorMessage) errorMessage.textContent = error.message;
        }
    }

    renderPlaylistsInModal(container, playlists) {
        container.innerHTML = playlists.map(playlist => {
            // Calculate song count robustly checking multiple possible property names
            const songCount = playlist.song_count !== undefined ? playlist.song_count :
                             (playlist.audio_count !== undefined ? playlist.audio_count :
                             (playlist.tracks ? playlist.tracks.length :
                             (playlist.songs ? playlist.songs.length : 0)));
            
            return `
            <div class="group relative bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-all cursor-pointer" data-playlist-id="${playlist.id}" data-playlist-name="${playlist.name}">
                <div class="flex items-start gap-4">
                     <div class="w-16 h-16 rounded-lg bg-gradient-to-br from-primary/20 to-purple-600/20 flex items-center justify-center flex-shrink-0">
                        <span class="material-symbols-outlined text-primary text-2xl">queue_music</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="text-base font-bold text-slate-900 dark:text-white truncate mb-1">${playlist.name}</h4>
                         <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-2">${playlist.description || 'No description'}</p>
                         <div class="flex items-center gap-2 text-xs text-slate-400">
                            <span class="flex items-center gap-1">
                                <span class="material-symbols-outlined text-[10px]">music_note</span>
                                <span class="song-count-display">${songCount}</span> songs
                            </span>
                            <span>•</span>
                            <span>${this.formatUploadDate(playlist.created_at)}</span>
                         </div>
                    </div>
                </div>
                 <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                    <button class="p-1.5 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors" title="Edit Playlist" onclick="event.stopPropagation();">
                         <span class="material-symbols-outlined text-sm">edit</span>
                    </button>
                    <button class="delete-playlist-btn p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors" title="Delete Playlist" data-id="${playlist.id}" data-name="${playlist.name}">
                         <span class="material-symbols-outlined text-sm">delete</span>
                    </button>
                 </div>
            </div>
        `}).join('');
    }

    handlePlaylistClick(playlistId) {
        // Get playlist name for UI
        const card = document.querySelector(`[data-playlist-id="${playlistId}"]`);
        const playlistName = card ? card.getAttribute('data-playlist-name') : 'Playlist';
        
        console.log('Opening playlist:', playlistId, playlistName);
        
        // Visual feedback
        if (card) {
            card.classList.add('ring-2', 'ring-primary', 'ring-offset-2', 'dark:ring-offset-surface-dark');
        }
        
        this.showNotification(`Opening "${playlistName}"...`, 'info');
        
        // Close the modal
        const modal = document.getElementById('yourPlaylistsModal');
        if (modal) {
            modal.style.opacity = '0';
            // Wait for transition then remove
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
            }, 200);
        }

        // Switch to Song Library tab if not active
        const songTabBtn = document.getElementById('songLibraryTabBtn');
        if (songTabBtn && !songTabBtn.classList.contains('active')) {
            songTabBtn.click();
        }

        // Update filters to load specific playlist
        this.currentFilters = { playlist_id: playlistId };
        this.currentSearch = ''; // Clear search to ensure we see the playlist content
        this.currentPage = 1;
        
        // Update UI Header to show context
        const header = document.querySelector('#song-library-content h2');
        const subheader = document.querySelector('#song-library-content p');
        
        if (header) {
            // Save original content if needed, or just overwrite
            if (!this.originalHeaderContent) this.originalHeaderContent = header.innerHTML;
            
            header.innerHTML = `
                <div class="flex items-center gap-3">
                    <button onclick="window.songLibrary.clearPlaylistFilter()" class="p-1 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors" title="Back to Library">
                        <span class="material-symbols-outlined">arrow_back</span>
                    </button>
                    <span>${playlistName}</span>
                </div>
            `;
        }
        
        if (subheader) {
            if (!this.originalSubheaderContent) this.originalSubheaderContent = subheader.textContent;
            subheader.textContent = 'Playlist Details';
        }

        // Trigger load
        this.loadLibrary();
    }

    clearPlaylistFilter() {
        this.currentFilters = {};
        
        // Restore header
        const header = document.querySelector('#song-library-content h2');
        const subheader = document.querySelector('#song-library-content p');
        
        if (header && this.originalHeaderContent) {
            header.innerHTML = this.originalHeaderContent;
        }
        
        if (subheader && this.originalSubheaderContent) {
            subheader.textContent = this.originalSubheaderContent;
        }

        // Check for other filters from DOM
        this.updateFilters();
    }

    showCreatePlaylistModal() {
        const template = document.getElementById('createPlaylistModalTemplate');
        const modal = template.content.cloneNode(true);
        
        document.body.appendChild(modal);
        
        // Set up modal event listeners
        const modalElement = document.getElementById('playlistModal');
        const closeBtn = modalElement.querySelector('.playlist-modal-close-btn');
        const cancelBtn = modalElement.querySelector('.playlist-modal-cancel-btn');
        const createBtn = modalElement.querySelector('.playlist-modal-create-btn');
        const nameInput = modalElement.querySelector('#playlistNameInput');
        const descriptionInput = modalElement.querySelector('#playlistDescriptionInput');
        const playlistTypeRadios = modalElement.querySelectorAll('input[name="playlistType"]');
        const smartOptions = modalElement.querySelector('#smartPlaylistOptions');
        const promptInput = modalElement.querySelector('#playlistPromptInput');
        
        const closeModal = () => {
            modalElement.remove();
        };
        
        closeBtn?.addEventListener('click', closeModal);
        cancelBtn?.addEventListener('click', closeModal);

        // Toggle smart options visibility
        playlistTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'prompt') {
                    smartOptions.classList.remove('hidden');
                    promptInput.focus();
                } else {
                    smartOptions.classList.add('hidden');
                }
            });
        });
        
        createBtn?.addEventListener('click', async () => {
            const name = nameInput.value.trim();
            const description = descriptionInput.value.trim();
            const generationType = Array.from(playlistTypeRadios).find(r => r.checked)?.value || 'manual';
            const generationPrompt = promptInput?.value.trim();
            
            if (!name) {
                this.showNotification('Please enter a playlist name', 'error');
                return;
            }

            if (generationType === 'prompt' && !generationPrompt) {
                this.showNotification('Please enter a generation prompt', 'error');
                promptInput.focus();
                return;
            }
            
            try {
                // Prepare payload
                const payload = {
                    name,
                    description,
                    generation_type: generationType
                };

                if (generationType === 'prompt') {
                    payload.generation_prompt = generationPrompt;
                }

                // Use the /api/playlists endpoint which supports smart generation
                const response = await fetch('/api/playlists', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    const msg = generationType === 'prompt'
                        ? 'Smart Playlist creation started! Tracks will appear shortly.'
                        : 'Playlist created successfully!';
                    this.showNotification(msg, 'success');
                    closeModal();
                    
                    // Refresh playlists list if we are in "Your Playlists" view
                    // Or if we are in the library, we might want to refresh.
                    // But currently this is just creating it.
                    // If we want to show it immediately, we might need to navigate or reload.
                    // For now, let's trigger the event.
                    document.dispatchEvent(new CustomEvent('playlistsUpdated'));

                } else {
                    throw new Error(data.error || 'Failed to create playlist');
                }
            } catch (error) {
                console.error('Error creating playlist:', error);
                this.showNotification('Error creating playlist: ' + error.message, 'error');
            }
        });
        
        // Focus name input initially
        nameInput?.focus();
    }
    
    showAddToPlaylistModal(song) {
        // Check if AddButton is available
        if (typeof AddButton === 'undefined') {
            console.warn('AddButton component not loaded');
            
            // Try to load the AddButton script dynamically
            this.loadAddButtonScript().then(() => {
                // Retry after loading
                this.createAddToPlaylistModal(song);
            }).catch(() => {
                this.showNotification('Add to playlist feature is not available. Please refresh the page.', 'error');
            });
            return;
        }
        
        // Create modal for playlist selection and add operation
        this.createAddToPlaylistModal(song);
    }
    
    /**
     * Load AddButton script dynamically
     * @returns {Promise} Promise that resolves when script is loaded
     */
    loadAddButtonScript() {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (typeof AddButton !== 'undefined') {
                resolve();
                return;
            }
            
            // Check if script is already being loaded
            if (document.querySelector('script[src*="addButton.js"]')) {
                const checkLoaded = setInterval(() => {
                    if (typeof AddButton !== 'undefined') {
                        clearInterval(checkLoaded);
                        resolve();
                    }
                }, 100);
                
                // Timeout after 10 seconds
                setTimeout(() => {
                    clearInterval(checkLoaded);
                    reject(new Error('Timeout loading AddButton script'));
                }, 10000);
                return;
            }
            
            // Create and load script
            const script = document.createElement('script');
            script.src = '/static/js/components/addButton.js?v=2';
            script.onload = () => {
                console.log('AddButton script loaded successfully');
                resolve();
            };
            script.onerror = () => {
                console.error('Failed to load AddButton script');
                reject(new Error('Failed to load AddButton script'));
            };
            document.head.appendChild(script);
        });
    }
    
    /**
     * Create modal for adding song to playlist
     * @param {Object} song - Song data
     */
    createAddToPlaylistModal(song) {
        // Get user playlists
        this.loadUserPlaylists().then(playlists => {
            this.showPlaylistSelectionModal(song, playlists);
        }).catch(error => {
            console.error('Error loading playlists:', error);
            this.showNotification('Failed to load playlists', 'error');
        });
    }
    
    /**
     * Show playlist selection modal with AddButton integration
     * @param {Object} song - Song data
     * @param {Array} playlists - Array of playlists
     */
    showPlaylistSelectionModal(song, playlists) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-surface-dark rounded-xl shadow-2xl border border-slate-200 dark:border-border-dark w-full max-w-md transform transition-all">
                <!-- Modal Header -->
                <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-border-dark">
                    <div class="flex items-center gap-3">
                        <div class="p-2 bg-primary/10 rounded-lg">
                            <span class="material-symbols-outlined text-primary">playlist_add</span>
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Add to Playlist</h3>
                            <p class="text-sm text-slate-500 dark:text-slate-400">"${song.title}" by ${song.artist}</p>
                        </div>
                    </div>
                    <button class="playlist-modal-close-btn p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close modal">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                
                <!-- Modal Body -->
                <div class="p-6">
                    <div class="mb-6">
                        <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                            <span class="material-symbols-outlined text-sm mr-1">library_music</span>
                            Select Playlist
                        </label>
                        <div class="relative">
                            <select id="playlistSelect" class="w-full p-3 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all appearance-none cursor-pointer">
                                <option value="">Choose a playlist...</option>
                                ${playlists.map(playlist => {
                                    const songCount = playlist.song_count !== undefined ? playlist.song_count :
                                                     (playlist.audio_count !== undefined ? playlist.audio_count :
                                                     (playlist.tracks ? playlist.tracks.length :
                                                     (playlist.songs ? playlist.songs.length : 0)));
                                    return `<option value="${playlist.id}" data-song-count="${songCount}">${playlist.name} (${songCount} songs)</option>`;
                                }).join('')}
                            </select>
                            <div class="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                                <span class="material-symbols-outlined text-slate-400">expand_more</span>
                            </div>
                        </div>
                    </div>
                    
                    <div id="addButtonContainer" class="mb-6">
                        <!-- AddButton will be inserted here -->
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-border-dark">
                        <button id="createNewPlaylistBtn" class="text-sm text-primary hover:text-primary-dark font-medium flex items-center gap-1 transition-colors">
                            <span class="material-symbols-outlined text-sm">add</span>
                            Create New Playlist
                        </button>
                        <div class="text-xs text-slate-500 dark:text-slate-400" id="playlistInfo">
                            ${playlists.length} playlist${playlists.length !== 1 ? 's' : ''} available
                        </div>
                    </div>
                </div>
                
                <!-- Modal Footer -->
                <div class="flex items-center justify-end gap-3 p-6 border-t border-slate-200 dark:border-border-dark">
                    <button id="cancelBtn" class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Set up event listeners
        const playlistSelect = modal.querySelector('#playlistSelect');
        const addButtonContainer = modal.querySelector('#addButtonContainer');
        const cancelBtn = modal.querySelector('#cancelBtn');
        const closeBtn = modal.querySelector('.playlist-modal-close-btn');
        const createNewPlaylistBtn = modal.querySelector('#createNewPlaylistBtn');
        
        const closeModal = () => {
            modal.style.opacity = '0';
            modal.querySelector('.bg-white').style.transform = 'scale(0.95)';
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
            }, 150);
        };
        
        cancelBtn?.addEventListener('click', closeModal);
        closeBtn?.addEventListener('click', closeModal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Create new playlist handler
        createNewPlaylistBtn?.addEventListener('click', () => {
            closeModal();
            this.showCreatePlaylistModal();
        });
        
        // Handle playlist selection
        playlistSelect?.addEventListener('change', () => {
            const selectedPlaylistId = playlistSelect.value;
            
            // Clear previous AddButton
            addButtonContainer.innerHTML = '';
            
            if (selectedPlaylistId) {
                // Create AddButton for selected playlist
                this.createAddButtonForPlaylist(
                    addButtonContainer, 
                    selectedPlaylistId, 
                    song
                );
            }
        });
        
        // Animate modal entrance
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.querySelector('.bg-white').style.transform = 'scale(1)';
        }, 10);
        
        // Focus playlist select
        setTimeout(() => {
            playlistSelect?.focus();
        }, 200);
    }
    
    /**
     * Create AddButton for specific playlist
     * @param {HTMLElement} container - Container element
     * @param {string} playlistId - Playlist ID
     * @param {Object} song - Song data
     */
    createAddButtonForPlaylist(container, playlistId, song) {
        try {
            // Convert song format for AddButton
            const songData = {
                id: song.id,
                title: song.title,
                artist: song.artist,
                duration: song.duration,
                genre: song.genre,
                album: song.album,
                audio_url: song.audio_url,
                ...song
            };
            
            // Create AddButton instance with enhanced configuration
            const addButton = new AddButton({
                playlistId: playlistId,
                songData: songData,
                variant: 'primary',
                size: 'large',
                showTooltip: true,
                showIcon: true,
                enableValidation: true,
                enableOptimisticUpdates: true,
                enableMockMode: false, // Ensure mock mode is disabled in production
                ariaLabel: `Add "${song.title}" to playlist`,
                tooltipText: 'Add to playlist',
                onSuccess: (response, songData, playlistId) => {
                    this.handleAddToPlaylistSuccess(response, songData, playlistId);
                    this.closePlaylistModal();
                },
                onError: (error, songData, playlistId) => {
                    this.handleAddToPlaylistError(error, songData, playlistId);
                },
                onStateChange: (state) => {
                    // Update modal UI based on AddButton state
                    this.updateModalUI(state);
                },
                onClick: (event, songData, playlistId) => {
                    // Custom click handler for additional validation
                    console.log('Add button clicked for:', songData.title);
                    return true; // Allow the operation to proceed
                },
                onShowNotification: (message, type) => this.showNotification(message, type)
            });
            
            // Create and append button element
            const buttonElement = addButton.createElement();
            container.appendChild(buttonElement);
            
            // Add success state change listener
            buttonElement.addEventListener('addButton:success', (event) => {
                console.log('AddButton success event:', event.detail);
            });
            
            // Add error state change listener
            buttonElement.addEventListener('addButton:error', (event) => {
                console.log('AddButton error event:', event.detail);
            });
            
            // Store reference for cleanup
            this.currentAddButton = addButton;
            
        } catch (error) {
            console.error('Error creating AddButton:', error);
            container.innerHTML = `
                <div class="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <span class="material-symbols-outlined text-red-500">error</span>
                    <span class="text-sm text-red-700 dark:text-red-400">Failed to create add button</span>
                </div>
            `;
        }
    }
    
    /**
     * Load user playlists
     * @returns {Promise<Array>} Array of playlists
     */
    async loadUserPlaylists() {
        try {
            const response = await fetch('/api/audio-library/playlists');
            const data = await response.json();
            
            if (response.ok && data.success) {
                return data.data.playlists || [];
            } else {
                throw new Error(data.error || 'Failed to load playlists');
            }
        } catch (error) {
            console.error('Error loading playlists:', error);
            throw error;
        }
    }
    
    /**
     * Handle successful add to playlist
     * @param {Object} response - API response
     * @param {Object} songData - Song data
     * @param {string} playlistId - Playlist ID
     */
    handleAddToPlaylistSuccess(response, songData, playlistId) {
        console.log('Song added to playlist successfully:', response);
        
        this.showNotification(
            `Added "${songData.title}" to playlist successfully!`, 
            'success'
        );
        
        // Refresh playlist data if needed
        this.refreshPlaylistData(playlistId);
        
        // Emit custom event for other components
        document.dispatchEvent(new CustomEvent('songAddedToPlaylist', {
            detail: { songData, playlistId, response }
        }));
        
        // Track analytics if available
        if (typeof gtag !== 'undefined') {
            gtag('event', 'add_to_playlist', {
                event_category: 'music',
                event_label: songData.title,
                value: 1
            });
        }
    }
    
    /**
     * Handle failed add to playlist
     * @param {Error} error - Error object
     * @param {Object} songData - Song data
     * @param {string} playlistId - Playlist ID
     */
    handleAddToPlaylistError(error, songData, playlistId) {
        console.error('Failed to add song to playlist:', error);
        
        let message = 'Failed to add song to playlist';
        let icon = 'error';
        
        if (error.message.includes('already in playlist')) {
            message = 'Song is already in this playlist';
            icon = 'info';
        } else if (error.message.includes('permission') || error.message.includes('unauthorized')) {
            message = 'You do not have permission to add songs to this playlist';
            icon = 'warning';
        } else if (error.message.includes('not found')) {
            message = 'Playlist not found';
            icon = 'error';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
            message = 'Network error. Please check your connection and try again.';
            icon = 'wifi_off';
        } else if (error.message.includes('quota') || error.message.includes('limit')) {
            message = 'Storage limit reached. Cannot add more songs to this playlist.';
            icon = 'storage';
        }
        
        this.showNotification(message, icon);
        
        // Track error analytics if available
        if (typeof gtag !== 'undefined') {
            gtag('event', 'add_to_playlist_error', {
                event_category: 'music',
                event_label: songData.title,
                error_message: error.message
            });
        }
    }
    
    /**
     * Update modal UI based on AddButton state
     * @param {Object} state - AddButton state
     */
    updateModalUI(state) {
        const modal = document.querySelector('.fixed.inset-0');
        if (!modal) return;
        
        const playlistSelect = modal.querySelector('#playlistSelect');
        const addButton = modal.querySelector('.add-button');
        
        if (playlistSelect) {
            playlistSelect.disabled = state.isLoading || state.isSuccess;
        }
        
        if (addButton) {
            addButton.className = `add-button ${this.getAddButtonClasses(state)}`;
        }
    }
    
    /**
     * Get CSS classes for AddButton based on state
     * @param {Object} state - AddButton state
     * @returns {string} CSS classes
     */
    getAddButtonClasses(state) {
        const classes = ['btn-primary'];
        
        if (state.isLoading) {
            classes.push('btn-loading');
        } else if (state.isSuccess) {
            classes.push('btn-success');
        } else if (state.isError) {
            classes.push('btn-error');
        }
        
        return classes.join(' ');
    }
    
    /**
     * Close playlist modal
     */
    closePlaylistModal() {
        const modal = document.querySelector('.fixed.inset-0');
        if (modal) {
            document.body.removeChild(modal);
        }
    }
    
    /**
     * Refresh playlist data
     * @param {string} playlistId - Specific playlist ID to refresh
     */
    async refreshPlaylistData(playlistId = null) {
        try {
            // Refresh user's playlists
            const playlists = await this.loadUserPlaylists();
            
            // Update any AddButtonCards with new playlist data
            document.dispatchEvent(new CustomEvent('playlistsUpdated', {
                detail: { playlists, playlistId }
            }));
            
        } catch (error) {
            console.warn('Failed to refresh playlist data:', error);
        }
    }
    
    showSongMenu(song, button) {
        // Remove any existing menus
        this.closeActiveMenu();

        // Create menu container
        const menu = document.createElement('div');
        menu.className = 'fixed z-[60] bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-1 min-w-[180px] animate-slide-in';
        menu.id = 'active-song-menu';
        
        // Position menu
        const rect = button.getBoundingClientRect();
        
        // Calculate position (align top-right of menu with bottom-right of button)
        let top = rect.bottom + 5;
        let left = rect.right - 180; // Default width alignment
        
        // Ensure it fits within viewport
        if (left < 10) left = 10;
        if (top + 100 > window.innerHeight) top = rect.top - 60; // Flip up if near bottom
        
        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;

        // Check if we are in a playlist view
        const isInPlaylist = !!this.currentFilters.playlist_id;
        const canRetryLyricsExtraction = this.canRetryLyricsExtraction(song);

        // Menu items
        menu.innerHTML = `
            <button class="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex items-center gap-3 transition-colors" data-action="add-to-playlist">
                <span class="material-symbols-outlined text-[20px]">playlist_add</span>
                <span class="font-medium">Add to Playlist</span>
            </button>
            ${canRetryLyricsExtraction ? `
            <button class="w-full text-left px-4 py-2.5 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 flex items-center gap-3 transition-colors" data-action="retry-lyrics-extraction">
                <span class="material-symbols-outlined text-[20px]">lyrics</span>
                <span class="font-medium">Retry Lyrics Extraction</span>
            </button>
            ` : ''}
            <div class="h-px bg-slate-100 dark:bg-slate-700 my-1"></div>
            ${isInPlaylist ? `
            <button class="w-full text-left px-4 py-2.5 text-sm text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 flex items-center gap-3 transition-colors" data-action="remove-from-playlist">
                <span class="material-symbols-outlined text-[20px]">playlist_remove</span>
                <span class="font-medium">Remove from Playlist</span>
            </button>
            ` : `
            <button class="w-full text-left px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors" data-action="delete">
                <span class="material-symbols-outlined text-[20px]">delete</span>
                <span class="font-medium">Delete Song</span>
            </button>
            `}
        `;

        // Append to body to ensure z-index works correctly
        document.body.appendChild(menu);
        
        // Event listeners
        const addToPlaylistBtn = menu.querySelector('[data-action="add-to-playlist"]');
        if (addToPlaylistBtn) {
            addToPlaylistBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeActiveMenu();
                this.showAddToPlaylistModal(song);
            });
        }

        const deleteBtn = menu.querySelector('[data-action="delete"]');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeActiveMenu();
                this.showDeleteConfirmation(song);
            });
        }

        const removeFromPlaylistBtn = menu.querySelector('[data-action="remove-from-playlist"]');
        if (removeFromPlaylistBtn) {
            removeFromPlaylistBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeActiveMenu();
                this.showRemoveFromPlaylistConfirmation(song);
            });
        }

        const retryLyricsBtn = menu.querySelector('[data-action="retry-lyrics-extraction"]');
        if (retryLyricsBtn) {
            retryLyricsBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                this.closeActiveMenu();
                await this.retryLyricsExtraction(song);
            });
        }

        // Close when clicking outside
        // Delay slightly to prevent the click that opened it from closing it immediately
        setTimeout(() => {
            const closeHandler = (e) => {
                if (!menu.contains(e.target) && e.target !== button && !button.contains(e.target)) {
                    this.closeActiveMenu();
                }
            };
            document.addEventListener('click', closeHandler);
            this.activeMenuCloseHandler = closeHandler;
        }, 10);
        
        this.activeMenu = menu;
    }

    canRetryLyricsExtraction(song) {
        if (!song || song.source_type !== 'upload' || !song.id) {
            return false;
        }

        const status = song.lyrics_extraction_status;
        return status === 'failed' || status === 'not_requested';
    }

    async retryLyricsExtraction(song) {
        if (!song?.id) {
            this.showNotification('Audio item not found', 'error');
            return;
        }

        this.showNotification(`Retrying lyrics extraction for "${song.title || 'song'}"...`, 'info');

        try {
            const response = await fetch(`/api/audio-library/${song.id}/lyrics-retry`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to queue lyrics extraction retry');
            }

            this.showNotification('Lyrics extraction retry queued', 'success');
            this.startLyricsStatusPolling(song.id);
            this.refreshLibrary();

        } catch (error) {
            console.error('Error retrying lyrics extraction:', error);
            this.showNotification(`Error retrying lyrics extraction: ${error.message}`, 'error');
        }
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

    showRemoveFromPlaylistConfirmation(song) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 w-full max-w-md transform transition-all scale-100 p-6 animate-slide-in">
                <div class="flex items-center gap-4 mb-4">
                    <div class="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-full flex-shrink-0">
                        <span class="material-symbols-outlined text-amber-600 dark:text-amber-400 text-2xl">playlist_remove</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-slate-900 dark:text-white">Remove from Playlist?</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Song will remain in your library</p>
                    </div>
                </div>
                
                <p class="text-slate-600 dark:text-slate-300 mb-6 bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                    Are you sure you want to remove <span class="font-bold text-slate-900 dark:text-white">"${song.title || 'Untitled'}"</span> from this playlist?
                </p>
                
                <div class="flex items-center justify-end gap-3">
                    <button class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" id="cancelRemoveBtn">
                        Cancel
                    </button>
                    <button class="px-4 py-2 text-sm font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors flex items-center gap-2 shadow-sm hover:shadow" id="confirmRemoveBtn">
                        <span class="material-symbols-outlined text-sm">playlist_remove</span>
                        Remove
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const cancelBtn = modal.querySelector('#cancelRemoveBtn');
        const confirmBtn = modal.querySelector('#confirmRemoveBtn');
        
        const closeModal = () => {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 200);
        };
        
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
        
        confirmBtn.addEventListener('click', () => {
            closeModal();
            this.removeSongFromPlaylist(song);
        });
        
        // Focus cancel button for accessibility
        cancelBtn.focus();
    }

    async removeSongFromPlaylist(song) {
        const playlistId = this.currentFilters.playlist_id;
        if (!playlistId) {
            this.showNotification('No active playlist', 'error');
            return;
        }

        // Show loading notification
        this.showNotification(`Removing "${song.title || 'song'}" from playlist...`, 'info');
        
        try {
            const response = await fetch(`/api/audio-library/playlists/${playlistId}/remove`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ audio_id: song.id })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Remove from DOM with animation
                const card = document.getElementById(`song-card-${song.id}`);
                if (card) {
                    card.style.transition = 'all 0.3s ease-out';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    card.style.height = card.offsetHeight + 'px'; // Fix height for smooth collapse
                    
                    setTimeout(() => {
                        card.style.marginBottom = '0';
                        card.style.height = '0';
                        card.style.paddingTop = '0';
                        card.style.paddingBottom = '0';
                        card.style.borderWidth = '0';
                        card.style.overflow = 'hidden';
                        
                        setTimeout(() => {
                            card.remove();
                            // Check if empty state needed
                            if (this.elements.container.children.length === 0) {
                                this.showEmptyState();
                            }
                            // Refresh Stats if needed (e.g. song count in header)
                            // Ideally we should decrement the count in the header
                            const countDisplay = document.querySelector('.song-count-display');
                            if (countDisplay) {
                                const current = parseInt(countDisplay.textContent);
                                if (!isNaN(current)) countDisplay.textContent = Math.max(0, current - 1);
                            }
                        }, 300);
                    }, 300);
                }
                
                this.showNotification('Song removed from playlist', 'success');
                
            } else {
                throw new Error(data.error || 'Failed to remove song');
            }
        } catch (error) {
            console.error('Error removing song:', error);
            this.showNotification(`Error removing song: ${error.message}`, 'error');
        }
    }

    showDeleteConfirmation(song) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 w-full max-w-md transform transition-all scale-100 p-6 animate-slide-in">
                <div class="flex items-center gap-4 mb-4">
                    <div class="p-3 bg-red-100 dark:bg-red-900/30 rounded-full flex-shrink-0">
                        <span class="material-symbols-outlined text-red-600 dark:text-red-400 text-2xl">delete_forever</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-slate-900 dark:text-white">Delete Song?</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">This action cannot be undone</p>
                    </div>
                </div>
                
                <p class="text-slate-600 dark:text-slate-300 mb-6 bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                    Are you sure you want to permanently delete <span class="font-bold text-slate-900 dark:text-white">"${song.title || 'Untitled'}"</span>?
                </p>
                
                <div class="flex items-center justify-end gap-3">
                    <button class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" id="cancelDeleteBtn">
                        Cancel
                    </button>
                    <button class="px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2 shadow-sm hover:shadow" id="confirmDeleteBtn">
                        <span class="material-symbols-outlined text-sm">delete</span>
                        Delete Forever
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const cancelBtn = modal.querySelector('#cancelDeleteBtn');
        const confirmBtn = modal.querySelector('#confirmDeleteBtn');
        
        const closeModal = () => {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 200);
        };
        
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
        
        confirmBtn.addEventListener('click', () => {
            closeModal();
            this.deleteSong(song);
        });
        
        // Focus cancel button for accessibility
        cancelBtn.focus();
    }

    async deleteSong(song) {
        // Show loading notification
        const notificationId = Date.now();
        this.showNotification(`Deleting "${song.title || 'song'}"...`, 'info');
        
        try {
            const response = await fetch(`/api/audio-library/${song.id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Remove from DOM with animation
                const card = document.getElementById(`song-card-${song.id}`);
                if (card) {
                    card.style.transition = 'all 0.3s ease-out';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    card.style.height = card.offsetHeight + 'px'; // Fix height for smooth collapse
                    
                    setTimeout(() => {
                        card.style.marginBottom = '0';
                        card.style.height = '0';
                        card.style.paddingTop = '0';
                        card.style.paddingBottom = '0';
                        card.style.borderWidth = '0';
                        card.style.overflow = 'hidden';
                        
                        setTimeout(() => {
                            card.remove();
                            // Check if empty state needed
                            if (this.elements.container.children.length === 0) {
                                this.showEmptyState();
                            }
                        }, 300);
                    }, 300);
                }
                
                this.showNotification('Song deleted successfully', 'success');
                
                // Update stats
                if (this.elements.statsTotal) {
                    const currentTotal = parseInt(this.elements.statsTotal.textContent);
                    if (!isNaN(currentTotal) && currentTotal > 0) {
                        this.elements.statsTotal.textContent = currentTotal - 1;
                    }
                }
                
            } else {
                throw new Error(data.error || 'Failed to delete song');
            }
        } catch (error) {
            console.error('Error deleting song:', error);
            this.showNotification(`Error deleting song: ${error.message}`, 'error');
        }
    }

    showDeletePlaylistConfirmation(playlistId, playlistName) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[110] p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 w-full max-w-md transform transition-all scale-100 p-6 animate-slide-in">
                <div class="flex items-center gap-4 mb-4">
                    <div class="p-3 bg-red-100 dark:bg-red-900/30 rounded-full flex-shrink-0">
                        <span class="material-symbols-outlined text-red-600 dark:text-red-400 text-2xl">delete_forever</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-slate-900 dark:text-white">Delete Playlist?</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">This action cannot be undone</p>
                    </div>
                </div>
                
                <p class="text-slate-600 dark:text-slate-300 mb-6 bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-700">
                    Are you sure you want to permanently delete the playlist <span class="font-bold text-slate-900 dark:text-white">"${playlistName}"</span>?
                </p>
                
                <div class="flex items-center justify-end gap-3">
                    <button class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" id="cancelPlaylistDeleteBtn">
                        Cancel
                    </button>
                    <button class="px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2 shadow-sm hover:shadow" id="confirmPlaylistDeleteBtn">
                        <span class="material-symbols-outlined text-sm">delete</span>
                        Delete Playlist
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const cancelBtn = modal.querySelector('#cancelPlaylistDeleteBtn');
        const confirmBtn = modal.querySelector('#confirmPlaylistDeleteBtn');
        
        const closeModal = () => {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 200);
        };
        
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
        
        confirmBtn.addEventListener('click', () => {
            closeModal();
            this.deletePlaylist(playlistId);
        });
        
        // Focus cancel button
        cancelBtn.focus();
    }

    async deletePlaylist(playlistId) {
        if (!playlistId) {
            this.showNotification('Invalid playlist ID', 'error');
            return;
        }

        this.showNotification('Deleting playlist...', 'info');
        
        try {
            // Use the dedicated playlists API endpoint which already supports DELETE
            const response = await fetch(`/api/playlists/${playlistId}`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                if (response.ok && data.success) {
                    this.showNotification('Playlist deleted successfully', 'success');
                    
                    // Refresh playlists in modal if open
                    const modal = document.getElementById('yourPlaylistsModal');
                    if (modal && document.body.contains(modal)) {
                        this.loadPlaylistsInModal(modal);
                    }
                    
                    // Also trigger generic update event
                    document.dispatchEvent(new CustomEvent('playlistsUpdated'));
                    
                } else {
                    throw new Error(data.error || 'Failed to delete playlist');
                }
            } else {
                // Handle non-JSON response (likely HTML error page)
                const text = await response.text();
                console.error('Non-JSON response from server:', text);
                throw new Error(`Server returned unexpected error (${response.status})`);
            }
        } catch (error) {
            console.error('Error deleting playlist:', error);
            this.showNotification(`Error deleting playlist: ${error.message}`, 'error');
        }
    }
    
    async downloadSong(song) {
        if (!song.audio_url) {
            this.showNotification('No audio URL available', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/download-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: song.audio_url,
                    filename: `${song.title || 'song'}.mp3`
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${song.title || 'song'}.mp3`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification('Download started!', 'success');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Error downloading song:', error);
            this.showNotification('Error downloading song', 'error');
        }
    }
    
    showEditModal(song) {
        // Placeholder for edit modal
        this.showNotification('Edit metadata feature coming soon!', 'info');
    }
    
    // Utility methods
    formatDuration(seconds) {
        if (!seconds) return '--:--';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    formatFileSize(bytes) {
        if (!bytes) return '--';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${Math.round(bytes / Math.pow(1024, i) * 10) / 10} ${sizes[i]}`;
    }
    
    formatUploadDate(dateString) {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return `${Math.floor(diffDays / 365)} years ago`;
    }
    
    showNotification(message, type = 'info', icon = null) {
        // Map notification types to default icons
        const typeIcons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info',
            wifi_off: 'wifi_off',
            storage: 'storage'
        };
        
        const finalIcon = icon || typeIcons[type] || 'info';
        
        // Use existing notification system if available
        if (typeof showSuccess === 'function' && type === 'success') {
            showSuccess(message);
        } else if (typeof showError === 'function' && (type === 'error' || type === 'warning')) {
            showError(message);
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg z-[110] max-w-md transform transition-all duration-300 translate-x-full`;
            
            const typeColors = {
                success: 'bg-green-500 text-white',
                error: 'bg-red-500 text-white',
                warning: 'bg-yellow-500 text-white',
                info: 'bg-blue-500 text-white',
                wifi_off: 'bg-gray-500 text-white',
                storage: 'bg-purple-500 text-white'
            };
            
            notification.className += ` ${typeColors[type] || typeColors.info}`;
            
            notification.innerHTML = `
                <div class="flex items-center">
                    <span class="material-symbols-outlined mr-2">${finalIcon}</span>
                    <span class="font-medium">${message}</span>
                    <button class="ml-auto text-white hover:text-gray-200 transition-colors" onclick="this.parentElement.parentElement.remove()">
                        <span class="material-symbols-outlined text-sm">close</span>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.classList.add('translate-x-full');
                    setTimeout(() => {
                        if (notification.parentElement) {
                            notification.remove();
                        }
                    }, 300);
                }
            }, 5000);
        }
    }
    
    // State management methods
    showLoadingState() {
        this.hideAllStates();
        this.elements.loadingState?.classList.remove('hidden');
    }
    
    showEmptyState() {
        this.hideAllStates();
        this.elements.emptyState?.classList.remove('hidden');
    }
    
    showErrorState(message) {
        this.hideAllStates();
        this.elements.errorState?.classList.remove('hidden');
        
        const errorMessageEl = this.elements.errorState?.querySelector('.error-message');
        if (errorMessageEl) {
            errorMessageEl.textContent = message;
        }
    }
    
    hideAllStates() {
        this.elements.loadingState?.classList.add('hidden');
        this.elements.emptyState?.classList.add('hidden');
        this.elements.errorState?.classList.add('hidden');
    }
}

// Make SongLibrary available globally
window.SongLibrary = SongLibrary;
