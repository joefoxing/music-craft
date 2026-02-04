/**
 * Mode and model management for the Music Cover Generator application.
 * Handles mode switching, model selection, and character counters.
 */

class ModeManager {
    constructor() {
        this.currentMode = false; // false = simple, true = custom
        this.currentTaskType = 'cover'; // 'cover' or 'extend'
        this.currentModel = 'V5';
        
        // DOM Elements (will be initialized by the main app)
        this.coverTaskBtn = null;
        this.extendTaskBtn = null;
        this.continueAtField = null;
        this.continueAtInput = null;
        this.taskTypeHelp = null;
        
        this.simpleModeBtn = null;
        this.customModeBtn = null;
        this.customFields = null;
        this.modeHelp = null;
        this.modelSelect = null;
        this.promptInput = null;
        this.promptChars = null;
        this.promptMax = null;
        this.styleInput = null;
        this.styleChars = null;
        this.styleMax = null;
        this.titleInput = null;
        this.titleChars = null;
        this.titleMax = null;
        this.instrumentalToggle = null;
    }

    /**
     * Initialize mode manager with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        console.log('ModeManager initializing with elements:', elements);
        this.coverTaskBtn = elements.coverTaskBtn;
        this.extendTaskBtn = elements.extendTaskBtn;
        this.continueAtField = elements.continueAtField;
        this.continueAtInput = elements.continueAtInput;
        this.taskTypeHelp = elements.taskTypeHelp;
        
        this.simpleModeBtn = elements.simpleModeBtn;
        this.customModeBtn = elements.customModeBtn;
        this.customFields = elements.customFields;
        this.modeHelp = elements.modeHelp;
        this.modelSelect = elements.modelSelect;
        this.promptInput = elements.promptInput;
        this.promptChars = elements.promptChars;
        this.promptMax = elements.promptMax;
        this.styleInput = elements.styleInput;
        this.styleChars = elements.styleChars;
        this.styleMax = elements.styleMax;
        this.titleInput = elements.titleInput;
        this.titleChars = elements.titleChars;
        this.titleMax = elements.titleMax;
        this.instrumentalToggle = elements.instrumentalToggle;

        this._setupEventListeners();
        this._initializeDefaults();
    }

    /**
     * Set up event listeners.
     * @private
     */
    _setupEventListeners() {
        console.log('ModeManager: Setting up event listeners');
        
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', this.updateModelLimits.bind(this));
            console.log('ModeManager: Added listener for modelSelect');
        } else {
            console.warn('ModeManager: modelSelect element not found');
        }

        if (this.promptInput) {
            this.promptInput.addEventListener('input', this.updatePromptCounter.bind(this));
        }

        if (this.styleInput) {
            this.styleInput.addEventListener('input', this.updateStyleCounter.bind(this));
        }

        if (this.titleInput) {
            this.titleInput.addEventListener('input', this.updateTitleCounter.bind(this));
        }

        if (this.simpleModeBtn) {
            this.simpleModeBtn.addEventListener('click', () => this.setMode(false));
            console.log('ModeManager: Added listener for simpleModeBtn');
        } else {
            console.warn('ModeManager: simpleModeBtn element not found');
        }

        if (this.customModeBtn) {
            this.customModeBtn.addEventListener('click', () => this.setMode(true));
            console.log('ModeManager: Added listener for customModeBtn');
        } else {
            console.warn('ModeManager: customModeBtn element not found');
        }
        
        if (this.coverTaskBtn) {
            this.coverTaskBtn.addEventListener('click', () => this.setTaskType('cover'));
            console.log('ModeManager: Added listener for coverTaskBtn');
        } else {
            console.warn('ModeManager: coverTaskBtn element not found');
        }
        
        if (this.extendTaskBtn) {
            this.extendTaskBtn.addEventListener('click', () => this.setTaskType('extend'));
            console.log('ModeManager: Added listener for extendTaskBtn');
        } else {
            console.warn('ModeManager: extendTaskBtn element not found - this is likely the issue!');
            // Try to find the element again
            this.extendTaskBtn = document.getElementById('extendTaskBtn');
            if (this.extendTaskBtn) {
                console.log('ModeManager: Found extendTaskBtn on second attempt, adding listener');
                this.extendTaskBtn.addEventListener('click', () => this.setTaskType('extend'));
            } else {
                console.error('ModeManager: extendTaskBtn still not found after second attempt');
            }
        }
    }

    /**
     * Initialize default values.
     * @private
     */
    _initializeDefaults() {
        if (this.promptMax) this.promptMax.textContent = '500';
        if (this.styleMax) this.styleMax.textContent = '200';
        if (this.titleMax) this.titleMax.textContent = '80';
        
        if (this.modelSelect) this.updateModelLimits();
        if (this.promptInput) this.updatePromptCounter();
        if (this.styleInput) this.updateStyleCounter();
        if (this.titleInput) this.updateTitleCounter();
    }

    /**
     * Set the current task type.
     * @param {string} type - 'cover' or 'extend'
     */
    setTaskType(type) {
        console.log('ModeManager.setTaskType called with:', type, 'from stack:', new Error().stack);
        this.currentTaskType = type;
        
        // Ensure elements are available (lazy load if missing)
        if (!this.coverTaskBtn) {
            this.coverTaskBtn = document.getElementById('coverTaskBtn');
            console.log('ModeManager: Lazily loaded coverTaskBtn:', this.coverTaskBtn);
        }
        if (!this.extendTaskBtn) {
            this.extendTaskBtn = document.getElementById('extendTaskBtn');
            console.log('ModeManager: Lazily loaded extendTaskBtn:', this.extendTaskBtn);
        }
        if (!this.continueAtField) {
            this.continueAtField = document.getElementById('continueAtField');
            console.log('ModeManager: Lazily loaded continueAtField:', this.continueAtField);
        }
        if (!this.taskTypeHelp) {
            this.taskTypeHelp = document.getElementById('taskTypeHelp');
            console.log('ModeManager: Lazily loaded taskTypeHelp:', this.taskTypeHelp);
        }
        
        // Debug element existence
        if (!this.coverTaskBtn) console.warn('coverTaskBtn element missing');
        if (!this.extendTaskBtn) console.warn('extendTaskBtn element missing');
        if (!this.continueAtField) console.warn('continueAtField element missing');

        if (type === 'extend') {
            console.log('Activating Extend mode UI');
            if (this.coverTaskBtn) {
                this.coverTaskBtn.classList.remove('active');
                console.log('ModeManager: Removed active class from coverTaskBtn');
            }
            if (this.extendTaskBtn) {
                this.extendTaskBtn.classList.add('active');
                console.log('ModeManager: Added active class to extendTaskBtn');
            }
            
            if (this.continueAtField) {
                this.continueAtField.classList.remove('hidden');
                console.log('Removed hidden class from continueAtField');
            } else {
                console.warn('ModeManager: continueAtField is null, cannot show it');
            }
            
            if (this.taskTypeHelp) this.taskTypeHelp.textContent = 'Extend: Continue the music from a specific point.';
        } else {
            console.log('Activating Cover mode UI');
            if (this.coverTaskBtn) {
                this.coverTaskBtn.classList.add('active');
                console.log('ModeManager: Added active class to coverTaskBtn');
            }
            if (this.extendTaskBtn) {
                this.extendTaskBtn.classList.remove('active');
                console.log('ModeManager: Removed active class from extendTaskBtn');
            }
            
            if (this.continueAtField) {
                this.continueAtField.classList.add('hidden');
                console.log('ModeManager: Added hidden class to continueAtField');
            }
            
            if (this.taskTypeHelp) this.taskTypeHelp.textContent = 'Cover: Create a new version/remix.';
        }
    }

    /**
     * Set the current mode.
     * @param {boolean} isCustom - true for custom mode, false for simple mode
     */
    setMode(isCustom) {
        this.currentMode = isCustom;
        
        if (isCustom) {
            if (this.simpleModeBtn) this.simpleModeBtn.classList.remove('active');
            if (this.customModeBtn) this.customModeBtn.classList.add('active');
            if (this.customFields) this.customFields.classList.remove('hidden');
            if (this.modeHelp) this.modeHelp.textContent = 'Custom Mode: Full control over style, title, and lyrics.';
            this.updatePromptMaxForModel();
        } else {
            if (this.simpleModeBtn) this.simpleModeBtn.classList.add('active');
            if (this.customModeBtn) this.customModeBtn.classList.remove('active');
            if (this.customFields) this.customFields.classList.add('hidden');
            if (this.modeHelp) this.modeHelp.textContent = 'Simple Mode: Just provide a prompt, lyrics will be auto-generated.';
            if (this.promptMax) this.promptMax.textContent = '500';
            this.updatePromptCounter();
        }
    }

    /**
     * Update model limits based on selected model.
     */
    updateModelLimits() {
        if (!this.modelSelect) return;
        
        this.currentModel = this.modelSelect.value;
        const limits = this._getModelLimits();
        const modelLimits = limits[this.currentModel];
        
        if (this.currentMode) {
            if (this.promptMax) this.promptMax.textContent = modelLimits.prompt;
            if (this.styleMax) this.styleMax.textContent = modelLimits.style;
            if (this.titleMax) this.titleMax.textContent = modelLimits.title;
        } else {
            if (this.promptMax) this.promptMax.textContent = '500';
        }
        
        this.updatePromptCounter();
        this.updateStyleCounter();
        this.updateTitleCounter();
    }

    /**
     * Update prompt max length for current model.
     */
    updatePromptMaxForModel() {
        const limits = this._getModelLimits();
        const promptLimit = limits[this.currentModel].prompt;
        
        if (this.promptMax) this.promptMax.textContent = promptLimit;
        this.updatePromptCounter();
    }

    /**
     * Update prompt character counter.
     */
    updatePromptCounter() {
        if (!this.promptInput || !this.promptChars) return;
        
        const length = this.promptInput.value.length;
        const max = parseInt(this.promptMax?.textContent || '500');
        
        this.promptChars.textContent = length;
        this._updateCounterColor(this.promptChars, length, max);
    }

    /**
     * Update style character counter.
     */
    updateStyleCounter() {
        if (!this.styleInput || !this.styleChars) return;
        
        const length = this.styleInput.value.length;
        const max = parseInt(this.styleMax?.textContent || '200');
        
        this.styleChars.textContent = length;
        this._updateCounterColor(this.styleChars, length, max);
    }

    /**
     * Update title character counter.
     */
    updateTitleCounter() {
        if (!this.titleInput || !this.titleChars) return;
        
        const length = this.titleInput.value.length;
        const max = parseInt(this.titleMax?.textContent || '80');
        
        this.titleChars.textContent = length;
        this._updateCounterColor(this.titleChars, length, max);
    }

    /**
     * Update counter color based on length.
     * @private
     */
    _updateCounterColor(element, length, max) {
        if (!element) return;
        
        if (length > max) {
            element.style.color = '#ef4444';
        } else if (length > max * 0.8) {
            element.style.color = '#f59e0b';
        } else {
            element.style.color = '#64748b';
        }
    }

    /**
     * Get model limits configuration.
     * @private
     */
    _getModelLimits() {
        return {
            'V5': { prompt: 5000, style: 1000, title: 100 },
            'V4_5PLUS': { prompt: 5000, style: 1000, title: 100 },
            'V4_5': { prompt: 5000, style: 1000, title: 100 },
            'V4_5ALL': { prompt: 5000, style: 1000, title: 80 },
            'V4': { prompt: 3000, style: 200, title: 80 }
        };
    }

    /**
     * Get the current mode.
     * @returns {boolean} true for custom mode, false for simple mode
     */
    getCurrentMode() {
        return this.currentMode;
    }

    /**
     * Get the current model.
     * @returns {string} The current model name
     */
    getCurrentModel() {
        return this.currentModel;
    }

    /**
     * Get the current prompt value.
     * @returns {string} The prompt text
     */
    getPrompt() {
        return this.promptInput?.value.trim() || '';
    }

    /**
     * Get the current style value.
     * @returns {string} The style text
     */
    getStyle() {
        return this.styleInput?.value.trim() || '';
    }

    /**
     * Get the current title value.
     * @returns {string} The title text
     */
    getTitle() {
        return this.titleInput?.value.trim() || '';
    }

    /**
     * Check if instrumental mode is enabled.
     * @returns {boolean} true if instrumental mode is enabled
     */
    isInstrumental() {
        return this.instrumentalToggle?.checked || false;
    }

    /**
     * Get continue_at value.
     * @returns {number|null} Continue at timestamp in seconds
     */
    getContinueAt() {
        if (this.currentTaskType !== 'extend') return null;
        return this.continueAtInput ? parseInt(this.continueAtInput.value) : 60;
    }

    /**
     * Validate the current input values.
     * @returns {Object} Validation result with isValid and message properties
     */
    validateInputs() {
        const prompt = this.getPrompt();
        const promptLength = prompt.length;
        const promptMaxLength = parseInt(this.promptMax?.textContent || '500');
        
        if (!prompt) {
            return { isValid: false, message: 'Please enter a prompt' };
        }
        
        if (promptLength > promptMaxLength) {
            return {
                isValid: false,
                message: `Prompt exceeds ${promptMaxLength} character limit`
            };
        }

        if (this.currentTaskType === 'extend') {
            const continueAt = this.getContinueAt();
            if (isNaN(continueAt) || continueAt < 0) {
                return { isValid: false, message: 'Please enter a valid continue time (seconds)' };
            }
        }
        
        if (this.currentMode) {
            const style = this.getStyle();
            const styleLength = style.length;
            const styleMaxLength = parseInt(this.styleMax?.textContent || '200');
            const title = this.getTitle();
            const titleLength = title.length;
            const titleMaxLength = parseInt(this.titleMax?.textContent || '80');
            
            if (!style) {
                return { isValid: false, message: 'Please enter a style for custom mode' };
            }
            
            if (!title) {
                return { isValid: false, message: 'Please enter a title for custom mode' };
            }
            
            if (styleLength > styleMaxLength) {
                return { 
                    isValid: false, 
                    message: `Style exceeds ${styleMaxLength} character limit` 
                };
            }
            
            if (titleLength > titleMaxLength) {
                return { 
                    isValid: false, 
                    message: `Title exceeds ${titleMaxLength} character limit` 
                };
            }
        }
        
        return { isValid: true, message: 'Inputs are valid' };
    }

    /**
     * Get generation parameters for API request.
     * @returns {Object} Generation parameters
     */
    getGenerationParameters() {
        const params = {
            prompt: this.getPrompt(),
            custom_mode: this.currentMode,
            instrumental: this.isInstrumental(),
            model: this.currentModel,
            task_type: this.currentTaskType
        };

        if (this.currentTaskType === 'extend') {
            params.continue_at = this.getContinueAt();
            // Default param flag for extend tasks (True by default as per sample code)
            params.default_param_flag = true;
        }
        
        if (this.currentMode) {
            params.style = this.getStyle();
            params.title = this.getTitle();
            
            // Optional parameters
            const vocalGender = document.getElementById('vocalGender')?.value;
            const negativeTags = document.getElementById('negativeTags')?.value;
            if (vocalGender) params.vocal_gender = vocalGender;
            if (negativeTags) params.negative_tags = negativeTags;
            
            // Advanced optional parameters (from sample code)
            // These could be added as UI fields in the future
            const styleWeight = document.getElementById('styleWeight')?.value;
            const weirdnessConstraint = document.getElementById('weirdnessConstraint')?.value;
            const audioWeight = document.getElementById('audioWeight')?.value;
            const personaId = document.getElementById('personaId')?.value;
            
            if (styleWeight) params.style_weight = parseFloat(styleWeight);
            if (weirdnessConstraint) params.weirdness_constraint = parseFloat(weirdnessConstraint);
            if (audioWeight) params.audio_weight = parseFloat(audioWeight);
            if (personaId) params.persona_id = personaId;
        }
        
        return params;
    }

    /**
     * Reset all inputs to default values.
     */
    resetInputs() {
        if (this.promptInput) this.promptInput.value = '';
        if (this.styleInput) this.styleInput.value = '';
        if (this.titleInput) this.titleInput.value = '';
        if (this.instrumentalToggle) this.instrumentalToggle.checked = false;
        
        this.updatePromptCounter();
        this.updateStyleCounter();
        this.updateTitleCounter();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModeManager;
} else {
    window.ModeManager = ModeManager;
}