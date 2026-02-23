/**
 * History page for the Music Cover Generator application.
 * Uses modular components for better maintainability and separation of concerns.
 */

// Initialize modular components
const notificationSystem = window.NotificationSystem;
const historyManager = new window.HistoryManager();
const audioPlayerComponent = new window.AudioPlayerComponent();

// DOM Elements
const DOM = {
    // History manager elements
    historyContainer: document.getElementById('historyContainer'),
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    errorState: document.getElementById('errorState'),
    statsTotal: document.getElementById('statsTotal'),
    statsToday: document.getElementById('statsToday'),
    statsSuccess: document.getElementById('statsSuccess'),
    statsFailed: document.getElementById('statsFailed'),
    refreshBtn: document.getElementById('refreshBtn'),
    cleanupBtn: document.getElementById('cleanupBtn'),
    filterSelect: document.getElementById('filterSelect'),
    searchInput: document.getElementById('searchInput'),
    historyModal: document.getElementById('historyModal'),
    modalCloseBtn: document.getElementById('modalCloseBtn'),
    modalContent: document.getElementById('modalContent'),
    
    
    // UI elements
    themeToggle: document.getElementById('themeToggle'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    
    // Templates
    audioPlayerTemplate: document.getElementById('audioPlayerTemplate'),
    videoPlayerTemplate: document.getElementById('videoPlayerTemplate')
};

// Video modal elements (will be initialized when needed)
let videoCreationModal = null;
let closeVideoModalBtn = null;
let cancelVideoBtn = null;
let createVideoBtn = null;
let modalTaskId = null;
let modalAudioId = null;
let modalSongTitleContainer = null;
let modalSongTitle = null;
let modalStatusMessage = null;
let modalStatusText = null;
let modalAuthor = null;
let modalDomainName = null;

/**
 * Initialize the history page.
 */
function initializeHistoryPage() {
    console.log('Initializing History page...');
    
    // Initialize components
    initializeComponents();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial history
    historyManager.loadHistory();
    
    console.log('History page initialized successfully.');
}

/**
 * Initialize modular components.
 */
function initializeComponents() {
    // Initialize history manager
    const historyManagerElements = {
        historyContainer: DOM.historyContainer,
        loadingState: DOM.loadingState,
        emptyState: DOM.emptyState,
        errorState: DOM.errorState,
        statsTotal: DOM.statsTotal,
        statsToday: DOM.statsToday,
        statsSuccess: DOM.statsSuccess,
        statsFailed: DOM.statsFailed,
        refreshBtn: DOM.refreshBtn,
        cleanupBtn: DOM.cleanupBtn,
        filterSelect: DOM.filterSelect,
        searchInput: DOM.searchInput,
        historyModal: DOM.historyModal,
        modalCloseBtn: DOM.modalCloseBtn,
        modalContent: DOM.modalContent
    };
    historyManager.initialize(historyManagerElements);
    
    // Set up history manager callbacks
    historyManager.setOnShowEntryDetails(showEntryDetails);
    
    // Initialize audio player component
    if (DOM.audioPlayerTemplate) {
        // Note: audioPlayerComponent needs a container, but we'll create it dynamically in the modal
        // We'll initialize it with a dummy container for now
        const dummyContainer = document.createElement('div');
        audioPlayerComponent.initialize(dummyContainer, DOM.audioPlayerTemplate);
    }
}

/**
 * Set up event listeners.
 */
function setupEventListeners() {
    // Theme toggle
    if (DOM.themeToggle) {
        DOM.themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Mobile menu
    if (DOM.mobileMenuBtn) {
        DOM.mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    
    
    // Video modal event listeners (will be set up when modal is shown)
    initVideoModalElements();
    
    if (closeVideoModalBtn) {
        closeVideoModalBtn.addEventListener('click', closeVideoModal);
    }
    if (cancelVideoBtn) {
        cancelVideoBtn.addEventListener('click', closeVideoModal);
    }
    if (createVideoBtn) {
        createVideoBtn.addEventListener('click', handleModalCreateVideo);
    }
    
    // Close modal when clicking outside
    if (videoCreationModal) {
        videoCreationModal.addEventListener('click', function(e) {
            if (e.target === videoCreationModal) {
                closeVideoModal();
            }
        });
    }
}

/**
 * Show entry details in modal.
 * @param {Object} entry - History entry object
 */
function showEntryDetails(entry) {
    console.log('Showing entry details for:', entry.id);
    
    if (!DOM.historyModal || !DOM.modalContent) {
        console.error('Modal elements not found');
        return;
    }
    
    // Format timestamp
    const timestamp = new Date(entry.timestamp);
    const formattedTime = timestamp.toLocaleString();
    
    // Get data
    const rawData = entry.raw_data || entry.data || {};
    const processedData = entry.processed_data || {};
    const tracks = processedData.tracks || [];
    const isVideoCallback = entry.is_video_callback || false;
    const videoUrl = entry.video_url || processedData.video_url;
    
    // Create modal content
    const modalHTML = `
        <div class="space-y-6">
            <div class="flex items-center justify-between">
                <h3 class="text-lg font-bold text-slate-900 dark:text-white">Callback Details</h3>
                <span class="text-xs text-slate-500">${formattedTime}</span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Task ID</label>
                        <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm break-all">${entry.task_id || 'N/A'}</code>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Entry ID</label>
                        <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm break-all">${entry.id || 'N/A'}</code>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Callback Type</label>
                        <span class="inline-block px-2 py-1 rounded text-sm font-medium
                            ${entry.callback_type === 'complete' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                              entry.callback_type === 'first' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                              entry.callback_type === 'text' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                              entry.callback_type === 'video_complete' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'}">
                            ${entry.callback_type || 'unknown'}
                        </span>
                    </div>
                </div>
                
                <div class="space-y-2">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Status Code</label>
                        <span class="inline-block px-2 py-1 rounded text-sm font-medium
                            ${entry.status_code === 200 || entry.status_code === 0 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                              'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}">
                            ${entry.status_code || 'N/A'}
                        </span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Status</label>
                        <span class="text-sm text-slate-700 dark:text-slate-300">${entry.status || 'unknown'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Type</label>
                        <span class="text-sm text-slate-700 dark:text-slate-300">
                            ${isVideoCallback ? 'Video' : 'Audio'} (${tracks.length || 0} track(s))
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- Content Section (Audio or Video) -->
            <div class="mt-6">
                ${isVideoCallback ? `
                    <!-- Video Section -->
                    <div class="flex items-center gap-2 mb-4">
                        <span class="material-symbols-outlined text-primary">movie</span>
                        <h4 class="font-bold text-slate-900 dark:text-white">Generated Video</h4>
                        <span class="text-xs px-2 py-1 bg-purple-500/10 text-purple-500 rounded-full">Video</span>
                    </div>
                    
                    <div id="videoPlayerContainer" class="space-y-4">
                        <!-- Video player will be dynamically inserted here -->
                    </div>
                ` : `
                    <!-- Audio Section -->
                    <div class="flex items-center gap-2 mb-4">
                        <span class="material-symbols-outlined text-primary">queue_music</span>
                        <h4 class="font-bold text-slate-900 dark:text-white">Generated Songs</h4>
                        <span class="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">${tracks.length} track(s)</span>
                    </div>
                    
                    <div id="audioPlayersContainer" class="space-y-4">
                        <!-- Audio players will be dynamically inserted here -->
                    </div>
                    
                    ${tracks.length === 0 ? `
                        <div class="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded-lg">
                            <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">music_off</span>
                            <p class="text-slate-500 dark:text-slate-400">No audio tracks available for this entry.</p>
                        </div>
                    ` : ''}
                `}
            </div>
            
            <!-- Raw Data Section (Collapsible) -->
            <div class="mt-6">
                <button id="toggleRawData" class="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-white mb-2">
                    <span class="material-symbols-outlined text-sm">expand_more</span>
                    <span class="text-sm font-medium">Raw Data</span>
                </button>
                <div id="rawDataContent" class="hidden">
                    <pre class="text-xs bg-slate-100 dark:bg-slate-800 p-3 rounded max-h-60 overflow-y-auto">${JSON.stringify(rawData, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
    
    DOM.modalContent.innerHTML = modalHTML;
    
    if (isVideoCallback) {
        // Add video player
        const videoPlayerContainer = document.getElementById('videoPlayerContainer');
        if (videoUrl && videoPlayerContainer) {
            const videoPlayer = createVideoPlayerForHistoryEntry(entry, videoUrl);
            if (videoPlayer) {
                videoPlayerContainer.appendChild(videoPlayer);
            }
        } else if (videoPlayerContainer) {
            // No video URL available
            videoPlayerContainer.innerHTML = `
                <div class="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">movie_off</span>
                    <p class="text-slate-500 dark:text-slate-400">Video URL not available for this entry.</p>
                </div>
            `;
        }
    } else {
        // Add audio players for each track
        if (tracks.length > 0) {
            const audioPlayersContainer = document.getElementById('audioPlayersContainer');
            if (audioPlayersContainer) {
                tracks.forEach((track, index) => {
                    // Add the entry's task ID to the track object for video creation
                    const trackWithTaskId = { ...track, task_id: entry.task_id };
                    const audioPlayer = createAudioPlayerForHistory(trackWithTaskId, index + 1);
                    if (audioPlayer) {
                        audioPlayersContainer.appendChild(audioPlayer);
                        // Initialize WaveSurfer now that element is in the DOM
                        if (audioPlayer._wsContainer && audioPlayer._wsAudioUrl) {
                            const wsPlayer = new UnifiedAudioPlayer(audioPlayer._wsContainer, audioPlayer._wsAudioUrl, {
                                height: 48,
                                progressColor: '#6366f1',
                                waveColor: '#94a3b8',
                                onReady: (player) => {
                                    const durationDataEl = audioPlayer.querySelector('[data-track-duration]');
                                    if (durationDataEl) {
                                        const duration = player.getDuration();
                                        const minutes = Math.floor(duration / 60);
                                        const seconds = Math.floor(duration % 60);
                                        durationDataEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                                    }
                                },
                            });
                            audioPlayer._wsPlayer = wsPlayer;
                        }
                    }
                });
            }
        }
    }
    
    // Set up raw data toggle
    const toggleRawDataBtn = document.getElementById('toggleRawData');
    const rawDataContent = document.getElementById('rawDataContent');
    
    if (toggleRawDataBtn && rawDataContent) {
        toggleRawDataBtn.addEventListener('click', () => {
            const isHidden = rawDataContent.classList.contains('hidden');
            rawDataContent.classList.toggle('hidden');
            toggleRawDataBtn.querySelector('.material-symbols-outlined').textContent =
                isHidden ? 'expand_less' : 'expand_more';
        });
    }
    
    // Show modal
    DOM.historyModal.classList.remove('hidden');

    // Trigger resize to help any deferred WaveSurfer instances render
    requestAnimationFrame(() => {
        window.dispatchEvent(new Event('resize'));
    });
}

/**
 * Create an audio player element for a track in history modal.
 * @param {Object} track - Track data object
 * @param {number} trackNumber - Track number
 * @returns {HTMLElement} Audio player element
 */
function createAudioPlayerForHistory(track, trackNumber) {
    const template = DOM.audioPlayerTemplate;
    if (!template) {
        console.error('Audio player template not found');
        return document.createElement('div');
    }
    
    const player = template.content.cloneNode(true);
    const playerElement = player.querySelector('.audio-player');
    
    if (!playerElement) {
        console.error('Could not find .audio-player element in template');
        return document.createElement('div');
    }
    
    // Set track information
    const title = track.title || track.name || `Track ${trackNumber}`;
    const model = track.model || 'unknown';
    
    // Handle tags
    let tags = 'No tags';
    if (track.tags) {
        if (Array.isArray(track.tags)) {
            tags = track.tags.join(', ');
        } else if (typeof track.tags === 'string') {
            tags = track.tags;
        } else {
            tags = String(track.tags);
        }
    }
    
    const prompt = track.prompt || 'No lyrics available';
    const created = track.created_at ? new Date(track.created_at).toLocaleString() : 'N/A';
    
    // Get audio URLs
    const audioUrls = track.audio_urls || {};
    const generatedAudioUrl = audioUrls.generated || audioUrls.audio || '';
    
    // Set text content
    const titleEl = playerElement.querySelector('[data-track-title]');
    const numberEl = playerElement.querySelector('[data-track-number]');
    const modelEl = playerElement.querySelector('[data-track-model]');
    const tagsEl = playerElement.querySelector('[data-track-tags]');
    const promptEl = playerElement.querySelector('[data-track-prompt]');
    const createdEl = playerElement.querySelector('[data-track-created]');
    
    if (titleEl) titleEl.textContent = title;
    if (numberEl) numberEl.textContent = `Track ${trackNumber}`;
    if (modelEl) modelEl.textContent = model;
    if (tagsEl) tagsEl.textContent = tags;
    if (promptEl) {
        // Format lyrics line by line
        if (prompt && prompt !== 'No lyrics available') {
            promptEl.innerHTML = prompt.split('\n').map(line => {
                if (line.trim() === '') return '<br>';
                return `<div class="lyric-line py-0.5 border-b border-slate-100 dark:border-slate-700/50 last:border-b-0 text-xs">${line}</div>`;
            }).join('');
        } else {
            promptEl.textContent = prompt;
        }
    }
    if (createdEl) createdEl.textContent = created;
    
    // Store WaveSurfer data for deferred initialization (after DOM append)
    const wsContainer = playerElement.querySelector('[data-ws-player-container]');
    const durationEl = playerElement.querySelector('[data-track-duration]');
    
    if (generatedAudioUrl && wsContainer) {
        // Defer WaveSurfer init — store URL & container reference on element
        playerElement._wsContainer = wsContainer;
        playerElement._wsAudioUrl = generatedAudioUrl;
    } else {
        // No audio URL available
        if (durationEl) durationEl.textContent = 'N/A';
    }
    
    // Add video button functionality
    const videoBtn = playerElement.querySelector('[data-video-btn]');
    if (videoBtn) {
        videoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleCreateMusicVideoForHistory(track, videoBtn);
        });
    }
    
    return playerElement;
}
