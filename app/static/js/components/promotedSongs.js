/**
 * PromotedSongs component for the Music Cover Generator application.
 * Populates the "Promoted Creator Songs" section with songs created by users.
 */

console.log('PromotedSongs script loaded');

class PromotedSongs {
    constructor() {
        this.songs = [];
        this.container = null;
        this.loadingState = null;
        this.emptyState = null;
        this.errorState = null;
        this.refreshBtn = null;
    }

    /**
     * Initialize the component with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.container = elements.container;
        this.loadingState = elements.loadingState;
        this.emptyState = elements.emptyState;
        this.errorState = elements.errorState;
        this.refreshBtn = elements.refreshBtn;

        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadSongs());
        }

        this.loadSongs();
    }

    /**
     * Load promoted songs from the API.
     */
    async loadSongs() {
        this.showLoading();

        try {
            // Fetch promoted songs from API
            // Using a query param or specific endpoint for promoted content
            const response = await fetch('/api/songs/promoted');
            
            if (!response.ok) {
                // Fallback to user activity if specific endpoint doesn't exist yet
                console.warn('Promoted songs endpoint not found, falling back to recent activity');
                await this.loadRecentSongs();
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                this.songs = data.data.songs || [];
                this.renderSongs();
                
                if (this.songs.length === 0) {
                    this.showEmpty();
                } else {
                    this.showContent();
                }
            } else {
                throw new Error(data.msg || 'Failed to load songs');
            }
        } catch (error) {
            console.error('Error loading promoted songs:', error);
            this.showError(error.message);
        }
    }

    /**
     * Load recent songs as fallback.
     */
    async loadRecentSongs() {
        try {
            const response = await fetch('/api/user-activity?type=generation&limit=6');
            const data = await response.json();
            
            if (response.ok && data.code === 200) {
                // Extract song data from activity
                this.songs = data.data.activities
                    .filter(activity => activity.data && activity.data.song)
                    .map(activity => activity.data.song);
                
                this.renderSongs();
                
                if (this.songs.length === 0) {
                    this.showEmpty();
                } else {
                    this.showContent();
                }
            } else {
                throw new Error(data.msg || 'Failed to load recent songs');
            }
        } catch (error) {
            console.error('Error loading recent songs:', error);
            this.showError(error.message);
        }
    }

    /**
     * Check if a song has an associated audio file.
     * @param {Object} song - Song data
     * @returns {boolean} True if song has audio, false otherwise
     */
    hasAudioFile(song) {
        return !!(song.audio_url || song.audio_urls?.generated || song.audio_urls?.source || song.stream_url);
    }

    /**
     * Render the list of songs, filtering out those without audio files.
     */
    renderSongs() {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        
        // Filter songs to only display those with audio files
        const songsWithAudio = this.songs.filter(song => this.hasAudioFile(song));
        
        // If no songs have audio, show empty state
        if (songsWithAudio.length === 0) {
            this.showEmpty();
            return;
        }
        
        songsWithAudio.forEach(song => {
            const card = this.createSongCard(song);
            this.container.appendChild(card);
        });
    }

    /**
     * Create a song card element.
     * Renders a card matching the design system with song data.
     * @param {Object} song - Song data
     * @returns {HTMLElement} Song card element
     */
    createSongCard(song) {
        const card = document.createElement('div');
        card.className = 'unified-card group relative p-3 rounded-2xl bg-white/[0.03] backdrop-blur-md neon-border-purple border border-white/5 overflow-hidden transition-transform hover:-translate-y-1 cursor-pointer';
        
        // Determine image source (try multiple possible property names)
        const imageUrl = song.cover_image_url || song.image_url || song.thumbnail || 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=300&fit=crop';
        
        // Extract creator/artist name
        const creator = song.creator_name || song.artist || song.username || 'Unknown Creator';
        
        // Extract title
        const title = song.title || song.name || 'Untitled Song';
        
        // Extract genre/style
        const genre = song.genre || song.style || 'Music';
        
        card.innerHTML = `
            <div class="relative aspect-video rounded-lg overflow-hidden mb-3 border border-white/5 h-48">
                <img src="${imageUrl}" alt="${title}" class="w-full h-full object-cover" onerror="this.src='https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=300&fit=crop'">
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            </div>
            <div class="px-2 pb-2">
                <h3 class="text-lg font-bold tracking-tight mb-1 text-white truncate">${title}</h3>
                <p class="text-white/50 text-sm leading-relaxed truncate">by ${creator}</p>
                <div class="flex items-center justify-between mt-3">
                    <span class="text-xs text-white/40 uppercase font-bold">${genre}</span>
                    <button class="px-2 py-1 rounded-full bg-primary-orange/20 text-primary-orange text-xs font-bold hover:bg-primary-orange/30 transition-colors play-song-btn">Play</button>
                </div>
            </div>
        `;
        
        // Add click handler to the Play button
        const playBtn = card.querySelector('.play-song-btn');
        if (playBtn) {
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.playSongInSticky(song);
            });
        }
        
        return card;
    }

    /**
     * Play a song in the sticky player at the bottom.
     * @param {Object} song - Song data to play
     */
    playSongInSticky(song) {
        // Get the audio URL from various possible properties
        const audioUrl = song.audio_url || song.audio_urls?.generated || song.audio_urls?.source || song.stream_url || '';
        
        if (!audioUrl) {
            console.error('No audio URL found for song:', song);
            alert('Cannot play this song - no audio available');
            return;
        }

        // Update sticky player elements
        const playerTitle = document.querySelector('[data-sticky-player-title]');
        const playerImage = document.querySelector('[data-sticky-player-image]');
        const audioElement = document.querySelector('[data-sticky-audio-element]');
        const playBtn = document.querySelector('[data-sticky-play-btn]');

        if (!audioElement) {
            console.error('Sticky player audio element not found');
            return;
        }

        // Update song information
        if (playerTitle) {
            playerTitle.textContent = song.title || song.name || 'Untitled Song';
        }

        if (playerImage) {
            const imageUrl = song.cover_image_url || song.image_url || song.thumbnail || 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=300&fit=crop';
            playerImage.src = imageUrl;
            playerImage.alt = song.title || 'Song cover';
        }

        // Update audio source and play
        audioElement.src = audioUrl;
        audioElement.play().catch(error => {
            console.error('Error playing audio:', error);
            alert('Could not play the audio. Please check your connection.');
        });

        // Update play button state
        if (playBtn) {
            playBtn.innerHTML = '<span class="material-symbols-outlined font-fill text-xl">pause</span>';
        }

        // Update progress bar when audio loads
        audioElement.addEventListener('loadedmetadata', () => {
            const progressContainer = document.querySelector('[data-sticky-progress-bar]');
            if (progressContainer) {
                progressContainer.style.width = '0%';
            }
        });

        // Update progress bar as audio plays
        audioElement.addEventListener('timeupdate', () => {
            const progressContainer = document.querySelector('[data-sticky-progress-bar]');
            if (progressContainer && audioElement.duration) {
                const progress = (audioElement.currentTime / audioElement.duration) * 100;
                progressContainer.style.width = progress + '%';
            }
        });

        // Reset play button when audio ends
        audioElement.addEventListener('ended', () => {
            if (playBtn) {
                playBtn.innerHTML = '<span class="material-symbols-outlined font-fill text-xl">play_arrow</span>';
            }
            const progressContainer = document.querySelector('[data-sticky-progress-bar]');
            if (progressContainer) {
                progressContainer.style.width = '0%';
            }
        });
    }

    formatDuration(seconds) {
        if (!seconds) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    showLoading() {
        if (this.loadingState) this.loadingState.classList.remove('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.container) this.container.classList.add('hidden');
    }

    showEmpty() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.remove('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.container) this.container.classList.add('hidden');
    }

    showError(message) {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) {
            this.errorState.classList.remove('hidden');
            const msgEl = this.errorState.querySelector('.error-message');
            if (msgEl) msgEl.textContent = message;
        }
        if (this.container) this.container.classList.add('hidden');
    }

    showContent() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.container) this.container.classList.remove('hidden');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PromotedSongs;
} else {
    window.PromotedSongs = PromotedSongs;
}