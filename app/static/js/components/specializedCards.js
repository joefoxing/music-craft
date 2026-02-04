/**
 * Specialized Card Types
 * Extends the BaseCard class for specific use cases throughout the application
 */

console.log('Specialized Card Types loaded');

/**
 * History Card - For displaying callback history entries
 */
class HistoryCard extends BaseCard {
    constructor(options = {}) {
        super({
            clickable: true,
            hoverable: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default'; // 'default', 'compact', 'detailed'
    }
    
    /**
     * Create the history card element
     * @returns {HTMLElement} History card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for history cards
        card.classList.add('history-card');
        
        // Build card content based on variant
        switch (this.variant) {
            case 'compact':
                this.buildCompactContent(card);
                break;
            case 'detailed':
                this.buildDetailedContent(card);
                break;
            default:
                this.buildDefaultContent(card);
        }
        
        return card;
    }
    
    /**
     * Build default history card content
     * @param {HTMLElement} card - Card element
     */
    buildDefaultContent(card) {
        const { data } = this;
        
        // Format timestamp
        const timestamp = new Date(data.timestamp);
        const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = timestamp.toLocaleDateString();
        
        // Determine status and callback type badges
        const statusBadge = CardUtils.createStatusBadge(
            this.getStatusType(data), 
            this.getStatusText(data)
        );
        
        const callbackTypeBadge = this.createCallbackTypeBadge(data.callback_type);
        
        // Get task ID for display
        const taskId = data.task_id || 'N/A';
        const shortTaskId = taskId.length > 12 ? taskId.substring(0, 12) + '...' : taskId;
        
        // Get tracks count
        const tracksCount = data.tracks_count || 0;
        
        // Build card HTML
        const cardHTML = `
            <div class="flex flex-col gap-3">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="material-symbols-outlined text-primary text-lg">history</span>
                            <h4 class="font-bold text-slate-900 dark:text-white truncate">Task: ${shortTaskId}</h4>
                        </div>
                        <p class="text-xs text-slate-500 dark:text-slate-400">${dateStr} at ${timeStr}</p>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        ${statusBadge.outerHTML}
                        ${callbackTypeBadge.outerHTML}
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-slate-500 text-sm">queue_music</span>
                        <span class="text-slate-600 dark:text-slate-400">${tracksCount} track(s)</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-slate-500 text-sm">schedule</span>
                        <span class="text-slate-600 dark:text-slate-400">${CardUtils.formatTimeAgo(timestamp)}</span>
                    </div>
                </div>
                
                <div class="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 dark:border-border-dark">
                    <button class="view-detail-btn text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1" data-action="view-details">
                        <span class="material-symbols-outlined text-sm">visibility</span>
                        View Details
                    </button>
                </div>
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners for action buttons
        this.setupActionListeners(card);
    }
    
    /**
     * Build compact history card content
     * @param {HTMLElement} card - Card element
     */
    buildCompactContent(card) {
        const { data } = this;
        
        const timestamp = new Date(data.timestamp);
        const shortTaskId = (data.task_id || 'N/A').substring(0, 8) + '...';
        
        const cardHTML = `
            <div class="flex items-center gap-3">
                <div class="flex-shrink-0">
                    <span class="material-symbols-outlined text-primary">history</span>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="font-medium text-slate-900 dark:text-white truncate">${shortTaskId}</p>
                    <p class="text-xs text-slate-500">${CardUtils.formatTimeAgo(timestamp)}</p>
                </div>
                <div class="flex-shrink-0">
                    ${CardUtils.createStatusBadge(this.getStatusType(data), this.getStatusText(data)).outerHTML}
                </div>
            </div>
        `;
        
        card.innerHTML = cardHTML;
    }
    
    /**
     * Build detailed history card content
     * @param {HTMLElement} card - Card element
     */
    buildDetailedContent(card) {
        // Similar to default but with more information
        this.buildDefaultContent(card);
        
        // Add additional details
        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'mt-4 pt-4 border-t border-slate-200 dark:border-slate-700';
        detailsContainer.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between text-sm">
                    <span class="text-slate-500">Status Code:</span>
                    <span class="font-mono text-slate-900 dark:text-white">${data.status_code || 'N/A'}</span>
                </div>
                ${data.status_message ? `
                <div class="flex justify-between text-sm">
                    <span class="text-slate-500">Message:</span>
                    <span class="text-slate-900 dark:text-white truncate max-w-xs">${data.status_message}</span>
                </div>
                ` : ''}
            </div>
        `;
        
        card.appendChild(detailsContainer);
    }
    
    /**
     * Create callback type badge
     * @param {string} callbackType - Callback type
     * @returns {HTMLElement} Badge element
     */
    createCallbackTypeBadge(callbackType) {
        const badge = document.createElement('span');
        badge.className = `callback-type-badge ${this.getCallbackTypeClasses(callbackType)}`;
        badge.textContent = callbackType || 'unknown';
        return badge;
    }
    
    /**
     * Get CSS classes for callback type badges
     * @param {string} callbackType - Callback type
     * @returns {string} CSS classes
     */
    getCallbackTypeClasses(callbackType) {
        const typeClasses = {
            complete: 'callback-type-complete',
            first: 'callback-type-first',
            text: 'callback-type-text',
            error: 'callback-type-error'
        };
        
        return typeClasses[callbackType] || typeClasses.text;
    }
    
    /**
     * Get status type for badge
     * @param {Object} data - Card data
     * @returns {string} Status type
     */
    getStatusType(data) {
        if (data.status_code === 200) return 'success';
        if (data.status_code && data.status_code !== 200) return 'error';
        return 'info';
    }
    
    /**
     * Get status text for badge
     * @param {Object} data - Card data
     * @returns {string} Status text
     */
    getStatusText(data) {
        if (data.status_code === 200) return 'success';
        if (data.status_code && data.status_code !== 200) return 'error';
        return data.status || 'unknown';
    }
    
    /**
     * Setup action button event listeners
     * @param {HTMLElement} card - Card element
     */
    setupActionListeners(card) {
        const viewDetailsBtn = card.querySelector('[data-action="view-details"]');
        if (viewDetailsBtn) {
            viewDetailsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('view-details', this.data, e);
                }
            });
        }
    }
}

/**
 * Song Card - For displaying audio tracks in library
 */
class SongCard extends BaseCard {
    constructor(options = {}) {
        super({
            clickable: true,
            hoverable: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default';
        this.showControls = options.showControls !== false;
    }
    
    /**
     * Create the song card element
     * @returns {HTMLElement} Song card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for song cards
        card.classList.add('song-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build song card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        // Set basic info
        const title = data.title || 'Unknown Title';
        const artist = data.artist || 'Unknown Artist';
        const album = data.album || '';
        const duration = CardUtils.formatDuration(data.duration);
        const fileSize = CardUtils.formatFileSize(data.file_size);
        const genre = data.genre || 'Unknown';
        const playCount = data.play_count || 0;
        const uploadDate = data.uploaded_at ? CardUtils.formatTimeAgo(data.uploaded_at) : 'Unknown';
        
        // Build card HTML
        const cardHTML = `
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1 min-w-0">
                    <h3 class="font-bold text-slate-900 dark:text-white text-lg mb-1 truncate song-title">${title}</h3>
                    <p class="text-slate-600 dark:text-slate-400 text-sm mb-1 song-artist">${artist}</p>
                    ${album ? `<p class="text-slate-500 dark:text-slate-500 text-xs song-album">${album}</p>` : ''}
                </div>
                <div class="flex items-center gap-2 ml-4">
                    ${this.createFavoriteButton().outerHTML}
                    ${this.createMenuButton().outerHTML}
                </div>
            </div>
            
            ${this.showControls ? this.buildAudioPlayer().outerHTML : ''}
            
            <!-- Metadata -->
            <div class="grid grid-cols-2 gap-3 text-xs text-slate-500 dark:text-slate-400 mb-4">
                ${CardUtils.createMetadataItem('Duration:', duration).outerHTML}
                ${CardUtils.createMetadataItem('Size:', fileSize).outerHTML}
                ${CardUtils.createMetadataItem('Genre:', genre).outerHTML}
                ${CardUtils.createMetadataItem('Plays:', playCount.toString()).outerHTML}
            </div>
            
            <!-- Tags -->
            ${data.tags && data.tags.length > 0 ? `
            <div class="flex flex-wrap gap-1 mb-4" data-tags-container>
                ${data.tags.map(tag => CardUtils.createTag(tag).outerHTML).join('')}
            </div>
            ` : ''}
            
            <!-- Actions -->
            <div class="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700">
                <div class="flex items-center gap-2">
                    <span class="text-xs text-slate-400">${uploadDate}</span>
                </div>
                <div class="flex items-center gap-2">
                    ${CardUtils.createActionButton('Add', 'playlist_add', 'info').outerHTML}
                    ${CardUtils.createActionButton('Download', 'download', 'success').outerHTML}
                    ${CardUtils.createActionButton('Edit', 'edit', 'secondary').outerHTML}
                </div>
            </div>
            
            <!-- Hidden audio element -->
            <audio class="hidden" data-audio-element>
                <source src="${data.audio_url || ''}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
    }
    
    /**
     * Build audio player component
     * @returns {HTMLElement} Audio player element
     */
    buildAudioPlayer() {
        const player = document.createElement('div');
        player.className = 'mb-4';
        player.innerHTML = `
            <div class="flex items-center gap-3 bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
                <button class="song-play-btn p-2 bg-primary hover:bg-primary-dark text-white rounded-full transition-colors" aria-label="Play song">
                    <span class="material-symbols-outlined play-icon" data-play-icon>play_arrow</span>
                    <span class="material-symbols-outlined pause-icon hidden" data-pause-icon>pause</span>
                </button>
                <div class="flex-1">
                    <div class="song-progress-bar h-1 bg-slate-300 dark:bg-slate-700 rounded-full overflow-hidden cursor-pointer">
                        <div class="song-progress h-full bg-primary" style="width: 0%" data-progress></div>
                    </div>
                    <div class="flex justify-between text-xs text-slate-500 mt-1">
                        <span class="song-current-time">0:00</span>
                        <span class="song-duration" data-duration>0:00</span>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button class="volume-btn p-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300" aria-label="Volume">
                        <span class="material-symbols-outlined text-sm">volume_up</span>
                    </button>
                    <input type="range" min="0" max="100" value="80" class="volume-slider w-16 accent-primary" aria-label="Volume slider">
                </div>
            </div>
        `;
        return player;
    }
    
    /**
     * Create favorite button
     * @returns {HTMLElement} Favorite button element
     */
    createFavoriteButton() {
        const button = document.createElement('button');
        button.className = 'song-favorite-btn p-2 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors';
        button.setAttribute('aria-label', 'Toggle favorite');
        
        const isFavorite = this.data.is_favorite;
        button.innerHTML = `
            <span class="material-symbols-outlined text-red-500 text-lg ${isFavorite ? '' : 'hidden'}" data-favorite-icon>favorite</span>
            <span class="material-symbols-outlined text-slate-400 text-lg ${isFavorite ? 'hidden' : ''}" data-not-favorite-icon>favorite_border</span>
        `;
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            if (this.callbacks.onAction) {
                this.callbacks.onAction('toggle-favorite', this.data, e);
            }
        });
        
        return button;
    }
    
    /**
     * Create menu button
     * @returns {HTMLElement} Menu button element
     */
    createMenuButton() {
        const button = document.createElement('button');
        button.className = 'song-menu-btn p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors';
        button.setAttribute('aria-label', 'Song options');
        button.innerHTML = '<span class="material-symbols-outlined text-slate-400">more_vert</span>';
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            if (this.callbacks.onAction) {
                this.callbacks.onAction('show-menu', this.data, e);
            }
        });
        
        return button;
    }
    
    /**
     * Setup event listeners for song card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Play/pause button
        const playBtn = card.querySelector('.song-play-btn');
        const audioElement = card.querySelector('[data-audio-element]');
        
        if (playBtn && audioElement) {
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('play-pause', this.data, e);
                }
            });
        }
        
        // Favorite button
        const favoriteBtn = card.querySelector('.song-favorite-btn');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('toggle-favorite', this.data, e);
                }
            });
        }

        // Menu button
        const menuBtn = card.querySelector('.song-menu-btn');
        if (menuBtn) {
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('show-menu', this.data, e);
                }
            });
        }
        
        // Action buttons
        const actionButtons = card.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Get action from data attribute or fallback to text content (handling icons)
                let action = button.getAttribute('data-action');
                
                if (!action) {
                    // Fallback: try to get text from the text span specifically, avoiding the icon
                    const textSpan = button.querySelector('span:not(.material-symbols-outlined)');
                    if (textSpan) {
                        action = textSpan.textContent.trim().toLowerCase();
                    } else {
                        // Last resort: clean up textContent by removing common icon ligature text if detected
                        action = button.textContent.trim().toLowerCase();
                    }
                }
                
                // Normalize action (replace spaces with dashes)
                if (action) {
                    action = action.replace(/\s+/g, '-');
                }
                
                console.log('Action button clicked:', action);
                
                if (this.callbacks.onAction) {
                    this.callbacks.onAction(action, this.data, e);
                }
            });
        });
    }
}

/**
 * Template Card - For displaying music generation templates
 */
class TemplateCard extends BaseCard {
    constructor(options = {}) {
        super({
            clickable: true,
            hoverable: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default';
    }
    
    /**
     * Create the template card element
     * @returns {HTMLElement} Template card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for template cards
        card.classList.add('template-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build template card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        // Determine difficulty badge color and text
        const difficultyColor = this.getDifficultyColor(data.difficulty);
        const difficultyText = this.formatDifficultyText(data.difficulty);
        
        // Determine popularity stars
        const popularityStars = this.getPopularityStars(data.popularity);
        
        // Get template gradient and icon
        const gradient = this.getTemplateGradient(data.category);
        const icon = this.getTemplateIcon(data.category);
        
        // Build card HTML
        const cardHTML = `
            <div class="relative">
                <!-- Template image/icon -->
                <div class="h-40 bg-gradient-to-br ${gradient} flex items-center justify-center mb-4">
                    <span class="material-symbols-outlined text-white text-5xl opacity-80 group-hover:scale-110 transition-transform">
                        ${icon}
                    </span>
                    ${data.popularity >= 80 ? '<div class="absolute top-2 right-2"><span class="material-symbols-outlined text-yellow-400">star</span></div>' : ''}
                </div>
                
                <!-- Content -->
                <div class="space-y-3">
                    <div class="flex items-start justify-between">
                        <h4 class="font-bold text-slate-900 dark:text-white truncate flex-1">${data.name}</h4>
                        <div class="flex items-center gap-1 text-amber-500 ml-2">
                            ${popularityStars}
                        </div>
                    </div>
                    
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-3 line-clamp-2">${data.description}</p>
                    
                    ${data.tags && data.tags.length > 0 ? `
                    <div class="flex flex-wrap gap-1 mb-3">
                        ${data.tags.slice(0, 3).map(tag => CardUtils.createTag(tag).outerHTML).join('')}
                    </div>
                    ` : ''}
                    
                    <div class="flex items-center justify-between text-xs text-slate-500">
                        <div class="flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">category</span>
                            <span class="truncate">${this.formatCategoryName(data.category)}</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">timer</span>
                            <span>${data.estimated_time || '5-10'} min</span>
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <span class="inline-block px-2 py-1 rounded text-xs font-medium ${difficultyColor}">
                            ${difficultyText}
                        </span>
                        <div class="flex gap-1">
                            ${CardUtils.createActionButton('Preview', 'visibility', 'secondary').outerHTML}
                            ${CardUtils.createActionButton('Apply', 'play_arrow', 'primary').outerHTML}
                        </div>
                    </div>
                </div>
                
                <!-- Context Menu -->
                <div class="template-context-menu absolute right-0 top-full mt-1 bg-white dark:bg-surface-dark border border-slate-200 dark:border-border-dark rounded-lg shadow-xl z-50 hidden min-w-[180px] animate-slide-in">
                    <div class="py-1">
                        <button class="context-menu-item w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">music_note</span>
                            Apply to Music Generator
                        </button>
                        <button class="context-menu-item w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">palette</span>
                            Apply to Cover Generator
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
    }
    
    /**
     * Get difficulty badge color
     * @param {string} difficulty - Difficulty level
     * @returns {string} CSS classes
     */
    getDifficultyColor(difficulty) {
        const colors = {
            beginner: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            easy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            intermediate: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            advanced: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
            expert: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
        };
        
        return colors[difficulty] || colors.intermediate;
    }
    
    /**
     * Format difficulty text
     * @param {string} difficulty - Difficulty level
     * @returns {string} Formatted difficulty text
     */
    formatDifficultyText(difficulty) {
        const texts = {
            beginner: 'Beginner',
            easy: 'Easy',
            intermediate: 'Intermediate',
            advanced: 'Advanced',
            expert: 'Expert'
        };
        
        return texts[difficulty] || 'Intermediate';
    }
    
    /**
     * Get popularity stars HTML
     * @param {number} popularity - Popularity percentage
     * @returns {string} Stars HTML
     */
    getPopularityStars(popularity) {
        const stars = Math.round(popularity / 20); // Convert percentage to 5-star rating
        return '★'.repeat(stars) + '☆'.repeat(5 - stars);
    }
    
    /**
     * Get template gradient based on category
     * @param {string} category - Template category
     * @returns {string} CSS gradient classes
     */
    getTemplateGradient(category) {
        const gradients = {
            electronic: 'from-purple-500 to-pink-500',
            rock: 'from-red-500 to-orange-500',
            jazz: 'from-blue-500 to-indigo-500',
            classical: 'from-yellow-500 to-amber-500',
            cinematic: 'from-gray-700 to-gray-900',
            ambient: 'from-teal-500 to-cyan-500',
            hyperpop: 'from-pink-500 to-purple-500',
            drill: 'from-gray-800 to-black',
            afrobeats: 'from-orange-500 to-red-500',
            'neo-soul': 'from-purple-600 to-blue-600',
            'drum-bass': 'from-green-500 to-teal-500',
            reggaeton: 'from-yellow-500 to-orange-500',
            phonk: 'from-red-600 to-purple-600',
            'k-pop': 'from-pink-400 to-purple-400',
            'trap-metal': 'from-gray-600 to-red-600',
            'hip-hop': 'from-orange-600 to-yellow-600',
            latin: 'from-red-500 to-pink-500'
        };
        
        return gradients[category] || 'from-slate-500 to-slate-700';
    }
    
    /**
     * Get template icon based on category
     * @param {string} category - Template category
     * @returns {string} Material icon name
     */
    getTemplateIcon(category) {
        const icons = {
            electronic: 'speaker',
            rock: 'electric_guitar',
            jazz: 'piano',
            classical: 'music_note',
            cinematic: 'movie',
            ambient: 'nature',
            hyperpop: 'star',
            drill: 'music_video',
            afrobeats: 'music_video',
            'neo-soul': 'music_note',
            'drum-bass': 'music_video',
            reggaeton: 'music_video',
            phonk: 'music_video',
            'k-pop:': 'star',
            'trap-metal': 'music_video',
            'hip-hop': 'music_video',
            latin: 'music_video'
        };
        
        return icons[category] || 'music_note';
    }
    
    /**
     * Format category name
     * @param {string} category - Category name
     * @returns {string} Formatted category name
     */
    formatCategoryName(category) {
        if (!category) return 'Unknown';
        return category.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    /**
     * Setup event listeners for template card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Action buttons
        const previewBtn = card.querySelector('[data-action="preview"]');
        const applyBtn = card.querySelector('[data-action="apply"]');
        
        if (previewBtn) {
            previewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('preview', this.data, e);
                }
            });
        }
        
        if (applyBtn) {
            applyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('apply', this.data, e);
                }
            });
        }
        
        // Context menu
        const applyMainBtn = card.querySelector('.action-btn[data-action="apply"]');
        const contextMenu = card.querySelector('.template-context-menu');
        const musicGeneratorBtn = contextMenu?.querySelector('.context-menu-item:nth-child(1)');
        const coverGeneratorBtn = contextMenu?.querySelector('.context-menu-item:nth-child(2)');
        
        if (applyMainBtn && contextMenu) {
            applyMainBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                contextMenu.classList.toggle('hidden');
            });
        }
        
        if (musicGeneratorBtn) {
            musicGeneratorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                contextMenu.classList.add('hidden');
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('apply-music-generator', this.data, e);
                }
            });
        }
        
        if (coverGeneratorBtn) {
            coverGeneratorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                contextMenu.classList.add('hidden');
                if (this.callbacks.onAction) {
                    this.callbacks.onAction('apply-cover-generator', this.data, e);
                }
            });
        }
        
        // Close context menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!card.contains(e.target) && contextMenu && !contextMenu.classList.contains('hidden')) {
                contextMenu.classList.add('hidden');
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        HistoryCard,
        SongCard,
        TemplateCard
    };
} else {
    window.HistoryCard = HistoryCard;
    window.SongCard = SongCard;
    window.TemplateCard = TemplateCard;
}