/**
 * Main application module for the Music Cover Generator.
 * Uses modular components for better maintainability and separation of concerns.
 */

// Global application state
const AppState = {
    currentTaskId: null,
    uploadedFileUrl: null,
    currentMode: false,
    currentModel: 'V5',
    isPolling: false,
    pollingTimeout: null,
    currentSourceType: 'upload'
};

// Initialize modular components
let notificationSystem, fileHandler, modeManager, taskManager, audioPlayerComponent, lyricGenerator;

// Define global functions early for onclick handlers
window.setTaskType = function(type) {
    console.log('Early window.setTaskType called with:', type);
    
    // If the full implementation isn't loaded yet, use simple DOM manipulation
    const coverTaskBtn = document.getElementById('coverTaskBtn');
    const extendTaskBtn = document.getElementById('extendTaskBtn');
    const continueAtField = document.getElementById('continueAtField');
    const taskTypeHelp = document.getElementById('taskTypeHelp');
    
    if (type === 'extend') {
        if (coverTaskBtn) coverTaskBtn.classList.remove('active');
        if (extendTaskBtn) extendTaskBtn.classList.add('active');
        if (continueAtField) continueAtField.classList.remove('hidden');
        if (taskTypeHelp) taskTypeHelp.textContent = 'Extend: Continue the music from a specific point.';
    } else {
        if (coverTaskBtn) coverTaskBtn.classList.add('active');
        if (extendTaskBtn) extendTaskBtn.classList.remove('active');
        if (continueAtField) continueAtField.classList.add('hidden');
        if (taskTypeHelp) taskTypeHelp.textContent = 'Cover: Create a new version/remix.';
    }
    
    // If modeManager is available later, it will handle the full logic
    if (window.modeManager && typeof window.modeManager.setTaskType === 'function') {
        window.modeManager.setTaskType(type);
    }
};

function createComponents() {
    let allCriticalComponentsLoaded = true;
    
    // Initialize notification system
    try {
        notificationSystem = window.NotificationSystem || {
            showError: (msg) => console.error('Notification Error:', msg),
            showSuccess: (msg) => console.log('Notification Success:', msg),
            showInfo: (msg) => console.log('Notification Info:', msg),
            showWarning: (msg) => console.warn('Notification Warning:', msg)
        };
    } catch (e) {
        console.error('Failed to init NotificationSystem:', e);
    }

    // Initialize FileHandler
    try {
        if (window.FileHandler) {
            fileHandler = new window.FileHandler();
        } else {
            console.error('FileHandler not available');
            allCriticalComponentsLoaded = false;
        }
    } catch (e) {
        console.error('Failed to init FileHandler:', e);
        allCriticalComponentsLoaded = false;
    }
    
    // Initialize ModeManager
    try {
        if (window.ModeManager) {
            modeManager = new window.ModeManager();
        } else {
            console.error('ModeManager not available');
            allCriticalComponentsLoaded = false;
        }
    } catch (e) {
        console.error('Failed to init ModeManager:', e);
        allCriticalComponentsLoaded = false;
    }
    
    // Initialize TaskManager
    try {
        if (window.TaskManager) {
            taskManager = new window.TaskManager();
        } else {
            console.error('TaskManager not available');
            allCriticalComponentsLoaded = false;
        }
    } catch (e) {
        console.error('Failed to init TaskManager:', e);
        allCriticalComponentsLoaded = false;
    }
    
    // Initialize AudioPlayerComponent (Optional but important)
    try {
        if (window.AudioPlayerComponent) {
            audioPlayerComponent = new window.AudioPlayerComponent();
        } else {
            console.error('AudioPlayerComponent not available');
        }
    } catch (e) {
        console.error('Failed to init AudioPlayerComponent:', e);
    }
    
    // Initialize LyricGenerator (Optional)
    try {
        if (window.LyricGenerator) {
            lyricGenerator = new window.LyricGenerator();
        } else {
            console.log('LyricGenerator not available (optional)');
        }
    } catch (e) {
        console.error('Failed to init LyricGenerator:', e);
    }
    
    return allCriticalComponentsLoaded;
}

// DOM Elements
const DOM = {};

function initializeDOM() {
    // Detect page type
    isMusicGenerator = !!document.getElementById('musicPrompt');

    Object.assign(DOM, {
        // File handling elements
        uploadArea: document.getElementById('uploadArea'),
        audioFileInput: document.getElementById('audioFile'),
        fileInfo: document.getElementById('fileInfo'),
        fileName: document.getElementById('fileName'),
        uploadStatus: document.getElementById('uploadStatus'),
        progressContainer: document.getElementById('progressContainer'),
        progressBar: document.getElementById('progressBar'),
        progressText: document.getElementById('progressText'),
        uploadBtn: document.getElementById('uploadBtn'),
        generateBtn: document.getElementById('generateBtn'),
        audioUrlInput: document.getElementById('audioUrlInput'),
        urlTestBtn: document.getElementById('urlTestBtn'),
        urlTestResult: document.getElementById('urlTestResult'),
        useUrlBtn: document.getElementById('useUrlBtn'),
        sourceInfo: document.getElementById('sourceInfo'),
        sourceType: document.getElementById('sourceType'),
        sourceUrl: document.getElementById('sourceUrl'),
        uploadTab: document.getElementById('uploadTab'),
        urlTab: document.getElementById('urlTab'),
        uploadSection: document.getElementById('uploadSection'),
        urlSection: document.getElementById('urlSection'),
        
        // Mode and model elements
        coverTaskBtn: document.getElementById('coverTaskBtn'),
        extendTaskBtn: document.getElementById('extendTaskBtn'),
        continueAtField: document.getElementById('continueAtField'),
        continueAtInput: document.getElementById('continueAtInput'),
        taskTypeHelp: document.getElementById('taskTypeHelp'),

        simpleModeBtn: document.getElementById('simpleModeBtn'),
        customModeBtn: document.getElementById('customModeBtn'),
        customFields: document.getElementById('customFields'),
        modeHelp: document.getElementById('modeHelp'),
        modelSelect: document.getElementById('modelSelect'),
        promptInput: document.getElementById('promptInput'),
        promptChars: document.getElementById('promptChars'),
        promptMax: document.getElementById('promptMax'),
        styleInput: document.getElementById('styleInput'),
        styleChars: document.getElementById('styleChars'),
        styleMax: document.getElementById('styleMax'),
        titleInput: document.getElementById('titleInput'),
        titleChars: document.getElementById('titleChars'),
        titleMax: document.getElementById('titleMax'),
        instrumentalToggle: document.getElementById('instrumentalToggle'),
        
        // Task status elements
        taskStatus: document.getElementById('taskStatus'),
        taskId: document.getElementById('taskId'),
        statusBadge: document.getElementById('statusBadge'),
        statusProgress: document.getElementById('statusProgress'),
        statusText: document.getElementById('statusText'),
        startTime: document.getElementById('startTime'),
        statusCode: document.getElementById('statusCode'),
        audioId: document.getElementById('audioId'),
        statusMessage: document.getElementById('statusMessage'),
        callbackType: document.getElementById('callbackType'),
        results: document.getElementById('results'),
        refreshStatusBtn: document.getElementById('refreshStatusBtn'),
        
        // Audio player elements
        audioPlayersContainer: document.getElementById('audioPlayersContainer'),
        audioPlayerTemplate: document.getElementById('audioPlayerTemplate'),
        
        // Lyric generator elements
        lyricPrompt: document.getElementById('lyricPrompt'),
        lyricCharCount: document.getElementById('lyricCharCount'),
        generateLyricsBtn: document.getElementById('generateLyricsBtn'),
        lyricsResultsContainer: document.getElementById('lyricsResultsContainer'),
        lyricsResults: document.getElementById('lyricsResults'),
        refreshLyricsBtn: document.getElementById('refreshLyrics'),
        clearLyricsBtn: document.getElementById('clearLyrics'),
        toggleLyricSectionBtn: document.getElementById('toggleLyricSection'),
        lyricSection: document.getElementById('lyricSection'),
        lyricAdvancedBtn: document.getElementById('lyricAdvancedBtn'),
        
        // UI elements
        themeToggle: document.getElementById('themeToggle'),
        mobileMenuBtn: document.getElementById('mobileMenuBtn')
    });
}

// Detect page type
let isMusicGenerator = false;

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
 * Initialize the application.
 */
function initializeApp() {
    console.log('Initializing Music Cover Generator application...');
    
    // Initialize DOM elements first
    initializeDOM();

    // Create component instances first
    if (!createComponents()) {
        console.error('Failed to create components. Application may not work properly.');
        // Continue anyway with fallback behavior
    }
    
    // Initialize modular components (set up DOM elements and event listeners)
    initializeComponents();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize defaults
    initializeDefaults();
    
    console.log('Application initialized successfully.');
}

/**
 * Initialize modular components (second part - setup after component creation).
 */
function initializeComponents() {
    // Initialize file handler if available
    if (fileHandler) {
        const fileHandlerElements = {
        uploadArea: DOM.uploadArea,
        audioFileInput: DOM.audioFileInput,
        fileInfo: DOM.fileInfo,
        fileName: DOM.fileName,
        uploadStatus: DOM.uploadStatus,
        progressContainer: DOM.progressContainer,
        progressBar: DOM.progressBar,
        progressText: DOM.progressText,
        uploadBtn: DOM.uploadBtn,
        generateBtn: DOM.generateBtn,
        audioUrlInput: DOM.audioUrlInput,
        urlTestResult: DOM.urlTestResult,
        useUrlBtn: DOM.useUrlBtn,
        sourceInfo: DOM.sourceInfo,
        sourceType: DOM.sourceType,
        sourceUrl: DOM.sourceUrl,
        uploadTab: DOM.uploadTab,
        urlTab: DOM.urlTab,
            uploadSection: DOM.uploadSection,
            urlSection: DOM.urlSection
        };
        fileHandler.initialize(fileHandlerElements);
    } else {
        console.error('FileHandler not initialized');
    }
    
    // Initialize mode manager if available
    if (modeManager) {
        const modeManagerElements = {
            coverTaskBtn: DOM.coverTaskBtn,
        extendTaskBtn: DOM.extendTaskBtn,
        continueAtField: DOM.continueAtField,
        continueAtInput: DOM.continueAtInput,
        taskTypeHelp: DOM.taskTypeHelp,
        
        simpleModeBtn: DOM.simpleModeBtn,
        customModeBtn: DOM.customModeBtn,
        customFields: DOM.customFields,
        modeHelp: DOM.modeHelp,
        modelSelect: DOM.modelSelect,
        promptInput: DOM.promptInput,
        promptChars: DOM.promptChars,
        promptMax: DOM.promptMax,
        styleInput: DOM.styleInput,
        styleChars: DOM.styleChars,
        styleMax: DOM.styleMax,
        titleInput: DOM.titleInput,
        titleChars: DOM.titleChars,
        titleMax: DOM.titleMax,
            instrumentalToggle: DOM.instrumentalToggle
        };
        modeManager.initialize(modeManagerElements);
    } else {
        console.error('ModeManager not initialized');
    }
    
    // Initialize task manager if available
    if (taskManager) {
        const taskManagerElements = {
            taskStatus: DOM.taskStatus,
        taskId: DOM.taskId,
        statusBadge: DOM.statusBadge,
        statusProgress: DOM.statusProgress,
        statusText: DOM.statusText,
        startTime: DOM.startTime,
        statusCode: DOM.statusCode,
        audioId: DOM.audioId,
        statusMessage: DOM.statusMessage,
        callbackType: DOM.callbackType,
            results: DOM.results,
            refreshStatusBtn: DOM.refreshStatusBtn
        };
        taskManager.initialize(taskManagerElements);
        
        // Set up task manager callbacks
        taskManager.setOnGenerationComplete(handleGenerationComplete);
        taskManager.setOnCallbackInfo(handleCallbackInfo);
        taskManager.setOnCallbackHistory(handleCallbackHistory);
    } else {
        console.error('TaskManager not initialized');
    }
    
    // Initialize audio player component if available
    if (audioPlayerComponent) {
        audioPlayerComponent.initialize(DOM.audioPlayersContainer, DOM.audioPlayerTemplate);
    } else {
        console.error('AudioPlayerComponent not initialized');
    }
    
    // Initialize lyric generator if available
    if (lyricGenerator) {
        const lyricGeneratorElements = {
            lyricPrompt: DOM.lyricPrompt,
            lyricCharCount: DOM.lyricCharCount,
            generateLyricsBtn: DOM.generateLyricsBtn,
            lyricsResultsContainer: DOM.lyricsResultsContainer,
            lyricsResults: DOM.lyricsResults,
            refreshLyricsBtn: DOM.refreshLyricsBtn,
            clearLyricsBtn: DOM.clearLyricsBtn,
            toggleLyricSectionBtn: DOM.toggleLyricSectionBtn,
            lyricSection: DOM.lyricSection,
            lyricAdvancedBtn: DOM.lyricAdvancedBtn
        };
        lyricGenerator.initialize(lyricGeneratorElements);
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
    
    // URL test button
    if (DOM.urlTestBtn) {
        DOM.urlTestBtn.addEventListener('click', () => fileHandler.testAudioUrl());
    }
    
    // Use URL button
    if (DOM.useUrlBtn) {
        DOM.useUrlBtn.addEventListener('click', () => fileHandler.useAudioUrl());
    }
    
    // Upload button
    if (DOM.uploadBtn) {
        DOM.uploadBtn.addEventListener('click', () => fileHandler.uploadFile());
    }
    
    // Generate button
    if (DOM.generateBtn) {
        DOM.generateBtn.addEventListener('click', generateCover);
    }
    
    // Source type tabs
    if (DOM.uploadTab && DOM.urlTab) {
        DOM.uploadTab.addEventListener('click', () => fileHandler.setSourceType('upload'));
        DOM.urlTab.addEventListener('click', () => fileHandler.setSourceType('url'));
    }
    
    // Video modal event listeners
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
 * Initialize default values.
 */
function initializeDefaults() {
    // Set initial source type
    if (DOM.uploadTab && DOM.urlTab) {
        fileHandler.setSourceType('upload');
    }
}

/**
 * Generate a music cover.
 */
async function generateCover() {
    if (DOM.generateBtn.disabled && DOM.generateBtn.innerHTML.includes('sync')) return;
    
    // Validate inputs
    const validation = modeManager.validateInputs();
    if (!validation.isValid) {
        notificationSystem.showError(validation.message);
        return;
    }
    
    // Prepare request data based on page type
    let requestData;
    let endpoint;
    
    if (isMusicGenerator) {
        // Music generator page: check if audio source is available
        if (fileHandler.hasSource()) {
            // If audio source is available, use cover generation with upload
            requestData = {
                upload_url: fileHandler.getUploadedFileUrl(),
                ...modeManager.getGenerationParameters()
            };
            endpoint = '/api/generate-cover'; // Use cover generation for audio-to-music
        } else {
            // No audio source: use text-to-music generation
            requestData = modeManager.getGenerationParameters();
            endpoint = '/api/generate-music-direct';
        }
    } else {
        // Cover/Extend generation requires an audio source
        if (!fileHandler.hasSource()) {
            notificationSystem.showError('Please select an audio source first (upload file or enter URL)');
            DOM.generateBtn.disabled = true;
            DOM.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate';
            return;
        }
        requestData = {
            upload_url: fileHandler.getUploadedFileUrl(),
            ...modeManager.getGenerationParameters()
        };
        
        // Determine endpoint based on task type
        if (requestData.task_type === 'extend') {
            endpoint = '/api/generate-extend';
        } else {
            endpoint = '/api/generate-cover';
        }
    }
    
    // Update UI state
    DOM.generateBtn.disabled = true;
    DOM.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Generating...';
    
    // Set timeout for the request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await response.json();
        
        if (response.ok) {
            // Handle both taskId (camelCase) and task_id (snake_case) from API responses
            const extractedTaskId = data.data?.taskId || data.data?.task_id;
            if (data.code === 200 && data.data && extractedTaskId) {
                AppState.currentTaskId = extractedTaskId;
                notificationSystem.showSuccess(isMusicGenerator ? 'Music generation started! Tracking task...' : 'Cover generation started! Tracking task...');
                
                // Start task tracking
                taskManager.setCurrentTask(extractedTaskId);
            } else {
                throw new Error(data.msg || 'Generation failed');
            }
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        notificationSystem.showError(`Generation failed: ${error.message}`);
        DOM.generateBtn.disabled = false;
        DOM.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> ' + (isMusicGenerator ? 'Generate Music' : 'Generate Music Cover');
    }
}

/**
 * Handle generation completion.
 * @param {Array} sunoData - Array of generated song data
 */
function handleGenerationComplete(sunoData) {
    // Display audio players with video buttons
    audioPlayerComponent.displayAllAudioPlayers(
        sunoData, 
        taskManager.getCurrentTaskId(), 
        handleCreateMusicVideo
    );
    
    // Show results section
    if (DOM.results) {
        DOM.results.classList.remove('hidden');
    }
    
    notificationSystem.showSuccess(`Cover generation completed! ${sunoData.length} song(s) generated.`);
}

/**
 * Handle callback information.
 * @param {Object} callbackData - Callback data
 */
function handleCallbackInfo(callbackData) {
    audioPlayerComponent.displayCallbackInfo(callbackData);
}

/**
 * Handle callback history.
 * @param {Array} callbacks - Array of callback objects
 */
function handleCallbackHistory(callbacks) {
    audioPlayerComponent.showCallbackHistorySummary(callbacks);
}

/**
 * Handle music video creation.
 * @param {Object} song - Song data object
 */
function handleCreateMusicVideo(song) {
    console.log('handleCreateMusicVideo called with song:', song);
    
    // Check for image URL using all possible property names
    const hasImageUrl = song.image_url ||
                       song.imageUrl ||
                       (song.image_urls && song.image_urls.generated) ||
                       song.source_image_url ||
                       song.sourceImageUrl;
    
    if (!song.id || !hasImageUrl) {
        console.error('Cannot create music video: Missing audio ID or image URL', song);
        notificationSystem.showError('Cannot create music video: Missing audio ID or image URL');
        return;
    }
    
    // Show the modal dialog
    console.log('Calling showVideoModal for song:', song.title);
    showVideoModal(song);
}

// Video modal functions
function initVideoModalElements() {
    if (!videoCreationModal) {
        videoCreationModal = document.getElementById('videoCreationModal');
        closeVideoModalBtn = document.getElementById('closeVideoModalBtn');
        cancelVideoBtn = document.getElementById('cancelVideoBtn');
        createVideoBtn = document.getElementById('createVideoBtn');
        modalTaskId = document.getElementById('modalTaskId');
        modalAudioId = document.getElementById('modalAudioId');
        modalSongTitleContainer = document.getElementById('modalSongTitleContainer');
        modalSongTitle = document.getElementById('modalSongTitle');
        modalStatusMessage = document.getElementById('modalStatusMessage');
        modalStatusText = document.getElementById('modalStatusText');
        modalAuthor = document.getElementById('modalAuthor');
        modalDomainName = document.getElementById('modalDomainName');
    }
}

function showVideoModal(song) {
    console.log('showVideoModal called with song:', song);
    
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!videoCreationModal || !modalTaskId || !modalAudioId) {
        console.error('Modal elements not found.');
        return;
    }
    
    // Get the current task ID from the global variable or from the song
    const taskId = AppState.currentTaskId || song.task_id;
    const audioId = song.id;
    
    console.log('Task ID:', taskId, 'Audio ID:', audioId);
    
    if (!taskId || !audioId) {
        console.error('Missing task ID or audio ID:', { taskId, audioId });
        notificationSystem.showError('Cannot create music video: Missing task ID or audio ID');
        return;
    }
    
    // Populate modal fields
    modalTaskId.value = taskId;
    modalAudioId.value = audioId;
    
    // Show song title if available
    if (song.title) {
        modalSongTitle.textContent = song.title;
        modalSongTitleContainer.classList.remove('hidden');
        console.log('Song title shown:', song.title);
    } else {
        modalSongTitleContainer.classList.add('hidden');
    }
    
    // Set empty values for author and domain name (user will fill them)
    if (modalAuthor) {
        modalAuthor.value = '';
    }
    if (modalDomainName) {
        modalDomainName.value = '';
    }
    
    // Hide status message
    modalStatusMessage.classList.add('hidden');
    
    // Store the current song data on the create button
    createVideoBtn.dataset.song = JSON.stringify(song);
    createVideoBtn.disabled = false;
    createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">movie</span> Create Video';
    
    // Show modal
    console.log('Showing modal...');
    videoCreationModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    console.log('Modal should be visible now');
}

function closeVideoModal() {
    initVideoModalElements();
    if (videoCreationModal) {
        videoCreationModal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

async function handleModalCreateVideo() {
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!createVideoBtn || !createVideoBtn.dataset.song) {
        notificationSystem.showError('No song data available');
        return;
    }
    
    try {
        const song = JSON.parse(createVideoBtn.dataset.song);
        
        // Check for image URL using all possible property names
        const hasImageUrl = song.image_url ||
                           song.imageUrl ||
                           (song.image_urls && song.image_urls.generated) ||
                           song.source_image_url ||
                           song.sourceImageUrl;
        
        // Validate required fields
        if (!song.id || !hasImageUrl) {
            notificationSystem.showError('Cannot create music video: Missing audio ID or image URL');
            closeVideoModal();
            return;
        }
        
        const taskId = AppState.currentTaskId || song.task_id;
        if (!taskId) {
            notificationSystem.showError('Cannot create music video: Missing task ID');
            closeVideoModal();
            return;
        }
        
        // Show loading state in modal
        createVideoBtn.disabled = true;
        createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">sync</span> Creating...';
        
        // Show status message
        if (modalStatusText) {
            modalStatusText.textContent = 'Starting video generation...';
        }
        if (modalStatusMessage) {
            modalStatusMessage.classList.remove('hidden');
        }
        
        // Call the actual video creation function
        await createVideoFromModal(taskId, song);
        
    } catch (error) {
        console.error('Error parsing song data:', error);
        notificationSystem.showError('Failed to parse song data');
        closeVideoModal();
    }
}

async function createVideoFromModal(taskId, song) {
    try {
        // Initialize modal elements if needed
        initVideoModalElements();
        
        // Get values from input fields
        const author = modalAuthor ? modalAuthor.value.trim() : 'Music Cover Generator';
        const domainName = modalDomainName ? modalDomainName.value.trim() : (window.location.hostname || 'music.example.com');
        
        // Request video generation
        const response = await fetch('/api/generate-music-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                audio_id: song.id,
                author: author,
                domain_name: domainName
            })
        });
        
        const data = await response.json();
        
        // Check for success - accept either code 0 or 200 (based on API documentation)
        // Handle both taskId (camelCase) and task_id (snake_case) from API responses
        const videoTaskId = data.data?.taskId || data.data?.task_id;
        const isSuccess = response.ok && data.data && videoTaskId && (data.code === 0 || data.code === 200);
        
        if (isSuccess) {
            // Update modal status
            modalStatusText.textContent = 'Video generation started! Task ID: ' + videoTaskId;
            modalStatusMessage.classList.remove('hidden');
            
            // Close modal after a short delay
            setTimeout(() => {
                closeVideoModal();
                notificationSystem.showSuccess('Music video generation started! Tracking progress...');
                
                // Note: Video player creation and polling would be implemented here
                // createVideoPlayer(song, videoTaskId);
                // pollVideoStatus(videoTaskId, song);
                
            }, 1500);
            
        } else {
            throw new Error(data.msg || `Video generation failed (code: ${data.code})`);
        }
    } catch (error) {
        console.error('Video creation error:', error);
        if (modalStatusText) {
            modalStatusText.textContent = 'Error: ' + error.message;
        }
        if (modalStatusMessage) {
            modalStatusMessage.classList.remove('hidden');
        }
        
        // Reset button state
        if (createVideoBtn) {
            createVideoBtn.disabled = false;
            createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">movie</span> Create Video';
        }
        
        // Show error notification
        setTimeout(() => {
            notificationSystem.showError(`Failed to create music video: ${error.message}`);
        }, 500);
    }
}

/**
 * Toggle theme between light and dark mode.
 */
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');
    if (isDark) {
        html.classList.remove('dark');
        if (DOM.themeToggle) {
            DOM.themeToggle.innerHTML = '<span class="material-symbols-outlined">light_mode</span>';
        }
    } else {
        html.classList.add('dark');
        if (DOM.themeToggle) {
            DOM.themeToggle.innerHTML = '<span class="material-symbols-outlined">dark_mode</span>';
        }
    }
}

/**
 * Toggle mobile menu visibility.
 */
function toggleMobileMenu() {
    const sidebar = document.querySelector('aside');
    if (sidebar) {
        sidebar.classList.toggle('hidden');
        sidebar.classList.toggle('md:flex');
    }
}

/**
 * Initialize the application when DOM is loaded.
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Export for testing or module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AppState,
        DOM,
        initializeApp,
        generateCover,
        handleCreateMusicVideo,
        toggleTheme,
        toggleMobileMenu
    };
} else {
    // Make functions available globally if needed
    window.MusicCoverGenerator = {
        initializeApp,
        generateCover,
        handleCreateMusicVideo,
        toggleTheme,
        toggleMobileMenu
    };
}

// Global functions for inline onclick handlers
function uploadFile() {
    if (fileHandler && typeof fileHandler.uploadFile === 'function') {
        fileHandler.uploadFile();
    } else {
        console.error('FileHandler not initialized or uploadFile method not available');
    }
}

function testAudioUrl() {
    if (fileHandler && typeof fileHandler.testAudioUrl === 'function') {
        fileHandler.testAudioUrl();
    } else {
        console.error('FileHandler not initialized or testAudioUrl method not available');
    }
}

function useAudioUrl() {
    if (fileHandler && typeof fileHandler.useAudioUrl === 'function') {
        fileHandler.useAudioUrl();
    } else {
        console.error('FileHandler not initialized or useAudioUrl method not available');
    }
}

function setSourceType(type) {
    if (fileHandler && typeof fileHandler.setSourceType === 'function') {
        fileHandler.setSourceType(type);
    } else {
        console.error('FileHandler not initialized or setSourceType method not available');
    }
}

function setMode(mode) {
    if (modeManager && typeof modeManager.setMode === 'function') {
        modeManager.setMode(mode);
    } else {
        console.error('ModeManager not initialized or setMode method not available');
    }
}

// setTaskType function is now defined at the top as window.setTaskType for early availability

function clearAudioSource() {
    if (fileHandler && typeof fileHandler.clearAudioSource === 'function') {
        fileHandler.clearAudioSource();
    } else {
        console.error('FileHandler not initialized or clearAudioSource method not available');
    }
}

function refreshTaskStatus() {
    if (taskManager && typeof taskManager.refreshTaskStatus === 'function') {
        taskManager.refreshTaskStatus();
    } else {
        console.error('TaskManager not initialized or refreshTaskStatus method not available');
    }
}

// Explicitly expose functions to window to ensure HTML onclick attributes can find them
// regardless of scope or module mode
window.uploadFile = uploadFile;
window.testAudioUrl = testAudioUrl;
window.useAudioUrl = useAudioUrl;
window.setSourceType = setSourceType;
window.setMode = setMode;
// window.setTaskType is already defined at the top of the file for early availability
window.clearAudioSource = clearAudioSource;
window.refreshTaskStatus = refreshTaskStatus;

function handleFileSelect(event) {
    if (fileHandler && typeof fileHandler.handleFileSelect === 'function') {
        fileHandler.handleFileSelect(event);
    } else {
        console.log('File selected but FileHandler not available');
        // Fallback: show basic file info
        const input = event.target;
        if (input.files && input.files.length > 0) {
            const fileName = input.files[0].name;
            const fileInfo = document.getElementById('fileInfo');
            const fileNameSpan = document.getElementById('fileName');
            if (fileNameSpan) fileNameSpan.textContent = fileName;
            if (fileInfo) fileInfo.classList.remove('hidden');
        }
    }
}
window.handleFileSelect = handleFileSelect;

// Add onchange handler for file input as fallback
document.addEventListener('DOMContentLoaded', function() {
    // Add inline onchange handler to file input as backup
    const audioFileInput = document.getElementById('audioFile');
    if (audioFileInput) {
        audioFileInput.addEventListener('change', handleFileSelect);
    }
});
