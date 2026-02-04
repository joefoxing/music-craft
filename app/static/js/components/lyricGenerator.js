/**
 * Lyric Generator component for the Music Cover Generator application.
 * Handles lyric generation, display, editing, and synchronization with music.
 */

class LyricGenerator {
    constructor() {
        this.currentLyricTaskId = null;
        this.isPollingLyrics = false;
        this.lyricPollingTimeout = null;
        this.generatedLyrics = [];
        
        // DOM Elements (will be initialized by the main app)
        this.lyricPrompt = null;
        this.lyricCharCount = null;
        this.generateLyricsBtn = null;
        this.lyricsResultsContainer = null;
        this.lyricsResults = null;
        this.refreshLyricsBtn = null;
        this.clearLyricsBtn = null;
        this.toggleLyricSectionBtn = null;
        this.lyricSection = null;
        this.lyricAdvancedBtn = null;
    }

    /**
     * Initialize lyric generator with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.lyricPrompt = elements.lyricPrompt;
        this.lyricCharCount = elements.lyricCharCount;
        this.generateLyricsBtn = elements.generateLyricsBtn;
        this.lyricsResultsContainer = elements.lyricsResultsContainer;
        this.lyricsResults = elements.lyricsResults;
        this.refreshLyricsBtn = elements.refreshLyricsBtn;
        this.clearLyricsBtn = elements.clearLyricsBtn;
        this.toggleLyricSectionBtn = elements.toggleLyricSectionBtn;
        this.lyricSection = elements.lyricSection;
        this.lyricAdvancedBtn = elements.lyricAdvancedBtn;
        this.expandMainEditorBtn = elements.expandMainEditorBtn;

        // Ensure editor modal exists in DOM
        this._ensureEditorModalExists();

        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize character counter
        this.updateLyricCharCount();
    }

    /**
     * Ensure the lyric editor modal exists in the DOM.
     * Creates it if it doesn't exist.
     * @private
     */
    _ensureEditorModalExists() {
        if (!document.getElementById('lyricEditorModal')) {
            const modalHTML = `
            <div id="lyricEditorModal" class="fixed inset-0 z-50 hidden items-center justify-center bg-black/50 backdrop-blur-sm p-4 sm:p-6" role="dialog" aria-modal="true" aria-labelledby="lyricEditorTitleLabel">
                <div class="bg-white dark:bg-surface-dark w-full h-full sm:w-[90vw] sm:h-[85vh] max-w-6xl rounded-xl shadow-2xl flex flex-col overflow-hidden border border-slate-200 dark:border-border-dark transition-all transform scale-100">
                    <!-- Header -->
                    <div class="flex items-center justify-between p-4 border-b border-slate-100 dark:border-border-dark bg-slate-50/50 dark:bg-slate-800/50">
                        <div class="flex items-center gap-3 flex-1 min-w-0">
                            <span class="material-symbols-outlined text-primary">edit_note</span>
                            <div class="flex flex-col">
                                <h3 id="lyricEditorTitleLabel" class="font-bold text-base text-slate-900 dark:text-white leading-none">Edit Lyrics</h3>
                                <input type="text" id="lyricEditorTitle" class="bg-transparent border-none p-0 focus:ring-0 text-sm text-slate-500 dark:text-slate-400 w-full max-w-xs placeholder-slate-400" placeholder="Song Title">
                            </div>
                        </div>
                        <div class="flex items-center gap-3">
                            <label class="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer select-none bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                <input type="checkbox" id="lyricEditorMonospaceToggle" class="rounded border-slate-300 text-primary focus:ring-primary w-3 h-3" checked>
                                <span>Monospace</span>
                            </label>
                            <button id="closeLyricEditor" class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close editor">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>
                    </div>

                    <!-- Toolbar -->
                    <div class="flex items-center gap-2 p-2 border-b border-slate-100 dark:border-border-dark bg-white dark:bg-surface-dark overflow-x-auto scrollbar-hide">
                        <button id="formatLyricBtn" class="px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-xs font-medium flex items-center gap-1 whitespace-nowrap transition-colors">
                            <span class="material-symbols-outlined text-[16px]">format_align_left</span> Format
                        </button>
                        <button id="addSectionBtn" class="px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-xs font-medium flex items-center gap-1 whitespace-nowrap transition-colors">
                            <span class="material-symbols-outlined text-[16px]">add_circle</span> Add Section
                        </button>
                        <button id="previewLyricBtn" class="px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-xs font-medium flex items-center gap-1 whitespace-nowrap transition-colors">
                            <span class="material-symbols-outlined text-[16px]">visibility</span> Preview
                        </button>
                        <div class="w-px h-4 bg-slate-200 dark:bg-slate-700 mx-1"></div>
                        <div id="lyricEditorStats" class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 px-2 font-mono">
                            <span id="lyricEditorLineCount">0 lines</span>
                            <span id="lyricEditorWordCount">0 words</span>
                            <span id="lyricEditorCharCount">0 chars</span>
                        </div>
                    </div>

                    <!-- Editor Area -->
                    <div class="flex-1 flex overflow-hidden relative bg-slate-50 dark:bg-black/20">
                        <!-- Line Numbers -->
                        <div id="lyricEditorLineNumbers" class="hidden sm:block w-10 bg-white dark:bg-surface-dark text-right pr-2 pt-4 text-xs font-mono text-slate-300 dark:text-slate-600 select-none overflow-hidden border-r border-slate-100 dark:border-border-dark leading-relaxed">
                            1
                        </div>
                        <!-- Textarea -->
                        <textarea id="lyricEditorText" class="flex-1 w-full h-full p-4 bg-white dark:bg-surface-dark text-slate-800 dark:text-slate-200 resize-none focus:ring-0 border-none font-mono text-sm sm:text-base leading-relaxed outline-none" spellcheck="false" placeholder="Enter lyrics here..."></textarea>
                        
                        <!-- Structure Sidebar (Desktop) -->
                        <div class="hidden lg:flex w-64 flex-col border-l border-slate-100 dark:border-border-dark bg-white dark:bg-surface-dark">
                            <div class="p-3 border-b border-slate-100 dark:border-border-dark bg-slate-50/50 dark:bg-slate-800/50">
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Structure</h4>
                            </div>
                            <div id="lyricStructure" class="flex-1 overflow-y-auto p-3 space-y-2"></div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div class="p-4 border-t border-slate-100 dark:border-border-dark bg-white dark:bg-surface-dark flex items-center justify-between gap-4">
                        <button id="lyricEditorCopyBtn" class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">content_copy</span>
                            <span class="hidden sm:inline">Copy to Clipboard</span>
                        </button>
                        <div class="flex items-center gap-3">
                            <button id="cancelLyricEdit" class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-sm font-medium transition-colors">
                                Cancel
                            </button>
                            <button id="saveLyricEdit" class="px-6 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg text-sm font-medium shadow-lg shadow-primary/20 transition-all transform active:scale-95 flex items-center gap-2">
                                <span class="material-symbols-outlined text-[18px]">save</span>
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        // Set up listeners for the modal
        this.setupLyricEditorListeners();
    }

    /**
     * Set up event listeners for lyric generator.
     */
    setupEventListeners() {
        if (this.lyricPrompt) {
            this.lyricPrompt.addEventListener('input', this.updateLyricCharCount.bind(this));
        }

        if (this.generateLyricsBtn) {
            this.generateLyricsBtn.addEventListener('click', this.generateLyrics.bind(this));
        }

        if (this.refreshLyricsBtn) {
            this.refreshLyricsBtn.addEventListener('click', this.refreshLyrics.bind(this));
        }

        if (this.clearLyricsBtn) {
            this.clearLyricsBtn.addEventListener('click', this.clearLyrics.bind(this));
        }

        if (this.toggleLyricSectionBtn) {
            this.toggleLyricSectionBtn.addEventListener('click', this.toggleLyricSection.bind(this));
        }

        if (this.lyricAdvancedBtn) {
            this.lyricAdvancedBtn.addEventListener('click', this.showAdvancedSettings.bind(this));
        }

        if (this.expandMainEditorBtn) {
            this.expandMainEditorBtn.addEventListener('click', this.expandMainLyricEditor.bind(this));
        }

        // Keyboard shortcut: Ctrl/Cmd+E to toggle expand editor
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'e' && !e.shiftKey && !e.altKey) {
                e.preventDefault();
                this.toggleExpandEditor();
            }
        });
    }

    /**
     * Update lyric character/word count display.
     */
    updateLyricCharCount() {
        if (!this.lyricPrompt || !this.lyricCharCount) return;
        
        const text = this.lyricPrompt.value;
        const wordCount = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
        this.lyricCharCount.textContent = `${wordCount}/200 words`;
        
        // Add warning class if over limit
        if (wordCount > 200) {
            this.lyricCharCount.classList.add('text-red-500');
        } else {
            this.lyricCharCount.classList.remove('text-red-500');
        }
    }

    /**
     * Generate lyrics from prompt.
     */
    async generateLyrics() {
        if (!this.lyricPrompt) {
            window.NotificationSystem?.showError('Lyric prompt element not found');
            return;
        }

        const prompt = this.lyricPrompt.value.trim();
        if (!prompt) {
            window.NotificationSystem?.showError('Please enter a description for the lyrics');
            return;
        }

        // Validate word count
        const wordCount = prompt.split(/\s+/).length;
        if (wordCount > 200) {
            window.NotificationSystem?.showError(`Prompt too long: ${wordCount} words. Maximum is 200 words.`);
            return;
        }

        // Update UI state
        this.generateLyricsBtn.disabled = true;
        this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">sync</span> Generating...';

        try {
            const response = await fetch('/api/generate-lyrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    call_back_url: window.location.origin + '/callback'
                })
            });

            const data = await response.json();

            if (response.ok && data.code === 200 && data.data?.taskId) {
                this.currentLyricTaskId = data.data.taskId;
                window.NotificationSystem?.showSuccess('Lyric generation started! Tracking task...');
                
                // Start polling for lyric task status
                this.pollLyricTaskStatus();
            } else {
                throw new Error(data.msg || 'Lyric generation failed');
            }
        } catch (error) {
            window.NotificationSystem?.showError(`Lyric generation failed: ${error.message}`);
            this.generateLyricsBtn.disabled = false;
            this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
        }
    }

    /**
     * Poll lyric task status.
     */
    async pollLyricTaskStatus() {
        if (!this.currentLyricTaskId || this.isPollingLyrics) return;
        
        this.isPollingLyrics = true;
        const pollInterval = 5000; // 5 seconds
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/v1/lyrics/record-info?taskId=${this.currentLyricTaskId}`);
                const result = await response.json();
                console.log('Lyric task status result:', result);
                
                if (response.ok) {
                    const data = result.data || {};
                    console.log('Lyric task data:', data);
                    const status = data.status || 'Unknown';
                    const message = result.msg || '';
                    
                    // Check if task is complete
                    if (status === 'SUCCESS' || status === 'FAILED') {
                        this.isPollingLyrics = false;
                        clearTimeout(this.lyricPollingTimeout);
                        
                        if (status === 'SUCCESS') {
                            let lyricsData = null;
                            console.log('Lyric extraction: data.response', data.response, 'data.data', data.data);
                            if (data.response && data.response.lyricsData) {
                                lyricsData = data.response.lyricsData;
                                console.log('LyricsData from response:', lyricsData);
                            } else if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                                // Check if data.data contains lyrics (has text or lyrics field)
                                const firstItem = data.data[0];
                                if (firstItem.text !== undefined || firstItem.lyrics !== undefined) {
                                    // Normalize to text field
                                    lyricsData = data.data.map(item => {
                                        const normalized = {...item};
                                        if (normalized.lyrics !== undefined && normalized.text === undefined) {
                                            normalized.text = normalized.lyrics;
                                        }
                                        return normalized;
                                    });
                                    console.log('LyricsData from mapping:', lyricsData);
                                }
                            }
                            
                            if (lyricsData) {
                                // Process and display generated lyrics
                                this.displayGeneratedLyrics(lyricsData);
                                
                                // Reset button state
                                this.generateLyricsBtn.disabled = false;
                                this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
                                
                                window.NotificationSystem?.showSuccess(`Lyric generation completed! ${lyricsData.length} variation(s) generated.`);
                            } else {
                                // No lyrics data found, treat as failure?
                                window.NotificationSystem?.showError('Lyric generation completed but no lyrics data received.');
                                this.generateLyricsBtn.disabled = false;
                                this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
                            }
                        } else if (status === 'FAILED') {
                            window.NotificationSystem?.showError(`Lyric generation failed: ${message || 'Unknown error'}`);
                            this.generateLyricsBtn.disabled = false;
                            this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
                        }
                    } else {
                        // Continue polling
                        this.lyricPollingTimeout = setTimeout(poll, pollInterval);
                    }
                } else {
                    throw new Error(result.error || 'Failed to get task status');
                }
            } catch (error) {
                console.error('Lyric polling error:', error);
                this.isPollingLyrics = false;
                window.NotificationSystem?.showError(`Failed to poll lyric task status: ${error.message}`);
                
                // Reset button state on error
                this.generateLyricsBtn.disabled = false;
                this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
            }
        };
        
        poll();
    }

    /**
     * Display generated lyrics.
     * @param {Array} lyricsData - Array of lyric objects
     */
    displayGeneratedLyrics(lyricsData) {
        console.log('Displaying generated lyrics:', lyricsData);
        if (!this.lyricsResults || !this.lyricsResultsContainer) return;
        
        this.generatedLyrics = lyricsData;
        this.lyricsResults.innerHTML = '';
        
        lyricsData.forEach((lyric, index) => {
            const lyricCard = this.createLyricCard(lyric, index);
            this.lyricsResults.appendChild(lyricCard);
        });
        
        // Show results container
        this.lyricsResultsContainer.classList.remove('hidden');
        
        // Populate lyric prompt box with first generated lyric
        if (this.lyricPrompt && lyricsData.length > 0) {
            this.lyricPrompt.value = lyricsData[0].text;
            this.updateLyricCharCount();
            // Optionally update label to indicate lyrics are loaded
            const label = document.querySelector('label[for="lyricPrompt"]');
            if (label) {
                label.textContent = 'Generated lyrics (editable)';
                label.classList.add('text-primary');
            }
        }
    }

    /**
     * Create a lyric card element.
     * @param {Object} lyric - Lyric object
     * @param {number} index - Index of lyric in array
     * @returns {HTMLElement} Lyric card element
     */
    createLyricCard(lyric, index) {
        const card = document.createElement('div');
        card.className = 'bg-white dark:bg-surface-dark rounded-xl border border-slate-200 dark:border-border-dark p-6 hover:border-primary/50 transition-all hover:shadow-lg hover:shadow-primary/5';
        
        // Parse lyric text into sections
        const sections = this.parseLyricSections(lyric.text);
        
        card.innerHTML = `
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h5 class="font-bold text-slate-900 dark:text-white text-lg">${lyric.title || `Lyrics ${index + 1}`}</h5>
                    <p class="text-xs text-slate-500 dark:text-slate-400">${sections.length} sections • Generated just now</p>
                </div>
                <div class="flex items-center gap-2">
                    <button class="lyric-edit-btn p-2 text-slate-400 hover:text-primary rounded-lg" data-index="${index}" title="Edit lyrics">
                        <span class="material-symbols-outlined">edit</span>
                    </button>
                    <button class="lyric-use-btn p-2 text-slate-400 hover:text-primary rounded-lg" data-index="${index}" title="Use for music generation">
                        <span class="material-symbols-outlined">music_note</span>
                    </button>
                    <button class="lyric-copy-btn p-2 text-slate-400 hover:text-primary rounded-lg" data-index="${index}" title="Copy to clipboard">
                        <span class="material-symbols-outlined">content_copy</span>
                    </button>
                    <button class="lyric-expand-editor-btn px-3 py-1.5 text-slate-400 hover:text-primary rounded-lg flex items-center gap-2 border border-slate-200 dark:border-slate-700 hover:border-primary/50 transition-colors" data-index="${index}" title="Expand editor (Ctrl+E)" aria-label="Expand editor">
                        <span class="material-symbols-outlined text-sm">open_in_full</span>
                        <span class="text-xs font-medium">Expand Editor</span>
                    </button>
                </div>
            </div>
            
            <div class="lyric-preview text-sm text-slate-700 dark:text-slate-300 max-h-48 overflow-y-auto custom-scrollbar mb-4">
                ${this.formatLyricPreview(sections)}
            </div>
            
            <div class="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-border-dark">
                <div class="flex items-center gap-2">
                    <span class="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">Lyrics</span>
                    <span class="text-xs text-slate-500">${this.countLines(lyric.text)} lines</span>
                </div>
                <button class="lyric-expand-btn text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1" data-index="${index}">
                    <span class="material-symbols-outlined text-[14px]">expand_more</span>
                    Expand
                </button>
            </div>
            
            <div class="lyric-full-content hidden mt-4 pt-4 border-t border-slate-100 dark:border-border-dark">
                <div class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line font-mono leading-relaxed">
                    ${lyric.text.replace(/\[/g, '<span class="text-primary font-bold">[').replace(/\]/g, ']</span>')}
                </div>
                <div class="mt-4 flex justify-end">
                    <button class="lyric-save-btn px-4 py-2 bg-primary hover:bg-primary-dark text-white text-xs font-bold rounded-lg transition-all">
                        Save to Project
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners to buttons
        const editBtn = card.querySelector('.lyric-edit-btn');
        const useBtn = card.querySelector('.lyric-use-btn');
        const copyBtn = card.querySelector('.lyric-copy-btn');
        const expandEditorBtn = card.querySelector('.lyric-expand-editor-btn');
        const expandBtn = card.querySelector('.lyric-expand-btn');
        const saveBtn = card.querySelector('.lyric-save-btn');
        
        if (editBtn) {
            editBtn.addEventListener('click', () => this.editLyric(index));
        }
        
        if (useBtn) {
            useBtn.addEventListener('click', () => this.useLyricForMusic(index));
        }
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyLyricToClipboard(index));
        }
        
        if (expandEditorBtn) {
            expandEditorBtn.addEventListener('click', () => this.expandLyricEditor(index));
        }
        
        if (expandBtn) {
            expandBtn.addEventListener('click', (e) => this.toggleLyricExpansion(e, index));
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveLyricToProject(index));
        }
        
        return card;
    }

    /**
     * Parse lyric text into sections.
     * @param {string} lyricText - Raw lyric text with section markers
     * @returns {Array} Array of section objects
     */
    parseLyricSections(lyricText) {
        const sections = [];
        const lines = lyricText.split('\n');
        let currentSection = null;
        
        lines.forEach(line => {
            const sectionMatch = line.match(/^\[([^\]]+)\]/);
            if (sectionMatch) {
                if (currentSection) {
                    sections.push(currentSection);
                }
                currentSection = {
                    title: sectionMatch[1],
                    lines: []
                };
            } else if (currentSection && line.trim()) {
                currentSection.lines.push(line.trim());
            }
        });
        
        if (currentSection) {
            sections.push(currentSection);
        }
        
        return sections;
    }

    /**
     * Format lyric preview for display.
     * @param {Array} sections - Array of lyric sections
     * @returns {string} HTML string for preview
     */
    formatLyricPreview(sections) {
        if (sections.length === 0) return '<p class="text-slate-500 italic">No lyrics content</p>';
        
        let preview = '';
        const maxSections = 2;
        const maxLines = 3;
        
        sections.slice(0, maxSections).forEach(section => {
            preview += `<div class="mb-3">
                <div class="text-primary font-bold text-xs mb-1">[${section.title}]</div>
                <div class="pl-2">`;
            
            section.lines.slice(0, maxLines).forEach(line => {
                preview += `<div class="mb-1">${line}</div>`;
            });
            
            if (section.lines.length > maxLines) {
                preview += `<div class="text-slate-500 text-xs italic">... ${section.lines.length - maxLines} more lines</div>`;
            }
            
            preview += `</div></div>`;
        });
        
        if (sections.length > maxSections) {
            preview += `<div class="text-slate-500 text-xs italic mt-2">... ${sections.length - maxSections} more sections</div>`;
        }
        
        return preview;
    }

    /**
     * Count lines in lyric text.
     * @param {string} text - Lyric text
     * @returns {number} Number of lines
     */
    countLines(text) {
        return text.split('\n').filter(line => line.trim()).length;
    }

    /**
     * Edit a lyric.
     * @param {number} index - Index of lyric to edit
     */
    editLyric(index) {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        this.openLyricEditor(lyric, index);
    }

    /**
     * Expand the main lyric input editor.
     */
    expandMainLyricEditor() {
        if (!this.lyricPrompt) return;
        
        const text = this.lyricPrompt.value;
        const lyric = {
            title: 'Custom Lyrics',
            text: text
        };
        
        // Use index -1 to indicate main input editing
        this.openLyricEditor(lyric, -1);
    }
    
    /**
     * Expand lyric editor (opens modal with enhanced editing).
     * @param {number} index - Index of lyric to expand
     */
    expandLyricEditor(index) {
        this.editLyric(index);
        // Additional setup for expanded mode can be added here
    }
    
    /**
     * Toggle expand editor modal with keyboard shortcut.
     */
    toggleExpandEditor() {
        const modal = document.getElementById('lyricEditorModal');
        if (!modal) return;
        
        if (modal.classList.contains('hidden')) {
            // Open editor for first lyric if any
            if (this.generatedLyrics.length > 0) {
                this.expandLyricEditor(0);
            }
        } else {
            // Close modal
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
    
    /**
     * Open lyric editor modal.
     * @param {Object} lyric - Lyric object to edit
     * @param {number} index - Index of lyric in array
     */
    openLyricEditor(lyric, index) {
        const modal = document.getElementById('lyricEditorModal');
        if (!modal) {
            window.NotificationSystem?.showError('Lyric editor modal not found');
            return;
        }
        
        // Store current editing index
        this.editingLyricIndex = index;
        
        // Populate editor fields
        const titleInput = document.getElementById('lyricEditorTitle');
        const textArea = document.getElementById('lyricEditorText');
        
        if (titleInput) {
            titleInput.value = lyric.title || `Lyrics ${index + 1}`;
        }
        
        if (textArea) {
            textArea.value = lyric.text;
            this.updateLyricEditorStats();
        }
        
        // Populate structure panel
        this.populateLyricStructure(lyric.text);
        
        // Show modal
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.style.display = ''; // Clear any inline style set by close
        
        // Focus text area
        if (textArea) {
            setTimeout(() => textArea.focus(), 100);
        }
    }
    
    /**
     * Populate lyric structure panel.
     * @param {string} lyricText - Lyric text to parse for structure
     */
    populateLyricStructure(lyricText) {
        const structureContainer = document.getElementById('lyricStructure');
        if (!structureContainer) return;
        
        const sections = this.parseLyricSections(lyricText);
        structureContainer.innerHTML = '';
        
        sections.forEach((section, index) => {
            const sectionElement = document.createElement('div');
            sectionElement.className = 'bg-slate-100 dark:bg-[#2a1f2a] rounded-lg p-3';
            sectionElement.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <span class="font-bold text-slate-900 dark:text-white text-sm">[${section.title}]</span>
                    <button class="section-delete-btn text-slate-400 hover:text-red-500" data-index="${index}">
                        <span class="material-symbols-outlined text-[16px]">delete</span>
                    </button>
                </div>
                <div class="text-xs text-slate-600 dark:text-slate-400">
                    ${section.lines.length} lines
                </div>
            `;
            structureContainer.appendChild(sectionElement);
        });
    }
    
    /**
     * Update lyric editor statistics.
     */
    updateLyricEditorStats() {
        const textArea = document.getElementById('lyricEditorText');
        const lineCountEl = document.getElementById('lyricEditorLineCount');
        const wordCountEl = document.getElementById('lyricEditorWordCount');
        const charCountEl = document.getElementById('lyricEditorCharCount');
        const lineNumbersEl = document.getElementById('lyricEditorLineNumbers');
        
        if (!textArea || !lineCountEl || !wordCountEl) return;
        
        const text = textArea.value;
        const allLines = text.split('\n');
        const lines = allLines.filter(line => line.trim()).length;
        const words = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
        const chars = text.length;
        const totalLines = allLines.length;
        
        lineCountEl.textContent = `${lines} line${lines !== 1 ? 's' : ''}`;
        wordCountEl.textContent = `${words} word${words !== 1 ? 's' : ''}`;
        if (charCountEl) {
            charCountEl.textContent = `${chars} character${chars !== 1 ? 's' : ''}`;
        }
        
        // Update line numbers
        if (lineNumbersEl) {
            let numbers = '';
            for (let i = 1; i <= totalLines; i++) {
                numbers += `<div>${i}</div>`;
            }
            lineNumbersEl.innerHTML = numbers;
        }
    }
    
    /**
     * Set up lyric editor modal event listeners.
     */
    setupLyricEditorListeners() {
        // Close button
        const closeBtn = document.getElementById('closeLyricEditor');
        const cancelBtn = document.getElementById('cancelLyricEdit');
        const saveBtn = document.getElementById('saveLyricEdit');
        const textArea = document.getElementById('lyricEditorText');
        const addSectionBtn = document.getElementById('addSectionBtn');
        const formatBtn = document.getElementById('formatLyricBtn');
        const previewBtn = document.getElementById('previewLyricBtn');
        const monospaceToggle = document.getElementById('lyricEditorMonospaceToggle');
        const copyBtn = document.getElementById('lyricEditorCopyBtn');
        
        const closeModal = (e) => {
            if (e) e.preventDefault();
            const modal = document.getElementById('lyricEditorModal');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                // Force display none to ensure it closes
                modal.style.display = 'none';
            }
        };
        
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', closeModal);
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', this.saveEditedLyric.bind(this));
        }
        
        if (textArea) {
            textArea.addEventListener('input', this.updateLyricEditorStats.bind(this));
            // Sync scroll for line numbers
            textArea.addEventListener('scroll', () => {
                const lineNumbers = document.getElementById('lyricEditorLineNumbers');
                if (lineNumbers) {
                    lineNumbers.scrollTop = textArea.scrollTop;
                }
            });
        }
        
        if (addSectionBtn) {
            addSectionBtn.addEventListener('click', this.addNewSection.bind(this));
        }
        
        if (formatBtn) {
            formatBtn.addEventListener('click', this.formatLyricText.bind(this));
        }
        
        if (previewBtn) {
            previewBtn.addEventListener('click', this.previewLyric.bind(this));
        }
        
        if (monospaceToggle) {
            monospaceToggle.addEventListener('change', (e) => {
                textArea.classList.toggle('font-mono', e.target.checked);
            });
            // Set initial state
            textArea.classList.toggle('font-mono', monospaceToggle.checked);
        }
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyEditorLyrics());
        }
        
        // Close modal on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('lyricEditorModal');
                if (modal && !modal.classList.contains('hidden')) {
                    closeModal();
                }
            }
        });
    }
    
    /**
     * Save edited lyric.
     */
    saveEditedLyric() {
        const index = this.editingLyricIndex;
        if (index === undefined || index === null) return;
        
        const titleInput = document.getElementById('lyricEditorTitle');
        const textArea = document.getElementById('lyricEditorText');
        
        if (!titleInput || !textArea) return;

        // Handle main input editing (index -1)
        if (index === -1) {
            if (this.lyricPrompt) {
                this.lyricPrompt.value = textArea.value;
                this.updateLyricCharCount();
            }
            
            // Close modal
            const modal = document.getElementById('lyricEditorModal');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            }
            
            window.NotificationSystem?.showSuccess(`Main lyrics updated successfully!`);
            return;
        }
        
        const updatedLyric = {
            ...this.generatedLyrics[index],
            title: titleInput.value.trim() || `Lyrics ${index + 1}`,
            text: textArea.value
        };
        
        // Update the lyric in the array
        this.generatedLyrics[index] = updatedLyric;
        
        // Update the display
        this.displayGeneratedLyrics(this.generatedLyrics);
        
        // Close modal
        const modal = document.getElementById('lyricEditorModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        
        window.NotificationSystem?.showSuccess(`Lyrics updated successfully!`);
    }
    
    /**
     * Add new section to lyric.
     */
    addNewSection() {
        const textArea = document.getElementById('lyricEditorText');
        if (!textArea) return;
        
        const cursorPos = textArea.selectionStart;
        const text = textArea.value;
        const before = text.substring(0, cursorPos);
        const after = text.substring(cursorPos);
        
        // Add a new section marker
        const newSection = '\n\n[New Section]\n';
        textArea.value = before + newSection + after;
        
        // Update cursor position
        const newCursorPos = cursorPos + newSection.length;
        setTimeout(() => {
            textArea.selectionStart = newCursorPos;
            textArea.selectionEnd = newCursorPos;
            textArea.focus();
        }, 10);
        
        // Update stats and structure
        this.updateLyricEditorStats();
        this.populateLyricStructure(textArea.value);
    }
    
    /**
     * Format lyric text.
     */
    formatLyricText() {
        const textArea = document.getElementById('lyricEditorText');
        if (!textArea) return;
        
        let text = textArea.value;
        
        // Ensure section markers have proper formatting
        text = text.replace(/\[([^\]]+)\]/g, '\n[$1]\n');
        
        // Remove excessive blank lines
        text = text.replace(/\n\s*\n\s*\n/g, '\n\n');
        
        // Trim each line
        const lines = text.split('\n').map(line => line.trim());
        text = lines.join('\n');
        
        // Ensure text starts with a section marker if not empty
        if (text.trim() && !text.trim().startsWith('[')) {
            text = '[Verse]\n' + text;
        }
        
        textArea.value = text;
        this.updateLyricEditorStats();
        this.populateLyricStructure(text);
        
        window.NotificationSystem?.showSuccess('Lyrics formatted!');
    }
    
    /**
     * Preview lyric.
     */
    previewLyric() {
        const textArea = document.getElementById('lyricEditorText');
        if (!textArea) return;
        
        const previewText = textArea.value;
        if (!previewText.trim()) {
            window.NotificationSystem?.showError('No lyrics to preview');
            return;
        }
        
        // In a real implementation, this would show a formatted preview
        // For now, just show an alert with the first few lines
        const previewLines = previewText.split('\n').slice(0, 10).join('\n');
        const previewTitle = document.getElementById('lyricEditorTitle')?.value || 'Preview';
        
        window.NotificationSystem?.showInfo(`Previewing "${previewTitle}":\n${previewLines}${previewText.split('\n').length > 10 ? '\n...' : ''}`);
    }
    
    /**
     * Copy lyrics from editor to clipboard.
     */
    copyEditorLyrics() {
        const textArea = document.getElementById('lyricEditorText');
        if (!textArea) return;
        
        const text = textArea.value;
        if (!text.trim()) {
            window.NotificationSystem?.showError('No lyrics to copy');
            return;
        }
        
        navigator.clipboard.writeText(text)
            .then(() => {
                window.NotificationSystem?.showSuccess('Lyrics copied to clipboard!');
            })
            .catch(err => {
                console.error('Failed to copy lyrics:', err);
                window.NotificationSystem?.showError(`Failed to copy lyrics: ${err.message}`);
            });
    }
    
    /**
     * Synchronize lyrics with music generation.
     * This method prepares lyrics to be used with music generation by creating
     * a structured prompt that includes timing and section information.
     * @param {number} index - Index of lyric to synchronize
     */
    synchronizeWithMusic(index) {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        // Parse sections
        const sections = this.parseLyricSections(lyric.text);
        
        // Create a structured music prompt with timing suggestions
        let musicPrompt = `Create music for these lyrics with the following structure:\n\n`;
        
        sections.forEach((section, i) => {
            const sectionType = section.title.toLowerCase();
            let tempo = 'medium';
            let mood = 'emotional';
            
            // Map section types to musical characteristics
            if (sectionType.includes('verse')) {
                tempo = 'medium';
                mood = 'storytelling';
            } else if (sectionType.includes('chorus')) {
                tempo = 'upbeat';
                mood = 'energetic';
            } else if (sectionType.includes('bridge')) {
                tempo = 'slow';
                mood = 'reflective';
            } else if (sectionType.includes('intro') || sectionType.includes('outro')) {
                tempo = 'slow';
                mood = 'atmospheric';
            }
            
            musicPrompt += `[${section.title}]: ${tempo} tempo, ${mood} mood, ${section.lines.length} lines\n`;
            
            // Add first few lines as example
            const sampleLines = section.lines.slice(0, 2).join(' ');
            if (sampleLines) {
                musicPrompt += `  "${sampleLines}"\n`;
            }
        });
        
        // Set the music prompt
        const musicPromptElement = document.getElementById('musicPrompt');
        if (musicPromptElement) {
            musicPromptElement.value = musicPrompt;
            
            // Update character count if exists
            const charCount = document.getElementById('charCount');
            if (charCount) {
                charCount.textContent = musicPrompt.length;
            }
            
            window.NotificationSystem?.showSuccess(`Lyrics synchronized with music generation! Structured prompt created.`);
            
            // Scroll to music section
            musicPromptElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            musicPromptElement.focus();
        }
    }
    
    /**
     * Export lyrics in various formats.
     * @param {number} index - Index of lyric to export
     * @param {string} format - Export format ('txt', 'json', 'srt')
     */
    exportLyrics(index, format = 'txt') {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        let content = '';
        let filename = '';
        let mimeType = '';
        
        switch (format) {
            case 'txt':
                content = `${lyric.title || 'Lyrics'}\n\n${lyric.text}`;
                filename = `${lyric.title || 'lyrics'}.txt`;
                mimeType = 'text/plain';
                break;
                
            case 'json':
                const lyricData = {
                    title: lyric.title || 'Lyrics',
                    text: lyric.text,
                    sections: this.parseLyricSections(lyric.text),
                    exportDate: new Date().toISOString()
                };
                content = JSON.stringify(lyricData, null, 2);
                filename = `${lyric.title || 'lyrics'}.json`;
                mimeType = 'application/json';
                break;
                
            case 'srt':
                // Simple SRT format for timing (placeholder times)
                const sections = this.parseLyricSections(lyric.text);
                let srtContent = '';
                let counter = 1;
                let startTime = 0;
                
                sections.forEach(section => {
                    section.lines.forEach((line, lineIndex) => {
                        const endTime = startTime + 5; // 5 seconds per line
                        srtContent += `${counter}\n`;
                        srtContent += `${this.formatTime(startTime)} --> ${this.formatTime(endTime)}\n`;
                        srtContent += `${line}\n\n`;
                        
                        startTime = endTime;
                        counter++;
                    });
                    // Add section marker as separate subtitle
                    const endTime = startTime + 2;
                    srtContent += `${counter}\n`;
                    srtContent += `${this.formatTime(startTime)} --> ${this.formatTime(endTime)}\n`;
                    srtContent += `[${section.title}]\n\n`;
                    
                    startTime = endTime;
                    counter++;
                });
                
                content = srtContent;
                filename = `${lyric.title || 'lyrics'}.srt`;
                mimeType = 'text/plain';
                break;
        }
        
        // Create download link
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        window.NotificationSystem?.showSuccess(`Lyrics exported as ${format.toUpperCase()} file!`);
    }
    
    /**
     * Format time for SRT export.
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time string (HH:MM:SS,mmm)
     */
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const millis = Math.floor((seconds % 1) * 1000);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${millis.toString().padStart(3, '0')}`;
    }

    /**
     * Use lyric for music generation.
     * @param {number} index - Index of lyric to use
     */
    useLyricForMusic(index) {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        // Set the prompt input with lyric content
        const promptInput = document.getElementById('promptInput');
        if (promptInput) {
            promptInput.value = lyric.text;
            
            // Update character count if exists
            const promptChars = document.getElementById('promptChars');
            if (promptChars) {
                promptChars.textContent = promptInput.value.length;
            }
            
            window.NotificationSystem?.showSuccess(`Lyrics added to generation prompt!`);
            
            // Scroll to prompt input section
            promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            promptInput.focus();
            
            // Trigger input event to ensure other listeners (like ModeManager) update
            promptInput.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            console.warn('Prompt input element not found');
        }
    }

    /**
     * Copy lyric to clipboard.
     * @param {number} index - Index of lyric to copy
     */
    async copyLyricToClipboard(index) {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        try {
            await navigator.clipboard.writeText(lyric.text);
            window.NotificationSystem?.showSuccess(`Lyrics copied to clipboard!`);
        } catch (error) {
            console.error('Failed to copy lyrics:', error);
            window.NotificationSystem?.showError(`Failed to copy lyrics: ${error.message}`);
        }
    }

    /**
     * Toggle lyric expansion.
     * @param {Event} event - Click event
     * @param {number} index - Index of lyric to expand/collapse
     */
    toggleLyricExpansion(event, index) {
        const card = event.target.closest('.bg-white, .dark\\:bg-surface-dark');
        if (!card) return;
        
        const fullContent = card.querySelector('.lyric-full-content');
        const expandBtn = card.querySelector('.lyric-expand-btn');
        const expandIcon = expandBtn?.querySelector('.material-symbols-outlined');
        
        if (fullContent && expandBtn && expandIcon) {
            if (fullContent.classList.contains('hidden')) {
                fullContent.classList.remove('hidden');
                expandIcon.textContent = 'expand_less';
                expandBtn.innerHTML = '<span class="material-symbols-outlined text-[14px]">expand_less</span> Collapse';
            } else {
                fullContent.classList.add('hidden');
                expandIcon.textContent = 'expand_more';
                expandBtn.innerHTML = '<span class="material-symbols-outlined text-[14px]">expand_more</span> Expand';
            }
        }
    }

    /**
     * Save lyric to project.
     * @param {number} index - Index of lyric to save
     */
    async saveLyricToProject(index) {
        const lyric = this.generatedLyrics[index];
        if (!lyric) return;
        
        // Prepare lyrics data for saving
        const lyricsData = {
            title: lyric.title || `Lyrics ${index + 1}`,
            text: lyric.text,
            sections: this.parseLyricSections(lyric.text),
            generatedAt: new Date().toISOString(),
            wordCount: lyric.text.trim() === '' ? 0 : lyric.text.trim().split(/\s+/).length,
            lineCount: this.countLines(lyric.text)
        };
        
        // Ask for project name
        const projectTitle = prompt('Enter a name for this lyric project:', lyricsData.title);
        if (!projectTitle) return; // User cancelled
        
        // Prepare save data
        const saveData = {
            title: projectTitle,
            lyrics_data: lyricsData,
            description: `Lyrics generated from prompt: "${this.lyricPrompt?.value.substring(0, 100)}..."`,
            tags: ['generated', 'lyrics'],
            is_public: false
        };
        
        try {
            const response = await fetch('/api/save-lyrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saveData)
            });
            
            const result = await response.json();
            
            if (response.ok && result.code === 200) {
                window.NotificationSystem?.showSuccess(`"${projectTitle}" saved to your projects!`);
                
                // Update the lyric card with project info
                this.updateLyricCardWithProjectInfo(index, result.data.project);
            } else {
                throw new Error(result.msg || 'Failed to save lyrics');
            }
        } catch (error) {
            console.error('Failed to save lyrics:', error);
            window.NotificationSystem?.showError(`Failed to save lyrics: ${error.message}`);
        }
    }
    
    /**
     * Update lyric card with project information.
     * @param {number} index - Index of lyric
     * @param {Object} project - Project data
     */
    updateLyricCardWithProjectInfo(index, project) {
        const lyricCard = document.querySelector(`.lyric-card[data-index="${index}"]`);
        if (!lyricCard) return;
        
        // Add project badge
        const badgeContainer = lyricCard.querySelector('.badge-container');
        if (badgeContainer) {
            const projectBadge = document.createElement('span');
            projectBadge.className = 'text-xs px-2 py-1 bg-green-500/10 text-green-500 rounded-full ml-2';
            projectBadge.textContent = 'Saved';
            badgeContainer.appendChild(projectBadge);
        }
        
        // Update save button
        const saveBtn = lyricCard.querySelector('.lyric-save-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saved to Project';
            saveBtn.classList.remove('bg-primary', 'hover:bg-primary-dark');
            saveBtn.classList.add('bg-green-500', 'hover:bg-green-600');
        }
    }
    
    /**
     * Load saved projects for the current user.
     */
    async loadSavedProjects() {
        try {
            const response = await fetch('/api/projects?type=lyrics&limit=10');
            const result = await response.json();
            
            if (response.ok && result.code === 200) {
                return result.data.projects || [];
            } else {
                console.warn('Failed to load saved projects:', result.msg);
                return [];
            }
        } catch (error) {
            console.error('Error loading saved projects:', error);
            return [];
        }
    }
    
    /**
     * Load a saved lyric project into the editor.
     * @param {Object} project - Project object
     */
    loadLyricProject(project) {
        if (!project || !project.lyrics_data) return;
        
        const lyricsData = project.lyrics_data;
        
        // Create a lyric object compatible with generatedLyrics format
        const lyric = {
            title: lyricsData.title || project.title,
            text: lyricsData.text || '',
            project_id: project.id,
            saved_at: project.updated_at
        };
        
        // Add to generated lyrics
        this.generatedLyrics.push(lyric);
        
        // Display it
        this.displayGeneratedLyrics(this.generatedLyrics);
        
        window.NotificationSystem?.showSuccess(`Loaded "${lyric.title}" from saved projects`);
    }

    /**
     * Refresh lyrics (re-poll current task).
     */
    refreshLyrics() {
        if (!this.currentLyricTaskId) {
            window.NotificationSystem?.showError('No active lyric task to refresh');
            return;
        }
        
        if (this.refreshLyricsBtn) {
            this.refreshLyricsBtn.disabled = true;
            this.refreshLyricsBtn.innerHTML = '<span class="material-symbols-outlined mr-1">sync</span> Refreshing...';
        }
        
        // Clear any existing polling timeout
        if (this.lyricPollingTimeout) {
            clearTimeout(this.lyricPollingTimeout);
            this.lyricPollingTimeout = null;
        }
        
        // Force a status check
        this.isPollingLyrics = false;
        this.pollLyricTaskStatus();
        
        // Re-enable button after a short delay
        setTimeout(() => {
            if (this.refreshLyricsBtn) {
                this.refreshLyricsBtn.disabled = false;
                this.refreshLyricsBtn.innerHTML = '<span class="material-symbols-outlined mr-1">refresh</span> Refresh';
            }
        }, 1000);
    }

    /**
     * Clear all generated lyrics.
     */
    clearLyrics() {
        if (this.generatedLyrics.length === 0) {
            window.NotificationSystem?.showInfo('No lyrics to clear');
            return;
        }
        
        if (confirm('Are you sure you want to clear all generated lyrics?')) {
            this.generatedLyrics = [];
            if (this.lyricsResults) {
                this.lyricsResults.innerHTML = '';
            }
            if (this.lyricsResultsContainer) {
                this.lyricsResultsContainer.classList.add('hidden');
            }
            // Clear lyric prompt box and revert label
            if (this.lyricPrompt) {
                this.lyricPrompt.value = '';
                this.updateLyricCharCount();
            }
            const label = document.querySelector('label[for="lyricPrompt"]');
            if (label) {
                label.textContent = 'Describe the lyrics you want to generate';
                label.classList.remove('text-primary');
            }
            window.NotificationSystem?.showSuccess('All lyrics cleared');
        }
    }

    /**
     * Toggle lyric section visibility.
     */
    toggleLyricSection() {
        if (!this.lyricSection || !this.toggleLyricSectionBtn) return;
        
        const isHidden = this.lyricSection.classList.contains('hidden');
        const icon = this.toggleLyricSectionBtn.querySelector('.material-symbols-outlined');
        const text = this.toggleLyricSectionBtn.querySelector('span:not(.material-symbols-outlined)');
        
        if (isHidden) {
            this.lyricSection.classList.remove('hidden');
            if (icon) icon.textContent = 'expand_less';
            if (text) text.textContent = 'Collapse';
        } else {
            this.lyricSection.classList.add('hidden');
            if (icon) icon.textContent = 'expand_more';
            if (text) text.textContent = 'Expand';
        }
    }

    /**
     * Show advanced settings for lyric generation.
     */
    showAdvancedSettings() {
        // In a real implementation, this would show a modal with advanced options
        window.NotificationSystem?.showInfo('Advanced lyric settings coming soon!');
    }

    /**
     * Get generated lyrics.
     * @returns {Array} Array of generated lyrics
     */
    getGeneratedLyrics() {
        return this.generatedLyrics;
    }

    /**
     * Set generated lyrics (for loading from saved state).
     * @param {Array} lyrics - Array of lyric objects
     */
    setGeneratedLyrics(lyrics) {
        this.generatedLyrics = lyrics || [];
        if (this.generatedLyrics.length > 0) {
            this.displayGeneratedLyrics(this.generatedLyrics);
        }
    }

    /**
     * Reset lyric generator state.
     */
    reset() {
        this.currentLyricTaskId = null;
        this.isPollingLyrics = false;
        this.generatedLyrics = [];
        
        if (this.lyricPollingTimeout) {
            clearTimeout(this.lyricPollingTimeout);
            this.lyricPollingTimeout = null;
        }
        
        if (this.lyricsResultsContainer) {
            this.lyricsResultsContainer.classList.add('hidden');
        }
        
        if (this.lyricsResults) {
            this.lyricsResults.innerHTML = '';
        }
        
        if (this.lyricPrompt) {
            this.lyricPrompt.value = '';
            this.updateLyricCharCount();
        }
        
        if (this.generateLyricsBtn) {
            this.generateLyricsBtn.disabled = false;
            this.generateLyricsBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">auto_awesome</span> Generate Lyrics';
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LyricGenerator;
} else {
    window.LyricGenerator = LyricGenerator;
}