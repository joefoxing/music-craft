/**
 * Lyrics Search Handler
 * Handles manual lyrics search using LRCLIB API
 */

class LyricsSearchHandler {
    constructor() {
        this.modal = null;
        this.resultsContainer = null;
        this.searchBtn = null;
        this.trackInput = null;
        this.artistInput = null;
        this.closeBtn = null;
        this.currentAudioId = null;
        this.autoExtractionEnabled = true; // Tier 2: Auto-extract metadata
    }

    init() {
        // Get DOM elements
        this.modal = document.getElementById('lyricsSearchModal');
        this.resultsContainer = document.getElementById('lyricsSearchResults');
        this.searchBtn = document.getElementById('searchLyricsBtn');
        this.trackInput = document.getElementById('lyricsSearchTrack');
        this.artistInput = document.getElementById('lyricsSearchArtist');
        this.closeBtn = document.getElementById('closeLyricsModal');

        if (!this.modal || !this.resultsContainer || !this.searchBtn) {
            console.warn('Lyrics search elements not found');
            return;
        }

        // Bind event listeners
        this.searchBtn.addEventListener('click', () => this.handleSearch());
        this.closeBtn.addEventListener('click', () => this.closeModal());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Allow Enter key to trigger search
        this.trackInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        this.artistInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
    }
    /**
     * Automatically extract metadata from uploaded file and search for lyrics (Tier 2)
     * @param {File} audioFile - The uploaded audio file
     */
    async autoExtractAndSearch(audioFile) {
        if (!this.autoExtractionEnabled || !audioFile) {
            return;
        }

        console.log('[Tier 2] Auto-extracting metadata from:', audioFile.name);
        
        try {
            // Step 1: Extract metadata
            const metadataFormData = new FormData();
            metadataFormData.append('file', audioFile);

            const metadataResponse = await fetch('/api/lyrics-search/extract-metadata', {
                method: 'POST',
                body: metadataFormData
            });

            if (!metadataResponse.ok) {
                console.warn('[Tier 2] Metadata extraction failed:', metadataResponse.status);
                return;
            }

            const metadata = await metadataResponse.json();
            console.log('[Tier 2] Metadata extracted:', metadata);

            // Populate search fields if found
            if (metadata.artist) {
                this.artistInput.value = metadata.artist;
            }
            if (metadata.title) {
                this.trackInput.value = metadata.title;
            }

            // Step 2: Auto-search if we have at least a title
            if (metadata.title) {
                console.log('[Tier 2] Auto-searching LRCLIB for:', metadata.title, metadata.artist || '(no artist)');
                
                const searchResponse = await fetch('/api/lyrics-search/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        track_name: metadata.title,
                        artist_name: metadata.artist || ''
                    })
                });

                const searchData = await searchResponse.json();

                if (searchResponse.ok && searchData.results && searchData.results.length > 0) {
                    console.log(`[Tier 2] Found ${searchData.results.length} lyrics result(s)`);
                    this.displayResults(searchData.results);
                    this.openModal();
                    this.showNotification(`Found ${searchData.results.length} lyrics for "${metadata.title}"`, 'success');
                } else {
                    console.log('[Tier 2] No LRCLIB results, will fall back to Tier 3');
                    this.showNotification(`No lyrics found for "${metadata.title}" - will use AI transcription`, 'info');
                }
            } else {
                console.log('[Tier 2] No title found in metadata, skipping auto-search');
            }
        } catch (error) {
            console.error('[Tier 2] Auto-extraction error:', error);
            // Don't show error to user - just silently fall back to Tier 3
        }
    }
    async handleSearch() {
        const trackName = this.trackInput.value.trim();
        if (!trackName) {
            this.showNotification('Please enter a song title', 'error');
            return;
        }

        const artistName = this.artistInput.value.trim();

        // Show loading state
        this.searchBtn.disabled = true;
        this.searchBtn.innerHTML = '<span class="material-symbols-outlined text-sm mr-1 animate-spin">progress_activity</span>Searching...';

        try {
            const response = await fetch('/api/lyrics-search/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    track_name: trackName,
                    artist_name: artistName
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Search failed');
            }

            if (data.results && data.results.length > 0) {
                this.displayResults(data.results);
                this.openModal();
            } else {
                this.showNotification('No lyrics found. Try different search terms.', 'info');
            }
        } catch (error) {
            console.error('Lyrics search error:', error);
            this.showNotification(error.message || 'Failed to search lyrics', 'error');
        } finally {
            // Reset button state
            this.searchBtn.disabled = false;
            this.searchBtn.innerHTML = '<span class="material-symbols-outlined text-sm mr-1">search</span>Search Lyrics';
        }
    }

    displayResults(results) {
        this.resultsContainer.innerHTML = '';

        const header = document.createElement('div');
        header.className = 'mb-3 text-sm text-slate-600 dark:text-slate-400';
        header.textContent = `Found ${results.length} result(s)`;
        this.resultsContainer.appendChild(header);

        results.forEach(result => {
            const resultCard = this.createResultCard(result);
            this.resultsContainer.appendChild(resultCard);
        });
    }

    createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'mb-3 p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-primary dark:hover:border-primary transition-colors cursor-pointer bg-slate-50 dark:bg-slate-800/30';

        const hasLyrics = result.lyrics && result.lyrics.trim();
        const lyricsType = result.has_synced ? 'Synced' : 'Plain';
        const duration = result.duration ? `${Math.floor(result.duration / 60)}:${String(result.duration % 60).padStart(2, '0')}` : 'Unknown';

        card.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <div class="font-medium text-slate-900 dark:text-slate-100">${this.escapeHtml(result.track_name)}</div>
                    <div class="text-sm text-slate-600 dark:text-slate-400 mt-1">
                        ${result.artist_name ? this.escapeHtml(result.artist_name) : 'Unknown Artist'}
                        ${result.album_name ? ` • ${this.escapeHtml(result.album_name)}` : ''}
                    </div>
                    <div class="text-xs text-slate-500 dark:text-slate-500 mt-1">
                        Duration: ${duration}
                        ${hasLyrics ? ` • ${lyricsType} Lyrics` : ' • No lyrics available'}
                        ${result.instrumental ? ' • Instrumental' : ''}
                    </div>
                </div>
                <button class="apply-lyrics-btn bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-result='${JSON.stringify(result).replace(/'/g, '&apos;')}'>
                    Apply
                </button>
            </div>
        `;

        const applyBtn = card.querySelector('.apply-lyrics-btn');
        applyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.applyLyrics(result);
        });

        return card;
    }

    async applyLyrics(result) {
        if (!result.lyrics || !result.lyrics.trim()) {
            this.showNotification('No lyrics available for this track', 'error');
            return;
        }

        try {
            const requestData = {
                lyrics: result.lyrics,
                track_name: result.track_name,
                artist_name: result.artist_name,
                album_name: result.album_name
            };

            // Add audio_id if available (for saving to database)
            if (this.currentAudioId) {
                requestData.audio_id = this.currentAudioId;
            }

            const response = await fetch('/api/lyrics-search/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to apply lyrics');
            }

            // Update prompt input with lyrics
            const promptInput = document.getElementById('promptInput');
            if (promptInput) {
                // Strip timestamps from synced lyrics before applying
                const cleanLyrics = this.stripTimestamps(result.lyrics);
                promptInput.value = cleanLyrics;
                // Trigger input event to update character counter
                promptInput.dispatchEvent(new Event('input'));
            }

            this.showNotification(`Lyrics applied: ${result.track_name}`, 'success');
            this.closeModal();
        } catch (error) {
            console.error('Apply lyrics error:', error);
            this.showNotification(error.message || 'Failed to apply lyrics', 'error');
        }
    }

    setCurrentAudioId(audioId) {
        this.currentAudioId = audioId;
    }

    openModal() {
        if (this.modal) {
            this.modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    stripTimestamps(lyrics) {
        if (!lyrics) return '';
        
        // Remove LRC format timestamps like [00:12.50] or [01:23.456]
        // Also handles enhanced LRC with word timestamps like <00:12.50>
        return lyrics
            .split('\n')
            .map(line => line.replace(/^\s*\[[\d:.]+\]\s*/g, '').replace(/<[\d:.]+>/g, ''))
            .join('\n')
            .trim();
    }

    showNotification(message, type = 'info') {
        // Try to use the app's notification system if available
        if (window.showNotification) {
            window.showNotification(message, type);
        } else if (window.NotificationManager && window.NotificationManager.show) {
            window.NotificationManager.show(message, type);
        } else {
            // Fallback to console
            console.log(`[${type.toUpperCase()}] ${message}`);
            alert(message);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const lyricsSearchHandler = new LyricsSearchHandler();
    lyricsSearchHandler.init();
    
    // Make it globally accessible
    window.lyricsSearchHandler = lyricsSearchHandler;
});
