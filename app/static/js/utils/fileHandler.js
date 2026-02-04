/**
 * File handling utilities for the Music Cover Generator application.
 * Handles file uploads, drag & drop, URL validation, and source management.
 */

class FileHandler {
    constructor() {
        this.uploadedFileUrl = null;
        this.currentSourceType = 'upload';
        this.currentFile = null; // Store the current file for upload
        
        // DOM Elements (will be initialized by the main app)
        this.uploadArea = null;
        this.audioFileInput = null;
        this.fileInfo = null;
        this.fileName = null;
        this.uploadStatus = null;
        this.progressContainer = null;
        this.progressBar = null;
        this.progressText = null;
        this.uploadBtn = null;
        this.generateBtn = null;
        this.audioUrlInput = null;
        this.urlTestResult = null;
        this.useUrlBtn = null;
        this.sourceInfo = null;
        this.sourceType = null;
        this.sourceUrl = null;
        this.uploadTab = null;
        this.urlTab = null;
        this.uploadSection = null;
        this.urlSection = null;
    }

    /**
     * Initialize file handler with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.uploadArea = elements.uploadArea;
        this.audioFileInput = elements.audioFileInput;
        this.fileInfo = elements.fileInfo;
        this.fileName = elements.fileName;
        this.uploadStatus = elements.uploadStatus;
        this.progressContainer = elements.progressContainer;
        this.progressBar = elements.progressBar;
        this.progressText = elements.progressText;
        this.uploadBtn = elements.uploadBtn;
        this.generateBtn = elements.generateBtn;
        this.audioUrlInput = elements.audioUrlInput;
        this.urlTestResult = elements.urlTestResult;
        this.useUrlBtn = elements.useUrlBtn;
        this.sourceInfo = elements.sourceInfo;
        this.sourceType = elements.sourceType;
        this.sourceUrl = elements.sourceUrl;
        this.uploadTab = elements.uploadTab;
        this.urlTab = elements.urlTab;
        this.uploadSection = elements.uploadSection;
        this.urlSection = elements.urlSection;

        this._setupEventListeners();
    }

    /**
     * Set up event listeners for file handling.
     * @private
     */
    _setupEventListeners() {
        if (this.uploadArea) {
            this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
            this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        }

        if (this.audioFileInput) {
            this.audioFileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        if (this.audioUrlInput) {
            this.audioUrlInput.addEventListener('input', () => {
                if (this.urlTestResult) this.urlTestResult.classList.add('hidden');
                if (this.useUrlBtn) this.useUrlBtn.disabled = !this.audioUrlInput.value.trim();
            });
        }
    }

    /**
     * Handle drag over event.
     * @param {Event} e - Drag event
     */
    handleDragOver(e) {
        e.preventDefault();
        if (this.uploadArea) {
            this.uploadArea.style.borderColor = '#4f46e5';
            this.uploadArea.style.background = '#e0e7ff';
        }
    }

    /**
     * Handle drag leave event.
     * @param {Event} e - Drag event
     */
    handleDragLeave(e) {
        e.preventDefault();
        if (this.uploadArea) {
            this.uploadArea.style.borderColor = '#cbd5e1';
            this.uploadArea.style.background = '#f1f5f9';
        }
    }

    /**
     * Handle drop event.
     * @param {Event} e - Drop event
     */
    handleDrop(e) {
        e.preventDefault();
        this.handleDragLeave(e);
        const files = e.dataTransfer.files;
        if (files.length > 0) this.handleFile(files[0]);
    }

    /**
     * Handle file selection from input.
     * @param {Event} e - Change event
     */
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) this.handleFile(file);
    }

    /**
     * Handle a selected file.
     * @param {File} file - The selected file
     */
    handleFile(file) {
        const allowedTypes = ['mp3', 'wav', 'ogg', 'm4a', 'flac'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            window.NotificationSystem?.showError(
                `File type .${fileExtension} not allowed. Please upload: ${allowedTypes.join(', ')}`
            );
            return;
        }

        if (file.size > 100 * 1024 * 1024) {
            window.NotificationSystem?.showError('File size exceeds 100MB limit');
            return;
        }

        // Store the file for upload
        this.currentFile = file;
        
        if (this.fileName) this.fileName.textContent = file.name;
        if (this.fileInfo) this.fileInfo.classList.remove('hidden');
        if (this.uploadStatus) this.uploadStatus.textContent = 'Ready to upload';
        if (this.uploadBtn) this.uploadBtn.disabled = false;
    }

    /**
     * Set the source type (upload or URL).
     * @param {string} type - 'upload' or 'url'
     */
    setSourceType(type) {
        this.currentSourceType = type;
        
        if (type === 'upload') {
            if (this.uploadTab) this.uploadTab.classList.add('active');
            if (this.urlTab) this.urlTab.classList.remove('active');
            if (this.uploadSection) this.uploadSection.classList.remove('hidden');
            if (this.urlSection) this.urlSection.classList.add('hidden');
        } else {
            if (this.uploadTab) this.uploadTab.classList.remove('active');
            if (this.urlTab) this.urlTab.classList.add('active');
            if (this.uploadSection) this.uploadSection.classList.add('hidden');
            if (this.urlSection) this.urlSection.classList.remove('hidden');
        }
        
        if (this.uploadedFileUrl) this.clearAudioSource();
    }

    /**
     * Test an audio URL for accessibility.
     */
    async testAudioUrl() {
        const url = this.audioUrlInput?.value.trim();
        if (!url) {
            window.NotificationSystem?.showError('Please enter a URL');
            return;
        }

        try {
            new URL(url);
        } catch (e) {
            window.NotificationSystem?.showError(
                'Invalid URL format. Please enter a valid URL starting with http:// or https://'
            );
            return;
        }

        if (this.urlTestBtn) {
            this.urlTestBtn.disabled = true;
            this.urlTestBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Testing...';
        }
        
        if (this.urlTestResult) this.urlTestResult.classList.add('hidden');

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            const response = await fetch(url, { method: 'HEAD', mode: 'cors', signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (response.ok) {
                if (this.urlTestResult) {
                    this.urlTestResult.textContent = '✓ URL accessible';
                    this.urlTestResult.className = 'test-result success';
                    this.urlTestResult.classList.remove('hidden');
                }
                if (this.useUrlBtn) this.useUrlBtn.disabled = false;
                window.NotificationSystem?.showSuccess('URL is accessible and ready to use');
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

            if (this.urlTestResult) {
                this.urlTestResult.textContent = '✗ URL not accessible';
                this.urlTestResult.className = 'test-result error';
                this.urlTestResult.classList.remove('hidden');
            }
            window.NotificationSystem?.showError(errorMessage);
        } finally {
            if (this.urlTestBtn) {
                this.urlTestBtn.disabled = false;
                this.urlTestBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_arrow</span> Test URL';
            }
        }
    }

    /**
     * Use the tested audio URL as the source.
     */
    useAudioUrl() {
        const url = this.audioUrlInput?.value.trim();
        if (!url) {
            window.NotificationSystem?.showError('Please enter a URL');
            return;
        }

        this.uploadedFileUrl = url;
        
        if (this.sourceType) this.sourceType.textContent = 'Public URL';
        if (this.sourceUrl) this.sourceUrl.textContent = url;
        if (this.sourceInfo) this.sourceInfo.classList.remove('hidden');
        if (this.generateBtn) {
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
        }
        
        window.NotificationSystem?.showSuccess('Audio URL set successfully! Ready to generate cover.');
    }

    /**
     * Upload the selected file to the server.
     */
    async uploadFile() {
        const file = this.currentFile;
        if (!file) {
            window.NotificationSystem?.showError('No file selected');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        
        if (this.progressContainer) this.progressContainer.classList.remove('hidden');
        if (this.uploadBtn) this.uploadBtn.disabled = true;
        if (this.uploadStatus) this.uploadStatus.textContent = 'Uploading...';

        try {
            const headers = window.csrfToken ? { 'X-CSRFToken': window.csrfToken } : {};
            const response = await fetch('/upload', { method: 'POST', body: formData, headers });
            const data = await response.json();
            
            if (data.success) {
                // The file_url is inside data.data
                const fileUrl = data.data?.file_url;
                if (!fileUrl) {
                    throw new Error('Server did not return file URL');
                }
                
                this.uploadedFileUrl = fileUrl;
                
                if (this.uploadStatus) {
                    this.uploadStatus.textContent = 'Upload successful!';
                    this.uploadStatus.style.color = '#10b981';
                }
                if (this.progressBar) this.progressBar.style.width = '100%';
                if (this.progressText) this.progressText.textContent = '100%';
                if (this.sourceType) this.sourceType.textContent = 'Uploaded File';
                if (this.sourceUrl) this.sourceUrl.textContent = fileUrl;
                if (this.sourceInfo) this.sourceInfo.classList.remove('hidden');
                if (this.generateBtn) {
                    this.generateBtn.disabled = false;
                    this.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
                }
                
                window.NotificationSystem?.showSuccess('File uploaded successfully! Ready to generate cover.');
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            if (this.uploadStatus) {
                this.uploadStatus.textContent = 'Upload failed';
                this.uploadStatus.style.color = '#ef4444';
            }
            window.NotificationSystem?.showError(`Upload failed: ${error.message}`);
            if (this.uploadBtn) this.uploadBtn.disabled = false;
        }
    }

    /**
     * Clear the current audio source.
     */
    clearAudioSource() {
        this.uploadedFileUrl = null;
        this.currentFile = null;
        
        if (this.fileInfo) this.fileInfo.classList.add('hidden');
        if (this.progressContainer) this.progressContainer.classList.add('hidden');
        if (this.uploadBtn) this.uploadBtn.disabled = false;
        if (this.audioFileInput) this.audioFileInput.value = '';
        if (this.audioUrlInput) this.audioUrlInput.value = '';
        if (this.urlTestResult) this.urlTestResult.classList.add('hidden');
        if (this.useUrlBtn) this.useUrlBtn.disabled = true;
        if (this.sourceInfo) this.sourceInfo.classList.add('hidden');
        if (this.generateBtn) {
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<span class="material-symbols-outlined mr-2">play_circle</span> Generate Music Cover';
        }
        
        window.NotificationSystem?.showSuccess('Audio source cleared. Please select a new source.');
    }

    /**
     * Get the current uploaded file URL.
     * @returns {string|null} The uploaded file URL or null
     */
    getUploadedFileUrl() {
        return this.uploadedFileUrl;
    }

    /**
     * Get the current source type.
     * @returns {string} 'upload' or 'url'
     */
    getCurrentSourceType() {
        return this.currentSourceType;
    }

    /**
     * Check if a source is selected.
     * @returns {boolean} True if a source is selected
     */
    hasSource() {
        return !!this.uploadedFileUrl;
    }

    /**
     * Validate a file before processing.
     * @param {File} file - The file to validate
     * @returns {Object} Validation result with isValid and message properties
     */
    static validateFile(file) {
        const allowedTypes = ['mp3', 'wav', 'ogg', 'm4a', 'flac'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            return {
                isValid: false,
                message: `File type .${fileExtension} not allowed. Please upload: ${allowedTypes.join(', ')}`
            };
        }

        if (file.size > 100 * 1024 * 1024) {
            return {
                isValid: false,
                message: 'File size exceeds 100MB limit'
            };
        }

        return { isValid: true, message: 'File is valid' };
    }

    /**
     * Validate a URL.
     * @param {string} url - The URL to validate
     * @returns {Object} Validation result with isValid and message properties
     */
    static validateUrl(url) {
        try {
            new URL(url);
            return { isValid: true, message: 'URL is valid' };
        } catch (e) {
            return {
                isValid: false,
                message: 'Invalid URL format. Please enter a valid URL starting with http:// or https://'
            };
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FileHandler;
} else {
    window.FileHandler = FileHandler;
}