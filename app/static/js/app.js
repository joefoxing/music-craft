// Global variables
let currentTaskId = null;
let uploadedFileUrl = null;
let currentMode = false;
let currentModel = 'V5';
let isPolling = false;
let pollingTimeout = null;
let currentSourceType = 'upload';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const audioFileInput = document.getElementById('audioFile');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const uploadStatus = document.getElementById('uploadStatus');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const uploadBtn = document.getElementById('uploadBtn');
const generateBtn = document.getElementById('generateBtn');
const modelSelect = document.getElementById('modelSelect');
const promptInput = document.getElementById('promptInput');
const promptChars = document.getElementById('promptChars');
const promptMax = document.getElementById('promptMax');
const customFields = document.getElementById('customFields');
const styleInput = document.getElementById('styleInput');
const styleChars = document.getElementById('styleChars');
const styleMax = document.getElementById('styleMax');
const titleInput = document.getElementById('titleInput');
const titleChars = document.getElementById('titleChars');
const titleMax = document.getElementById('titleMax');
const instrumentalToggle = document.getElementById('instrumentalToggle');
const taskStatus = document.getElementById('taskStatus');
const taskId = document.getElementById('taskId');
const statusBadge = document.getElementById('statusBadge');
const statusProgress = document.getElementById('statusProgress');
const statusText = document.getElementById('statusText');
const startTime = document.getElementById('startTime');
const statusCode = document.getElementById('statusCode');
const audioId = document.getElementById('audioId');
const statusMessage = document.getElementById('statusMessage');
const callbackType = document.getElementById('callbackType');
const results = document.getElementById('results');

// New DOM Elements
const uploadTab = document.getElementById('uploadTab');
const urlTab = document.getElementById('urlTab');
const uploadSection = document.getElementById('uploadSection');
const urlSection = document.getElementById('urlSection');
const audioUrlInput = document.getElementById('audioUrlInput');
const urlTestBtn = document.getElementById('urlTestBtn');
const urlTestResult = document.getElementById('urlTestResult');
const useUrlBtn = document.getElementById('useUrlBtn');
const sourceInfo = document.getElementById('sourceInfo');
const sourceType = document.getElementById('sourceType');
const sourceUrl = document.getElementById('sourceUrl');
const themeToggle = document.getElementById('themeToggle');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const simpleModeBtn = document.getElementById('simpleModeBtn');
const customModeBtn = document.getElementById('customModeBtn');
const refreshStatusBtn = document.getElementById('refreshStatusBtn');

// Video Creation Modal Elements (will be initialized when needed)
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

// Function to initialize modal elements (call this before using them)
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

// Initialize
if (promptMax) promptMax.textContent = '500';
if (styleMax) styleMax.textContent = '200';
if (titleMax) titleMax.textContent = '80';

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Only add event listeners if elements exist (for cover-generator page)
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
    }
    if (audioFileInput) {
        audioFileInput.addEventListener('change', handleFileSelect);
    }
    if (modelSelect) {
        modelSelect.addEventListener('change', updateModelLimits);
    }
    if (promptInput) {
        promptInput.addEventListener('input', updatePromptCounter);
    }
    if (styleInput) {
        styleInput.addEventListener('input', updateStyleCounter);
    }
    if (titleInput) {
        titleInput.addEventListener('input', updateTitleCounter);
    }
    if (audioUrlInput) {
        audioUrlInput.addEventListener('input', function() {
            if (urlTestResult) urlTestResult.classList.add('hidden');
            if (useUrlBtn) useUrlBtn.disabled = !this.value.trim();
        });
    }
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    // Mobile menu handled by sidebar.js
    
    // Video modal event listeners - initialize elements first
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
    
    // Only run page-specific initialization if elements exist
    if (modelSelect) {
        updateModelLimits();
    }
    if (promptInput) {
        updatePromptCounter();
    }
    if (styleInput) {
        updateStyleCounter();
    }
    if (titleInput) {
        updateTitleCounter();
    }
    if (uploadTab && urlTab) {
        setSourceType('upload');
    }

    // Event delegation for dynamically added "Add" buttons
    document.body.addEventListener('click', function(event) {
        // Use .closest() to handle clicks on child elements (like the span or icon)
        const button = event.target.closest('.action-btn');
        if (button) {
            const songId = button.dataset.songId; // Assuming the button has data-song-id attribute
            
            console.log(`Add button clicked for Song ID: ${songId}`);
            
            // Prevent multiple clicks
            if (button.disabled) {
                return;
            }
            button.disabled = true;
            button.textContent = 'Adding...';

            // --- Placeholder for actual "add song" logic ---
            // Example:
            // addSongToPlaylist(songId)
            //     .then(() => {
            //         button.textContent = 'Added';
            //         button.classList.add('btn-success');
            //     })
            //     .catch((error) => {
            //         console.error('Failed to add song:', error);
            //         button.disabled = false;
            //         button.textContent = 'Add';
            //         showError('Failed to add song. Please try again.');
            //     });
            
            // For demonstration, we'll just simulate a success state
            setTimeout(() => {
                button.textContent = 'Added';
                 button.classList.add('btn-success');
            }, 1000);
        }
    });
});

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');
    if (isDark) {
        html.classList.remove('dark');
        themeToggle.innerHTML = '<span class="material-symbols-outlined">light_mode</span>';
    } else {
        html.classList.add('dark');
        themeToggle.innerHTML = '<span class="material-symbols-outlined">dark_mode</span>';
    }
}

// Drag and drop
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.style.borderColor = '#4f46e5';
    uploadArea.style.background = '#e0e7ff';
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.style.borderColor = '#cbd5e1';
    uploadArea.style.background = '#f1f5f9';
}

function handleDrop(e) {
    e.preventDefault();
    handleDragLeave(e);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {
    const allowedTypes = ['mp3', 'wav', 'ogg', 'm4a', 'flac'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        showError(`File type .${fileExtension} not allowed. Please upload: ${allowedTypes.join(', ')}`);
        return;
    }
    if (file.size > 100 * 1024 * 1024) {
        showError('File size exceeds 100MB limit');
        return;
    }
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    uploadStatus.textContent = 'Ready to upload';
    uploadBtn.disabled = false;
    // Store the file for upload (don't try to set files property which is read-only)
    window.currentFile = file; // Store globally for uploadFile function
}

// Source selection
function setSourceType(type) {
    currentSourceType = type;
    if (type === 'upload') {
        uploadTab.classList.add('active');
        urlTab.classList.remove('active');
        uploadSection.classList.remove('hidden');
        urlSection.classList.add('hidden');
    } else {
        uploadTab.classList.remove('active');
        urlTab.classList.add('active');
        uploadSection.classList.add('hidden');
        urlSection.classList.remove('hidden');
    }
    if (uploadedFileUrl) clearAudioSource();
}

// Test URL
async function testAudioUrl() {
    const url = audioUrlInput.value.trim();
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    try {
        new URL(url);
    } catch (e) {
        showError('Invalid URL format. Please enter a valid URL starting with http:// or https://');
        return;
    }
    urlTestBtn.disabled = true;
    urlTestBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Testing...';
    urlTestResult.classList.add('hidden');
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        const response = await fetch(url, { method: 'HEAD', mode: 'cors', signal: controller.signal });
        clearTimeout(timeoutId);
        if (response.ok) {
            urlTestResult.textContent = '✓ URL accessible';
            urlTestResult.className = 'test-result success';
            urlTestResult.classList.remove('hidden');
            useUrlBtn.disabled = false;
            showSuccess('URL is accessible and ready to use');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        let errorMessage = `URL test failed: ${error.message}`;
        if (error.name === 'AbortError') {
            errorMessage = 'URL test timeout: The server took too long to respond.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'URL test failed: Could not access the URL. Check CORS settings or try a different URL.';
        } else if (error.message.includes('403') || error.message.includes('404')) {
            errorMessage = 'URL test failed: File not accessible (403/404). Make sure the file is publicly accessible.';
        }
        urlTestResult.textContent = '✗ URL not accessible';
        urlTestResult.className = 'test-result error';
        urlTestResult.classList.remove('hidden');
        showError(errorMessage);
    } finally {
        urlTestBtn.disabled = false;
        urlTestBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_arrow</span> Test URL';
    }
}

// Use URL
function useAudioUrl() {
    const url = audioUrlInput.value.trim();
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    uploadedFileUrl = url;
    sourceType.textContent = 'Public URL';
    sourceUrl.textContent = url;
    sourceInfo.classList.remove('hidden');
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
    showSuccess('Audio URL set successfully! Ready to generate cover.');
}

// Clear source
function clearAudioSource() {
    uploadedFileUrl = null;
    window.currentFile = null;
    fileInfo.classList.add('hidden');
    progressContainer.classList.add('hidden');
    uploadBtn.disabled = false;
    audioFileInput.value = '';
    audioUrlInput.value = '';
    urlTestResult.classList.add('hidden');
    useUrlBtn.disabled = true;
    sourceInfo.classList.add('hidden');
    generateBtn.disabled = true;
    showSuccess('Audio source cleared. Please select a new source.');
}

// Video Creation Modal Functions
function showVideoModal(song) {
    console.log('showVideoModal called with song:', song);
    
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!videoCreationModal || !modalTaskId || !modalAudioId) {
        console.error('Modal elements not found. videoCreationModal:', videoCreationModal, 'modalTaskId:', modalTaskId, 'modalAudioId:', modalAudioId);
        console.error('This usually happens when the modal HTML is not in the DOM or has different IDs');
        return;
    }
    
    // Get the current task ID from the global variable or from the song
    const taskId = currentTaskId || song.task_id;
    const audioId = song.id;
    
    console.log('Task ID:', taskId, 'Audio ID:', audioId);
    
    if (!taskId || !audioId) {
        console.error('Missing task ID or audio ID:', { taskId, audioId });
        showError('Cannot create music video: Missing task ID or audio ID');
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

function handleModalCreateVideo() {
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!createVideoBtn || !createVideoBtn.dataset.song) {
        showError('No song data available');
        return;
    }
    
    try {
        const song = JSON.parse(createVideoBtn.dataset.song);
        
        // Check for image URL using all possible property names (similar to displayAllAudioPlayers)
        const hasImageUrl = song.image_url ||
                           song.imageUrl ||
                           (song.image_urls && song.image_urls.generated) ||
                           song.source_image_url ||
                           song.sourceImageUrl;
        
        // Validate required fields
        if (!song.id || !hasImageUrl) {
            showError('Cannot create music video: Missing audio ID or image URL');
            closeVideoModal();
            return;
        }
        
        const taskId = currentTaskId || song.task_id;
        if (!taskId) {
            showError('Cannot create music video: Missing task ID');
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
        createVideoFromModal(taskId, song);
        
    } catch (error) {
        console.error('Error parsing song data:', error);
        showError('Failed to parse song data');
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
                showSuccess('Music video generation started! Tracking progress...');
                
                // Create and display video player
                createVideoPlayer(song, videoTaskId);
                
                // Start polling for video status
                pollVideoStatus(videoTaskId, song);
            }, 1500);
            
        } else {
            throw new Error(data.msg || `Video generation failed (code: ${data.code})`);
        }
    } catch (error) {
        console.error('Video creation error:', error);
        modalStatusText.textContent = 'Error: ' + error.message;
        modalStatusMessage.classList.remove('hidden');
        
        // Reset button state
        createVideoBtn.disabled = false;
        createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">movie</span> Create Video';
        
        // Show error notification
        setTimeout(() => {
            showError(`Failed to create music video: ${error.message}`);
        }, 500);
    }
}

// Upload file
async function uploadFile() {
    const file = window.currentFile || audioFileInput.files[0];
    if (!file) {
        showError('No file selected');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    progressContainer.classList.remove('hidden');
    uploadBtn.disabled = true;
    uploadStatus.textContent = 'Uploading...';
    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.success) {
            // The file_url is inside data.data
            const fileUrl = data.data?.file_url;
            if (!fileUrl) {
                throw new Error('Server did not return file URL');
            }
            
            uploadedFileUrl = fileUrl;
            uploadStatus.textContent = 'Upload successful!';
            uploadStatus.style.color = '#10b981';
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            sourceType.textContent = 'Uploaded File';
            sourceUrl.textContent = fileUrl;
            sourceInfo.classList.remove('hidden');
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
            showSuccess('File uploaded successfully! Ready to generate cover.');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        uploadStatus.textContent = 'Upload failed';
        uploadStatus.style.color = '#ef4444';
        showError(`Upload failed: ${error.message}`);
        uploadBtn.disabled = false;
    }
}

// Set mode
function setMode(isCustom) {
    currentMode = isCustom;
    const simpleModeBtn = document.getElementById('simpleModeBtn');
    const customModeBtn = document.getElementById('customModeBtn');
    const modeHelp = document.getElementById('modeHelp');
    if (isCustom) {
        simpleModeBtn.classList.remove('active');
        customModeBtn.classList.add('active');
        customFields.classList.remove('hidden');
        modeHelp.textContent = 'Custom Mode: Full control over style, title, and lyrics.';
        updatePromptMaxForModel();
    } else {
        simpleModeBtn.classList.add('active');
        customModeBtn.classList.remove('active');
        customFields.classList.add('hidden');
        modeHelp.textContent = 'Simple Mode: Just provide a prompt, lyrics will be auto-generated.';
        promptMax.textContent = '500';
        updatePromptCounter();
    }
}

// Update model limits
function updateModelLimits() {
    currentModel = modelSelect.value;
    const limits = {
        'V5': { prompt: 5000, style: 1000, title: 100 },
        'V4_5PLUS': { prompt: 5000, style: 1000, title: 100 },
        'V4_5': { prompt: 5000, style: 1000, title: 100 },
        'V4_5ALL': { prompt: 5000, style: 1000, title: 80 },
        'V4': { prompt: 3000, style: 200, title: 80 }
    };
    const modelLimits = limits[currentModel];
    if (currentMode) {
        promptMax.textContent = modelLimits.prompt;
        styleMax.textContent = modelLimits.style;
        titleMax.textContent = modelLimits.title;
    } else {
        promptMax.textContent = '500';
    }
    updatePromptCounter();
    updateStyleCounter();
    updateTitleCounter();
}

function updatePromptMaxForModel() {
    const limits = {
        'V5': 5000,
        'V4_5PLUS': 5000,
        'V4_5': 5000,
        'V4_5ALL': 5000,
        'V4': 3000
    };
    promptMax.textContent = limits[currentModel];
    updatePromptCounter();
}

// Character counters
function updatePromptCounter() {
    const length = promptInput.value.length;
    const max = parseInt(promptMax.textContent);
    promptChars.textContent = length;
    if (length > max) {
        promptChars.style.color = '#ef4444';
    } else if (length > max * 0.8) {
        promptChars.style.color = '#f59e0b';
    } else {
        promptChars.style.color = '#64748b';
    }
}

function updateStyleCounter() {
    const length = styleInput.value.length;
    const max = parseInt(styleMax.textContent);
    styleChars.textContent = length;
    if (length > max) {
        styleChars.style.color = '#ef4444';
    } else if (length > max * 0.8) {
        styleChars.style.color = '#f59e0b';
    } else {
        styleChars.style.color = '#64748b';
    }
}

function updateTitleCounter() {
    const length = titleInput.value.length;
    const max = parseInt(titleMax.textContent);
    titleChars.textContent = length;
    if (length > max) {
        titleChars.style.color = '#ef4444';
    } else if (length > max * 0.8) {
        titleChars.style.color = '#f59e0b';
    } else {
        titleChars.style.color = '#64748b';
    }
}

// Generate cover
async function generateCover() {
    if (generateBtn.disabled && generateBtn.innerHTML.includes('sync')) return;
    if (!uploadedFileUrl) {
        showError('Please select an audio source first (upload file or enter URL)');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
        return;
    }
    if (!promptInput.value.trim()) {
        showError('Please enter a prompt');
        return;
    }
    const promptLength = promptInput.value.length;
    const promptMaxLength = parseInt(promptMax.textContent);
    if (promptLength > promptMaxLength) {
        showError(`Prompt exceeds ${promptMaxLength} character limit`);
        return;
    }
    if (currentMode) {
        const styleLength = styleInput.value.length;
        const styleMaxLength = parseInt(styleMax.textContent);
        const titleLength = titleInput.value.length;
        const titleMaxLength = parseInt(titleMax.textContent);
        if (!styleInput.value.trim()) {
            showError('Please enter a style for custom mode');
            return;
        }
        if (!titleInput.value.trim()) {
            showError('Please enter a title for custom mode');
            return;
        }
        if (styleLength > styleMaxLength) {
            showError(`Style exceeds ${styleMaxLength} character limit`);
            return;
        }
        if (titleLength > titleMaxLength) {
            showError(`Title exceeds ${titleMaxLength} character limit`);
            return;
        }
    }
    const requestData = {
        upload_url: uploadedFileUrl,
        prompt: promptInput.value.trim(),
        custom_mode: currentMode,
        instrumental: instrumentalToggle.checked,
        model: currentModel
    };
    if (currentMode) {
        requestData.style = styleInput.value.trim();
        requestData.title = titleInput.value.trim();
        const vocalGender = document.getElementById('vocalGender')?.value;
        const negativeTags = document.getElementById('negativeTags')?.value;
        if (vocalGender) requestData.vocal_gender = vocalGender;
        if (negativeTags) requestData.negative_tags = negativeTags;
    }
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Generating...';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);
    try {
        const response = await fetch('/api/generate-cover', {
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
                currentTaskId = extractedTaskId;
                showSuccess('Cover generation started! Tracking task...');
                taskId.textContent = currentTaskId;
                startTime.textContent = new Date().toLocaleTimeString();
                taskStatus.classList.remove('hidden');
                pollTaskStatus();
            } else {
                throw new Error(data.msg || 'Generation failed');
            }
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showError(`Generation failed: ${error.message}`);
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
    }
}

// Show error message
function showError(message) {
    console.error('Error:', message);
    // Create or use a notification system
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md';
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="material-symbols-outlined mr-2">error</span>
            <span class="font-medium">${message}</span>
            <button class="ml-auto text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Show success message
function showSuccess(message) {
    console.log('Success:', message);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md';
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="material-symbols-outlined mr-2">check_circle</span>
            <span class="font-medium">${message}</span>
            <button class="ml-auto text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Poll task status with enhanced callback data handling
function pollTaskStatus() {
    if (!currentTaskId || isPolling) return;
    
    isPolling = true;
    const pollInterval = 5000; // 5 seconds
    
    const poll = async () => {
        try {
            const response = await fetch(`/api/task-status/${currentTaskId}`);
            const result = await response.json();
            
            if (response.ok) {
                // Extract data from the API response structure
                const data = result.data || {};
                const status = data.status || 'Unknown';
                const message = result.msg || '';
                const code = result.code || '';
                
                // Update status display
                statusBadge.textContent = status;
                statusText.textContent = message;
                statusCode.textContent = code;
                statusMessage.textContent = message;
                
                // Update progress based on status
                let progressValue = 0;
                if (status === 'PENDING') progressValue = 25;
                else if (status === 'TEXT_SUCCESS') progressValue = 40;
                else if (status === 'GENERATE_AUDIO_FAILED') progressValue = 50;
                else if (status === 'SUCCESS') progressValue = 100;
                else if (status === 'FAILED') progressValue = 100;
                
                statusProgress.value = progressValue;
                
                // Update other fields
                taskId.textContent = currentTaskId;
                audioId.textContent = data.taskId || '';
                callbackType.textContent = data.type || '';
                
                // Check if task is complete
                if (status === 'SUCCESS' || status === 'FAILED' || status === 'GENERATE_AUDIO_FAILED') {
                    isPolling = false;
                    clearTimeout(pollingTimeout);
                    
                    if (status === 'SUCCESS' && data.response && data.response.sunoData) {
                        // Show results for all generated songs
                        const sunoData = data.response.sunoData;
                        if (sunoData.length > 0) {
                            // Also fetch callback history for this task
                            fetchCallbackHistory(currentTaskId);
                            
                            // Use the enhanced function that adds video buttons
                            displayAllAudioPlayersWithVideo(sunoData);
                            showSuccess(`Cover generation completed! ${sunoData.length} song(s) generated.`);
                        }
                    } else if (status === 'FAILED' || status === 'GENERATE_AUDIO_FAILED') {
                        showError(`Generation failed: ${message || 'Unknown error'}`);
                    }
                } else {
                    // Continue polling
                    pollingTimeout = setTimeout(poll, pollInterval);
                }
            } else {
                throw new Error(result.error || 'Failed to get task status');
            }
        } catch (error) {
            console.error('Polling error:', error);
            isPolling = false;
            showError(`Failed to poll task status: ${error.message}`);
        }
    };
    
    poll();
}

// Fetch callback history for a specific task
async function fetchCallbackHistory(taskId) {
    try {
        const response = await fetch(`/api/history`);
        const result = await response.json();
        
        if (response.ok && result.success) {
            const history = result.history || [];
            const taskCallbacks = history.filter(entry => entry.task_id === taskId);
            
            if (taskCallbacks.length > 0) {
                // Sort by timestamp (newest first)
                taskCallbacks.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                
                // Display callback information
                const latestCallback = taskCallbacks[0];
                if (latestCallback.processed_data) {
                    displayCallbackInfo(latestCallback.processed_data);
                }
                
                // Show callback history summary
                showCallbackHistorySummary(taskCallbacks);
            }
        }
    } catch (error) {
        console.error('Error fetching callback history:', error);
    }
}

// Show callback history summary
function showCallbackHistorySummary(callbacks) {
    const container = document.getElementById('audioPlayersContainer');
    
    if (callbacks.length <= 1) return; // Only show if multiple callbacks
    
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
    const callbackCard = container.querySelector('.callback-card');
    if (callbackCard) {
        callbackCard.insertAdjacentElement('afterend', historyCard);
    } else if (container.firstChild) {
        container.insertBefore(historyCard, container.firstChild);
    } else {
        container.appendChild(historyCard);
    }
}

// Display all audio players for multiple songs with enhanced callback data
function displayAllAudioPlayers(sunoData) {
    const container = document.getElementById('audioPlayersContainer');
    const template = document.getElementById('audioPlayerTemplate');
    
    // Clear existing content
    container.innerHTML = '';
    
    // Create a player for each song
    sunoData.forEach((song, index) => {
        const clone = template.content.cloneNode(true);
        
        // Set song title (use title from song or default)
        const title = song.title || `Generated Song ${index + 1}`;
        clone.querySelector('[data-title]').textContent = title;
        
        // Set model
        clone.querySelector('[data-model]').textContent = song.modelName || 'chirp-crow';
        
        // Set duration
        const duration = song.duration ? `${Math.floor(song.duration)} seconds` : 'Unknown';
        clone.querySelector('[data-duration]').textContent = duration;
        
        // Set audio source - try multiple URL sources
        const audioElement = clone.querySelector('[data-audio]');
        const audioUrl = song.audioUrl || song.sourceAudioUrl || song.streamAudioUrl || song.sourceStreamAudioUrl;
        if (audioUrl) {
            audioElement.src = audioUrl;
        }
        
        // Set audio URL link
        const audioUrlLink = clone.querySelector('[data-audio-url]');
        if (audioUrl) {
            audioUrlLink.href = audioUrl;
            audioUrlLink.textContent = audioUrl;
        }
        
        // Set image URL link - handle multiple possible structures
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
        
        // Set lyrics (display line by line)
        const lyricsElement = clone.querySelector('[data-lyrics]');
        if (song.prompt) {
            // Helper to escape HTML
            const escapeHtml = (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
            // Add line-by-line formatting for better readability
            lyricsElement.innerHTML = song.prompt.split('\n').map(line => {
                if (line.trim() === '') return '<br>';
                return `<div class="lyric-line py-1 border-b border-slate-100 dark:border-slate-700/50 last:border-b-0">${escapeHtml(line)}</div>`;
            }).join('');
        }
        
        // Set up download button
        const downloadBtn = clone.querySelector('[data-download-btn]');
        if (audioUrl) {
            downloadBtn.addEventListener('click', () => {
                handleDownloadAudio(audioUrl, title);
            });
        } else {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<span class="material-symbols-outlined mr-2">block</span> No URL';
        }
        
        // Set up video button with audio ID
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
                    handleCreateMusicVideo(song);
                });
            } else {
                console.log('Video button hidden - no image for song:', song.title);
            }
        } else {
            console.log('Video button not found or song missing ID:', song.id);
        }
        
        // Add enhanced callback data display
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
                        <span class="text-slate-700 dark:text-slate-300">${song.createTime || 'N/A'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Tags/Genre</label>
                        <span class="text-slate-700 dark:text-slate-300">${song.tags || 'N/A'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Source Audio</label>
                        ${song.sourceAudioUrl ?
                            `<a href="${song.sourceAudioUrl}" target="_blank" class="text-primary hover:underline text-xs break-all">View Source</a>` :
                            '<span class="text-slate-500 text-xs">N/A</span>'}
                    </div>
                </div>
            `;
            audioPlayerDiv.appendChild(enhancedDataDiv);
        }
        
        container.appendChild(clone);
    });
    
    // Show results section
    results.classList.remove('hidden');
}

// Display enhanced callback information
function displayCallbackInfo(callbackData) {
    const container = document.getElementById('audioPlayersContainer');
    
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
    if (container.firstChild) {
        container.insertBefore(callbackCard, container.firstChild);
    } else {
        container.appendChild(callbackCard);
    }
}

// Refresh task status manually
function refreshTaskStatus() {
    if (!currentTaskId) {
        showError('No active task to refresh');
        return;
    }
    
    if (refreshStatusBtn) {
        refreshStatusBtn.disabled = true;
        refreshStatusBtn.innerHTML = '<span class="material-symbols-outlined mr-1">sync</span> Refreshing...';
    }
    
    // Clear any existing polling timeout
    if (pollingTimeout) {
        clearTimeout(pollingTimeout);
        pollingTimeout = null;
    }
    
    // Force a status check
    isPolling = false;
    
    // Call pollTaskStatus which will fetch and update
    pollTaskStatus();
    
    // Re-enable button after a short delay
    setTimeout(() => {
        if (refreshStatusBtn) {
            refreshStatusBtn.disabled = false;
            refreshStatusBtn.innerHTML = '<span class="material-symbols-outlined mr-1">refresh</span> Refresh';
        }
    }, 1000);
}

// Handle audio download
async function handleDownloadAudio(audioUrl, title) {
    if (!audioUrl) {
        showError('No audio URL available for download');
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
            
            showSuccess('Download started! The file will be saved as: ' + filename);
            
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
            
            showSuccess('Download started using direct method!');
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
        
        showSuccess('Download started using fallback method!');
    }
}

// Music Video Generation Functions
function showVideoButtonForAudioPlayer(audioPlayerDiv, song) {
    // Show video button if the song has an image (needed for video)
    const videoBtn = audioPlayerDiv.querySelector('[data-video-btn]');
    
    // Check for image URL using all possible property names
    const hasImageUrl = song.image_url ||
                       song.imageUrl ||
                       (song.image_urls && song.image_urls.generated) ||
                       song.source_image_url ||
                       song.sourceImageUrl;
    
    if (videoBtn && song.id && hasImageUrl) {
        videoBtn.style.display = 'block';
        videoBtn.addEventListener('click', () => {
            handleCreateMusicVideo(song);
        });
    }
}

function handleCreateMusicVideo(song) {
    console.log('handleCreateMusicVideo called with song:', song);
    
    // Check for image URL using all possible property names (similar to displayAllAudioPlayers)
    const hasImageUrl = song.image_url ||
                       song.imageUrl ||
                       (song.image_urls && song.image_urls.generated) ||
                       song.source_image_url ||
                       song.sourceImageUrl;
    
    if (!song.id || !hasImageUrl) {
        console.error('Cannot create music video: Missing audio ID or image URL', song);
        showError('Cannot create music video: Missing audio ID or image URL');
        return;
    }
    
    // Show the modal dialog instead of confirmation
    console.log('Calling showVideoModal for song:', song.title);
    showVideoModal(song);
}

function createVideoPlayer(song, videoTaskId) {
    const container = document.getElementById('audioPlayersContainer');
    const template = document.getElementById('videoPlayerTemplate');
    
    if (!template) {
        console.error('Video player template not found');
        return;
    }
    
    const clone = template.content.cloneNode(true);
    
    // Set video title
    const videoTitle = clone.querySelector('[data-video-title]');
    videoTitle.textContent = `Music Video: ${song.title || 'Generated Track'}`;
    
    // Set video task ID
    const taskIdElement = clone.querySelector('[data-video-task-id]');
    taskIdElement.textContent = videoTaskId;
    
    // Store references for updates
    const videoPlayer = clone.querySelector('.video-player');
    videoPlayer.dataset.videoTaskId = videoTaskId;
    videoPlayer.dataset.audioId = song.id;
    
    // Find the corresponding audio player and insert video player after it
    const audioPlayer = container.querySelector(`.audio-player [data-title*="${song.title}"]`)?.closest('.audio-player');
    if (audioPlayer) {
        audioPlayer.insertAdjacentElement('afterend', videoPlayer);
    } else {
        // If can't find specific audio player, append to container
        container.appendChild(videoPlayer);
    }
}

async function pollVideoStatus(videoTaskId, song) {
    const pollInterval = 10000; // 10 seconds for video generation
    
    const poll = async () => {
        try {
            const videoPlayer = document.querySelector(`.video-player[data-video-task-id="${videoTaskId}"]`);
            if (!videoPlayer) {
                console.log('Video player not found, stopping polling');
                return;
            }
            
            const progressBar = videoPlayer.querySelector('[data-video-progress]');
            const statusText = videoPlayer.querySelector('[data-video-status-text]');
            const statusContainer = videoPlayer.querySelector('[data-video-status-container]');
            const videoContainer = videoPlayer.querySelector('[data-video-container]');
            const videoElement = videoPlayer.querySelector('[data-video]');
            const videoUrlLink = videoPlayer.querySelector('[data-video-url]');
            const downloadBtn = videoPlayer.querySelector('[data-video-download-btn]');
            
            // Call the video status API
            const response = await fetch(`/api/video-status/${videoTaskId}`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                const status = data.status;
                const videoUrl = data.video_url;
                const statusMessage = data.status_message;
                
                // Update progress based on status
                if (status === 'complete' && videoUrl) {
                    // Video is ready
                    progressBar.value = 100;
                    statusText.textContent = 'Video generation complete!';
                    
                    // Hide status container and show video
                    setTimeout(() => {
                        statusContainer.style.display = 'none';
                        videoContainer.style.display = 'block';
                        
                        // Set video source
                        videoElement.src = videoUrl;
                        videoUrlLink.href = videoUrl;
                        videoUrlLink.style.display = 'block';
                        videoUrlLink.textContent = 'View video';
                        
                        // Show download button
                        downloadBtn.style.display = 'block';
                        downloadBtn.addEventListener('click', () => {
                            handleDownloadVideo(videoUrl, `${song.title || 'music-video'}.mp4`);
                        });
                        
                        showSuccess('Music video generated successfully!');
                    }, 1000);
                    
                    return; // Stop polling
                } else if (status === 'processing') {
                    // Still processing
                    const currentProgress = parseInt(progressBar.value) || 0;
                    let newProgress = currentProgress + 10;
                    if (newProgress > 90) newProgress = 90; // Cap at 90% until complete
                    
                    progressBar.value = newProgress;
                    statusText.textContent = `Processing video... ${newProgress}% (${statusMessage || 'In progress'})`;
                    
                    // Continue polling
                    setTimeout(poll, pollInterval);
                } else {
                    // Error or unknown status
                    progressBar.value = 100;
                    statusText.textContent = `Error: ${statusMessage || 'Unknown status'}`;
                    statusText.style.color = '#ef4444';
                    
                    // Continue polling but with longer interval
                    setTimeout(poll, pollInterval * 2);
                }
            } else {
                // API error
                console.error('Video status API error:', data.error);
                const currentProgress = parseInt(progressBar.value) || 0;
                let newProgress = currentProgress + 5;
                if (newProgress > 95) newProgress = 95;
                
                progressBar.value = newProgress;
                statusText.textContent = `Checking status... ${newProgress}%`;
                
                // Continue polling
                setTimeout(poll, pollInterval);
            }
        } catch (error) {
            console.error('Error polling video status:', error);
            // Retry after delay
            setTimeout(poll, pollInterval);
        }
    };
    
    // Start polling
    setTimeout(poll, 2000);
}

function handleDownloadVideo(videoUrl, filename) {
    if (!videoUrl) {
        showError('No video URL available for download');
        return;
    }
    
    // Create download link
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    showSuccess('Video download started!');
}

// Update displayAllAudioPlayers to show video buttons
function displayAllAudioPlayersWithVideo(sunoData) {
    displayAllAudioPlayers(sunoData);
    
    // After audio players are displayed, add video buttons
    setTimeout(() => {
        const audioPlayers = document.querySelectorAll('.audio-player');
        audioPlayers.forEach((player, index) => {
            if (index < sunoData.length) {
                const song = sunoData[index];
                showVideoButtonForAudioPlayer(player, song);
            }
        });
    }, 100);
}

// Replace the existing displayAllAudioPlayers call in pollTaskStatus
// We need to update the pollTaskStatus function to use the new function
// Let's find and update that specific part