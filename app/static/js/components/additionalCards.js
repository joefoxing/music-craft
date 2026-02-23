/**
 * Additional Specialized Card Types
 * Extends the BaseCard class for more specific use cases
 */

console.log('Additional Specialized Card Types loaded');

/**
 * Lyric Card - For displaying generated lyrics
 */
class LyricCard extends BaseCard {
    constructor(options = {}) {
        super({
            clickable: true,
            hoverable: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default'; // 'default', 'compact', 'expanded'
        this.editable = options.editable || false;
    }
    
    /**
     * Create the lyric card element
     * @returns {HTMLElement} Lyric card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for lyric cards
        card.classList.add('lyric-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build lyric card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        // Get preview and full content
        const previewContent = this.getPreviewContent(data.content);
        const fullContent = data.content || '';
        
        // Build card HTML
        const cardHTML = `
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="material-symbols-outlined text-primary">lyrics</span>
                        <h4 class="font-bold text-slate-900 dark:text-white">${data.title || 'Untitled Lyrics'}</h4>
                        ${data.status ? CardUtils.createStatusBadge(this.getStatusType(data.status), data.status).outerHTML : ''}
                    </div>
                    ${data.project_info ? `
                    <div class="badge-container mb-3">
                        <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded-full text-xs">
                            <span class="material-symbols-outlined text-xs">check_circle</span>
                            ${data.project_info}
                        </span>
                    </div>
                    ` : ''}
                </div>
                <div class="flex items-center gap-2">
                    ${this.editable ? CardUtils.createActionButton('Edit', 'edit', 'secondary').outerHTML : ''}
                    <button class="expand-btn text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 p-1" data-action="expand">
                        <span class="material-symbols-outlined">expand_more</span>
                    </button>
                </div>
            </div>
            
            <!-- Lyric Content -->
            <div class="lyric-content-container">
                <div class="lyric-preview-content text-sm text-slate-700 dark:text-slate-300 mb-3 line-clamp-3">
                    ${previewContent}
                </div>
                
                <div class="lyric-full-content hidden text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    ${fullContent}
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
                <div class="flex items-center gap-2">
                    ${CardUtils.createActionButton('Copy', 'content_copy', 'info').outerHTML}
                    ${CardUtils.createActionButton('Use', 'check', 'success').outerHTML}
                    ${this.variant === 'default' ? CardUtils.createActionButton('Expand Editor', 'edit_note', 'secondary').outerHTML : ''}
                </div>
                <div class="text-xs text-slate-500">
                    ${data.word_count ? `${data.word_count} words` : ''}
                    ${data.created_at ? ` • ${CardUtils.formatTimeAgo(data.created_at)}` : ''}
                </div>
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
        
        // Add data attributes
        card.dataset.index = data.index || '';
    }
    
    /**
     * Get preview content (first few lines)
     * @param {string} content - Full lyric content
     * @returns {string} Preview content
     */
    getPreviewContent(content) {
        if (!content) return 'No content available';
        
        const lines = content.split('\n').filter(line => line.trim());
        const previewLines = lines.slice(0, 3);
        return previewLines.join('\n') + (lines.length > 3 ? '...' : '');
    }
    
    /**
     * Get status type for badge
     * @param {string} status - Status string
     * @returns {string} Status type
     */
    getStatusType(status) {
        switch (status?.toLowerCase()) {
            case 'complete':
            case 'completed':
            case 'success':
                return 'success';
            case 'error':
            case 'failed':
                return 'error';
            case 'generating':
            case 'processing':
                return 'pending';
            default:
                return 'info';
        }
    }
    
    /**
     * Setup event listeners for lyric card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Expand/collapse button
        const expandBtn = card.querySelector('[data-action="expand"]');
        if (expandBtn) {
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleExpansion(card);
            });
        }
        
        // Action buttons
        const actionButtons = card.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = button.textContent.trim().toLowerCase().replace(/\s+/g, '-');
                if (this.callbacks.onAction) {
                    this.callbacks.onAction(action, this.data, e);
                }
            });
        });
    }
    
    /**
     * Toggle content expansion
     * @param {HTMLElement} card - Card element
     */
    toggleExpansion(card) {
        const previewContent = card.querySelector('.lyric-preview-content');
        const fullContent = card.querySelector('.lyric-full-content');
        const expandBtn = card.querySelector('[data-action="expand"]');
        const expandIcon = expandBtn?.querySelector('.material-symbols-outlined');
        
        if (previewContent && fullContent) {
            const isExpanded = !previewContent.classList.contains('hidden');
            
            if (isExpanded) {
                // Collapse
                previewContent.classList.remove('hidden');
                fullContent.classList.add('hidden');
                if (expandIcon) expandIcon.textContent = 'expand_more';
            } else {
                // Expand
                previewContent.classList.add('hidden');
                fullContent.classList.remove('hidden');
                if (expandIcon) expandIcon.textContent = 'expand_less';
            }
        }
    }
}

/**
 * Audio Player Card - For displaying audio players in history modals
 */
class AudioPlayerCard extends BaseCard {
    constructor(options = {}) {
        super({
            interactive: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default'; // 'default', 'compact', 'detailed'
        this.showControls = options.showControls !== false;
    }
    
    /**
     * Create the audio player card element
     * @returns {HTMLElement} Audio player card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for audio player cards
        card.classList.add('audio-player-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build audio player card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        // Build card HTML
        const cardHTML = `
            <div class="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="material-symbols-outlined text-primary">music_note</span>
                        <h4 class="font-bold text-slate-900 dark:text-white" data-track-title>${data.title || 'Track Title'}</h4>
                        <span class="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full" data-track-number>Track ${data.track_number || 1}</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm mb-3">
                        ${CardUtils.createMetadataItem('Model', data.model || 'chirp-crow').outerHTML}
                        ${CardUtils.createMetadataItem('Duration', CardUtils.formatDuration(data.duration)).outerHTML}
                        ${CardUtils.createMetadataItem('Tags', data.tags || 'No tags').outerHTML}
                        ${CardUtils.createMetadataItem('Created', data.created ? CardUtils.formatTimeAgo(data.created) : 'N/A').outerHTML}
                    </div>
                    
                    ${data.lyrics || data.prompt ? `
                    <div class="mb-3">
                        <p class="text-slate-500 text-sm mb-1">Lyrics</p>
                        <div class="lyrics-container max-h-32 overflow-y-auto bg-slate-50 dark:bg-slate-800/50 rounded-lg p-2 border border-slate-200 dark:border-slate-700">
                            <div class="lyrics-content text-xs text-slate-700 dark:text-slate-300 whitespace-pre-line" data-track-prompt>${data.lyrics || data.prompt}</div>
                        </div>
                    </div>
                    ` : ''}
                </div>
                
                <div class="flex flex-col gap-2">
                    ${CardUtils.createActionButton('Download MP3', 'download', 'success').outerHTML}
                    ${CardUtils.createActionButton('Create Music Video', 'movie', 'info').outerHTML}
                    
                    ${data.image_url ? `
                    <div class="mt-2">
                        <p class="text-slate-500 text-sm mb-2">Generated Image</p>
                        <div class="relative bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
                            <img src="${data.image_url}" alt="Generated cover image" class="w-full h-32 object-contain bg-white hidden" data-image-display>
                            <div class="w-full h-32 flex items-center justify-center" data-image-placeholder>
                                <span class="material-symbols-outlined text-slate-400 text-4xl">image</span>
                            </div>
                        </div>
                        <a href="${data.image_url}" target="_blank" class="mt-1 text-xs text-primary hover:underline block text-center" data-image-url>View full image</a>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${this.showControls ? this.buildAudioControls().outerHTML : ''}
            
            ${data.audio_url || data.source_audio_url ? `
            <div class="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                <p class="text-slate-500 text-sm mb-2">Audio URLs</p>
                <div class="space-y-1">
                    ${data.audio_url ? `
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-xs text-green-500">link</span>
                        <a href="${data.audio_url}" target="_blank" class="text-primary hover:underline text-xs break-all" data-audio-url>Generated Audio URL</a>
                    </div>
                    ` : ''}
                    ${data.source_audio_url ? `
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-xs text-blue-500">link</span>
                        <a href="${data.source_audio_url}" target="_blank" class="text-primary hover:underline text-xs break-all" data-source-audio-url>Source Audio URL</a>
                    </div>
                    ` : ''}
                </div>
            </div>
            ` : ''}
            
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
    }
    
    /**
     * Build audio controls component
     * @returns {HTMLElement} Audio controls element
     */
    buildAudioControls() {
        const controls = document.createElement('div');
        controls.className = 'mt-4';
        controls.innerHTML = `
            <p class="text-slate-500 text-sm mb-2">Audio Preview</p>
            <div data-ws-player-container>
                <!-- WaveSurfer player will be rendered here -->
            </div>
        `;
        return controls;
    }
    
    /**
     * Setup event listeners for audio player card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Defer WaveSurfer init until element is in the DOM
        const wsContainer = card.querySelector('[data-ws-player-container]');
        const audioUrl = this.data.audio_url || '';
        if (wsContainer && audioUrl) {
            card._wsContainer = wsContainer;
            card._wsAudioUrl = audioUrl;
            // Use rAF to wait for DOM insertion before initializing WaveSurfer
            requestAnimationFrame(() => {
                if (card._wsContainer && card._wsAudioUrl && card.isConnected) {
                    this._wsPlayer = new UnifiedAudioPlayer(card._wsContainer, card._wsAudioUrl, {
                        height: 48,
                        progressColor: '#6366f1',
                        waveColor: '#94a3b8',
                    });
                    card._wsPlayer = this._wsPlayer;
                }
            });
        }
        
        // Action buttons
        const actionButtons = card.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = button.textContent.trim().toLowerCase().replace(/\s+/g, '-');
                if (this.callbacks.onAction) {
                    this.callbacks.onAction(action, this.data, e);
                }
            });
        });
    }
}

/**
 * Video Player Card - For displaying video players in history modals
 */
class VideoPlayerCard extends BaseCard {
    constructor(options = {}) {
        super({
            interactive: true,
            ...options
        });
        
        this.data = options.data || {};
        this.variant = options.variant || 'default';
        this.showControls = options.showControls !== false;
    }
    
    /**
     * Create the video player card element
     * @returns {HTMLElement} Video player card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for video player cards
        card.classList.add('video-player-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build video player card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        const isProcessing = data.status === 'processing' || data.status === 'pending';
        const hasVideo = data.video_url && !isProcessing;
        
        // Build card HTML
        const cardHTML = `
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h5 class="font-bold text-slate-900 dark:text-white text-lg" data-video-title>Music Video</h5>
                    <div class="flex items-center gap-3 mt-1">
                        <span class="text-xs px-2 py-1 bg-blue-500/10 text-blue-500 rounded-full">Video</span>
                        <span class="text-xs text-slate-500" data-video-status>${this.getStatusText(data.status)}</span>
                    </div>
                </div>
                ${hasVideo ? CardUtils.createActionButton('Download MP4', 'download', 'info').outerHTML : ''}
            </div>
            
            <div class="video-player-container mb-3" data-video-container style="display: ${hasVideo ? 'block' : 'none'};">
                <video controls class="w-full rounded-lg" data-video>
                    Your browser does not support the video element.
                </video>
            </div>
            
            <div class="video-status mb-3" data-video-status-container style="display: ${isProcessing ? 'block' : 'none'};">
                <div class="flex items-center gap-2 mb-2">
                    <span class="material-symbols-outlined text-blue-500">sync</span>
                    <span class="text-sm font-medium">Video generation in progress...</span>
                </div>
                <progress value="0" max="100" class="w-full h-2 rounded-full" data-video-progress></progress>
                <p class="text-xs text-slate-500 mt-1" data-video-status-text>Starting video generation</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                    <label class="block text-sm font-medium mb-1">Video Task ID</label>
                    <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm" data-video-task-id>${data.video_task_id || 'N/A'}</code>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Video URL</label>
                    ${hasVideo ? `<a href="${data.video_url}" target="_blank" class="text-blue-500 hover:underline break-all text-sm" data-video-url>View video</a>` : '<span class="text-slate-500 text-sm">Processing...</span>'}
                </div>
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
    }
    
    /**
     * Get status text for video
     * @param {string} status - Video status
     * @returns {string} Status text
     */
    getStatusText(status) {
        switch (status) {
            case 'processing':
            case 'pending':
                return 'Processing';
            case 'completed':
            case 'success':
                return 'Ready';
            case 'error':
            case 'failed':
                return 'Failed';
            default:
                return 'Unknown';
        }
    }
    
    /**
     * Setup event listeners for video player card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Action buttons
        const actionButtons = card.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = button.textContent.trim().toLowerCase().replace(/\s+/g, '-');
                if (this.callbacks.onAction) {
                    this.callbacks.onAction(action, this.data, e);
                }
            });
        });
    }
}

/**
 * Activity Feed Card - For displaying activity feed items
 */
class ActivityFeedCard extends BaseCard {
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
     * Create the activity feed card element
     * @returns {HTMLElement} Activity feed card element
     */
    createElement() {
        const card = super.createElement();
        
        // Add specific styling for activity feed cards
        card.classList.add('activity-feed-card');
        
        // Build card content
        this.buildContent(card);
        
        return card;
    }
    
    /**
     * Build activity feed card content
     * @param {HTMLElement} card - Card element
     */
    buildContent(card) {
        const { data } = this;
        
        // Build card HTML
        const cardHTML = `
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <span class="material-symbols-outlined text-primary">${this.getActivityIcon(data.type)}</span>
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <h4 class="font-medium text-slate-900 dark:text-white truncate">${data.title || 'Activity'}</h4>
                        ${data.status ? CardUtils.createStatusBadge(this.getStatusType(data.status), data.status).outerHTML : ''}
                    </div>
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-2">${data.description || ''}</p>
                    <div class="flex items-center gap-4 text-xs text-slate-500">
                        <span>${CardUtils.formatTimeAgo(data.timestamp)}</span>
                        ${data.user ? `<span>by ${data.user}</span>` : ''}
                        ${data.project ? `<span>${data.project}</span>` : ''}
                    </div>
                </div>
                ${data.action_url ? `
                <div class="flex-shrink-0">
                    <a href="${data.action_url}" class="text-primary hover:text-primary-dark text-sm font-medium">
                        View
                    </a>
                </div>
                ` : ''}
            </div>
        `;
        
        card.innerHTML = cardHTML;
        
        // Add event listeners
        this.setupEventListeners(card);
    }
    
    /**
     * Get icon for activity type
     * @param {string} type - Activity type
     * @returns {string} Icon name
     */
    getActivityIcon(type) {
        const icons = {
            'template-applied': 'auto_awesome',
            'music-generated': 'music_note',
            'cover-created': 'palette',
            'lyric-generated': 'lyrics',
            'video-created': 'movie',
            'user-registered': 'person_add',
            'user-login': 'login',
            'task-completed': 'check_circle',
            'task-failed': 'error',
            'default': 'activity'
        };
        
        return icons[type] || icons.default;
    }
    
    /**
     * Get status type for activity
     * @param {string} status - Status string
     * @returns {string} Status type
     */
    getStatusType(status) {
        switch (status?.toLowerCase()) {
            case 'success':
            case 'completed':
            case 'active':
                return 'success';
            case 'error':
            case 'failed':
            case 'inactive':
                return 'error';
            case 'pending':
            case 'processing':
                return 'pending';
            default:
                return 'info';
        }
    }
    
    /**
     * Setup event listeners for activity feed card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        // Click handler
        if (this.callbacks.onAction) {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('a')) {
                    this.callbacks.onAction('click', this.data, e);
                }
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LyricCard,
        AudioPlayerCard,
        VideoPlayerCard,
        ActivityFeedCard
    };
} else {
    window.LyricCard = LyricCard;
    window.AudioPlayerCard = AudioPlayerCard;
    window.VideoPlayerCard = VideoPlayerCard;
    window.ActivityFeedCard = ActivityFeedCard;
}