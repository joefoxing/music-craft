/**
 * Audio player component for the Music Cover Generator application.
 * Handles displaying and managing audio players for generated songs.
 */

class AudioPlayerComponent {
    constructor() {
        this.container = null;
        this.template = null;
    }

    /**
     * Initialize audio player component.
     * @param {HTMLElement} container - Container element for audio players
     * @param {HTMLTemplateElement} template - Template for audio player
     */
    initialize(container, template) {
        this.container = container;
        this.template = template;
    }

    /**
     * Display all audio players for multiple songs.
     * @param {Array} sunoData - Array of song data objects
     * @param {string} currentTaskId - Current task ID
     * @param {Function} onVideoCreate - Callback for video creation
     */
    displayAllAudioPlayers(sunoData, currentTaskId, onVideoCreate = null) {
        if (!this.container || !this.template) {
            console.error('Audio player container or template not initialized');
            return;
        }

        // Clear existing content
        this.container.innerHTML = '';

        // Create a player for each song
        sunoData.forEach((song, index) => {
            const player = this.createAudioPlayer(song, index, currentTaskId, onVideoCreate);
            this.container.appendChild(player);
        });
    }

    /**
     * Create a single audio player element.
     * @param {Object} song - Song data object
     * @param {number} index - Song index
     * @param {string} currentTaskId - Current task ID
     * @param {Function} onVideoCreate - Callback for video creation
     * @returns {HTMLElement} Audio player element
     */
    createAudioPlayer(song, index, currentTaskId, onVideoCreate = null) {
        const clone = this.template.content.cloneNode(true);
        const audioPlayerDiv = clone.querySelector('.audio-player');

        // Set song title (use title from song or default)
        const title = song.title || `Generated Song ${index + 1}`;
        clone.querySelector('[data-title]').textContent = title;

        // Set model
        clone.querySelector('[data-model]').textContent = song.modelName || song.model_name || 'chirp-crow';

        // Set duration
        const duration = song.duration ? `${Math.floor(song.duration)} seconds` : 'Unknown';
        clone.querySelector('[data-duration]').textContent = duration;

        // Set audio source - try multiple URL sources
        const audioElement = clone.querySelector('[data-audio]');
        const audioUrl = song.audioUrl || song.audio_url ||
                         (song.audio_urls && song.audio_urls.generated) ||
                         song.sourceAudioUrl || song.source_audio_url ||
                         (song.audio_urls && song.audio_urls.source) ||
                         song.streamAudioUrl || song.stream_audio_url ||
                         (song.audio_urls && song.audio_urls.stream) ||
                         song.sourceStreamAudioUrl || song.source_stream_audio_url ||
                         (song.audio_urls && song.audio_urls.source_stream);
        if (audioUrl) {
            audioElement.src = audioUrl;
        }

        // Set audio URL link
        const audioUrlLink = clone.querySelector('[data-audio-url]');
        if (audioUrl) {
            audioUrlLink.href = audioUrl;
            audioUrlLink.textContent = audioUrl;
        }

        // Handle image display
        this._setupImageDisplay(clone, song);

        // Set lyrics (display line by line)
        this._setupLyricsDisplay(clone, song);

        // Set up download button
        this._setupDownloadButton(clone, audioUrl, title);

        // Set up video button
        this._setupVideoButton(clone, song, currentTaskId, onVideoCreate);

        // Add enhanced callback data display
        this._addEnhancedDataDisplay(clone, song);

        // Inject TrackOptions
        if (typeof TrackOptions !== 'undefined') {
            const downloadBtn = clone.querySelector('[data-download-btn]');
            if (downloadBtn && downloadBtn.parentElement) {
                try {
                    const trackOptions = new TrackOptions();
                    // Ensure task ID is present
                    const trackData = { ...song, task_id: song.task_id || currentTaskId };
                    const menuElement = trackOptions.render(trackData);
                    menuElement.classList.add('self-end', 'mb-2');
                    downloadBtn.parentElement.insertBefore(menuElement, downloadBtn.parentElement.firstChild);
                } catch (e) {
                    console.error('Error injecting TrackOptions:', e);
                }
            }
        }

        return audioPlayerDiv;
    }

    /**
     * Set up image display for a song.
     * @private
     */
    _setupImageDisplay(clone, song) {
        let imageUrl = '';
        // Try different possible image URL structures
        if (song.image_url) {
            imageUrl = song.image_url;  // From user's JSON example
        } else if (song.imageUrl) {
            imageUrl = song.imageUrl;  // From current code
        } else if (song.image_urls && song.image_urls.generated) {
            imageUrl = song.image_urls.generated;  // From process_callback_data
        } else if (song.source_image_url) {
            imageUrl = song.source_image_url;  // Alternative from user's JSON
        } else if (song.sourceImageUrl) {
            imageUrl = song.sourceImageUrl;  // From current code
        }

        // Handle image display
        const imageDisplay = clone.querySelector('[data-image-display]');
        const imagePlaceholder = clone.querySelector('[data-image-placeholder]');
        const imageUrlLink = clone.querySelector('[data-image-url]');

        if (imageUrl) {
            // Set image source and show it
            imageDisplay.src = imageUrl;
            imageDisplay.classList.remove('hidden');
            imageDisplay.style.display = 'block';
            imagePlaceholder.style.display = 'none';

            // Set the link to view full image
            imageUrlLink.href = imageUrl;
            imageUrlLink.style.display = 'block';
            imageUrlLink.textContent = 'View full image';

            // Add error handling for broken images
            imageDisplay.onerror = function() {
                this.style.display = 'none';
                this.classList.add('hidden');
                imagePlaceholder.style.display = 'flex';
                imagePlaceholder.innerHTML = '<span class="material-symbols-outlined text-slate-400 text-4xl">broken_image</span>';
                imageUrlLink.textContent = 'Image failed to load';
            };
        } else {
            // No image available
            imageDisplay.style.display = 'none';
            imageDisplay.classList.add('hidden');
            imagePlaceholder.style.display = 'flex';
            imagePlaceholder.innerHTML = '<span class="material-symbols-outlined text-slate-400 text-4xl">image</span><span class="text-slate-500 ml-2">No image available</span>';
            imageUrlLink.style.display = 'none';
        }
    }

    /**
     * Set up lyrics display for a song.
     * @private
     */
    _setupLyricsDisplay(clone, song) {
        const lyricsElement = clone.querySelector('[data-lyrics]');
        const lyricsText = song.lyrics || song.prompt;
        if (lyricsText) {
            // Helper to escape HTML
            const escapeHtml = (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
            // Add line-by-line formatting for better readability
            lyricsElement.innerHTML = lyricsText.split('\n').map(line => {
                if (line.trim() === '') return '<br>';
                return `<div class="lyric-line py-1 border-b border-slate-100 dark:border-slate-700/50 last:border-b-0">${escapeHtml(line)}</div>`;
            }).join('');
        }
    }

    /**
     * Set up download button for a song.
     * @private
     */
    _setupDownloadButton(clone, audioUrl, title) {
        const downloadBtn = clone.querySelector('[data-download-btn]');
        if (audioUrl) {
            downloadBtn.addEventListener('click', () => {
                this.handleDownloadAudio(audioUrl, title);
            });
        } else {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<span class="material-symbols-outlined mr-2">block</span> No URL';
        }
    }

    /**
     * Set up video button for a song.
     * @private
     */
    _setupVideoButton(clone, song, currentTaskId, onVideoCreate) {
        const videoBtn = clone.querySelector('[data-video-btn]');
        if (videoBtn && song.id) {
            videoBtn.dataset.audioId = song.id;
            videoBtn.dataset.taskId = currentTaskId;

            // Only show video button if there's an image (needed for video)
            // Check for image URL using all possible property names
            const hasImageUrl = song.image_url ||
                               song.imageUrl ||
                               (song.image_urls && song.image_urls.generated) ||
                               song.source_image_url ||
                               song.sourceImageUrl;
            
            if (hasImageUrl) {
                videoBtn.style.display = 'block';
                console.log('Video button shown for song:', song.title, 'with image:', hasImageUrl);
                videoBtn.addEventListener('click', () => {
                    console.log('Video button clicked for song:', song);
                    if (onVideoCreate) {
                        onVideoCreate(song);
                    }
                });
            } else {
                console.log('Video button hidden - no image for song:', song.title);
            }
        } else {
            console.log('Video button not found or song missing ID:', song.id);
        }
    }

    /**
     * Add enhanced data display to audio player.
     * @private
     */
    _addEnhancedDataDisplay(clone, song) {
        const audioPlayerDiv = clone.querySelector('.audio-player');
        if (audioPlayerDiv) {
            // Create enhanced data section
            const enhancedDataDiv = document.createElement('div');
            enhancedDataDiv.className = 'mt-4 pt-4 border-t border-slate-200 dark:border-slate-700';
            enhancedDataDiv.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Track ID</label>
                        <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-xs">${song.id || 'N/A'}</code>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Created</label>
                        <span class="text-slate-700 dark:text-slate-300">${song.createTime || song.create_time || 'N/A'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Tags/Genre</label>
                        <span class="text-slate-700 dark:text-slate-300">${song.tags || 'N/A'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Source Audio</label>
                        ${song.sourceAudioUrl || song.source_audio_url ?
                            `<a href="${song.sourceAudioUrl || song.source_audio_url}" target="_blank" class="text-primary hover:underline text-xs break-all">View Source</a>` :
                            '<span class="text-slate-500 text-xs">N/A</span>'}
                    </div>
                </div>
            `;
            audioPlayerDiv.appendChild(enhancedDataDiv);
        }
    }

    /**
     * Handle audio download.
     * @param {string} audioUrl - URL of the audio file
     * @param {string} title - Song title for filename
     */
    async handleDownloadAudio(audioUrl, title) {
        if (!audioUrl) {
            window.NotificationSystem?.showError('No audio URL available for download');
            return;
        }

        // Create a safe filename from the title
        const safeTitle = (title || 'generated-cover').replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const filename = `${safeTitle}.mp3`;

        console.log('Downloading audio:', { audioUrl, filename });

        try {
            // Use server-side proxy for download
            const response = await fetch('/api/download-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: audioUrl,
                    filename: filename
                })
            });

            console.log('Download audio API response status:', response.status);

            if (response.ok) {
                // Get the blob from the response
                const blob = await response.blob();

                // Create download link and trigger download
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                link.style.display = 'none';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                // Clean up the object URL
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                }, 100);

                window.NotificationSystem?.showSuccess('Download started! The file will be saved as: ' + filename);

            } else {
                // API returned an error, fall back to direct download
                console.error('Download audio API error:', response.status);
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                const errorMsg = errorData.error || errorData.msg || `Server error: ${response.status}`;

                console.log('Falling back to direct download:', errorMsg);

                // Try direct download as fallback
                const a = document.createElement('a');
                a.href = audioUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                window.NotificationSystem?.showSuccess('Download started using direct method!');
            }

        } catch (error) {
            console.error('Error downloading audio:', error);

            // Fall back to direct download
            const a = document.createElement('a');
            a.href = audioUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            window.NotificationSystem?.showSuccess('Download started using fallback method!');
        }
    }

    /**
     * Display callback information.
     * @param {Object} callbackData - Callback data object
     */
    displayCallbackInfo(callbackData) {
        if (!this.container) return;

        // Create callback info card
        const callbackCard = document.createElement('div');
        callbackCard.className = 'callback-card border border-blue-200 dark:border-blue-800 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20 mb-6';
        callbackCard.innerHTML = `
            <div class="flex items-center gap-2 mb-3">
                <span class="material-symbols-outlined text-blue-500">info</span>
                <h5 class="font-bold text-slate-900 dark:text-white">Callback Information</h5>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                    <label class="block text-xs font-medium text-slate-500 mb-1">Callback Type</label>
                    <span class="inline-block px-2 py-1 rounded text-xs font-medium
                        ${callbackData.callbackType === 'complete' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                          callbackData.callbackType === 'first' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                          callbackData.callbackType === 'text' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'}">
                        ${callbackData.callbackType || 'unknown'}
                    </span>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-500 mb-1">Status Code</label>
                    <span class="inline-block px-2 py-1 rounded text-xs font-medium
                        ${callbackData.code === 200 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                          'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}">
                        ${callbackData.code || 'N/A'}
                    </span>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-500 mb-1">Tracks Generated</label>
                    <span class="text-slate-700 dark:text-slate-300">${callbackData.tracks ? callbackData.tracks.length : 0}</span>
                </div>
            </div>
            
            <div class="mt-3">
                <label class="block text-xs font-medium text-slate-500 mb-1">Status Message</label>
                <p class="text-sm text-slate-700 dark:text-slate-300">${callbackData.message || 'No message'}</p>
            </div>
        `;

        // Insert at the beginning of the container
        if (this.container.firstChild) {
            this.container.insertBefore(callbackCard, this.container.firstChild);
        } else {
            this.container.appendChild(callbackCard);
        }
    }

    /**
     * Show callback history summary.
     * @param {Array} callbacks - Array of callback objects
     */
    showCallbackHistorySummary(callbacks) {
        if (!this.container || callbacks.length <= 1) return;

        const historyCard = document.createElement('div');
        historyCard.className = 'history-card border border-purple-200 dark:border-purple-800 rounded-lg p-4 bg-purple-50 dark:bg-purple-900/20 mb-6';
        historyCard.innerHTML = `
            <div class="flex items-center gap-2 mb-3">
                <span class="material-symbols-outlined text-purple-500">history</span>
                <h5 class="font-bold text-slate-900 dark:text-white">Callback History</h5>
                <span class="ml-auto text-xs px-2 py-1 bg-purple-100 dark:bg-purple-800 text-purple-800 dark:text-purple-300 rounded-full">
                    ${callbacks.length} callback(s)
                </span>
            </div>
            
            <div class="space-y-2 max-h-40 overflow-y-auto">
                ${callbacks.map((callback, index) => `
                    <div class="flex items-center justify-between text-sm p-2 hover:bg-white/50 dark:hover:bg-black/20 rounded">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-xs ${
                                callback.callback_type === 'complete' ? 'text-green-500' :
                                callback.callback_type === 'first' ? 'text-yellow-500' :
                                callback.callback_type === 'text' ? 'text-blue-500' :
                                'text-gray-500'
                            }">circle</span>
                            <span class="font-medium">${callback.callback_type || 'unknown'}</span>
                        </div>
                        <div class="text-xs text-slate-500">
                            ${new Date(callback.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Insert after callback info card if it exists, otherwise at the beginning
        const callbackCard = this.container.querySelector('.callback-card');
        if (callbackCard) {
            callbackCard.insertAdjacentElement('afterend', historyCard);
        } else if (this.container.firstChild) {
            this.container.insertBefore(historyCard, this.container.firstChild);
        } else {
            this.container.appendChild(historyCard);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioPlayerComponent;
} else {
    window.AudioPlayerComponent = AudioPlayerComponent;
}