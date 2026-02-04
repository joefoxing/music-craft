/**
 * TemplateApplier component for the Music Cover Generator application.
 * Handles applying template data to the main form and managing template workflows.
 */

class TemplateApplier {
    constructor() {
        // DOM Elements (will be initialized by the main app)
        this.form = null;
        this.titleInput = null;
        this.artistInput = null;
        this.genreSelect = null;
        this.moodSelect = null;
        this.durationInput = null;
        this.tempoInput = null;
        this.keySelect = null;
        this.styleInput = null;
        this.instrumentsInput = null;
        this.lyricsTextarea = null;
        
        // Template modal elements
        this.templateModal = null;
        this.modalTitle = null;
        this.modalDescription = null;
        this.modalPreview = null;
        this.modalApplyBtn = null;
        this.modalCancelBtn = null;
        this.modalCloseBtn = null;
        
        // Current template
        this.currentTemplate = null;
        
        // Callbacks
        this.onTemplateApplied = null;
        this.onTemplatePreview = null;
    }

    /**
     * Initialize template applier with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        // Form elements
        this.form = elements.form;
        this.titleInput = elements.titleInput;
        this.artistInput = elements.artistInput;
        this.genreSelect = elements.genreSelect;
        this.moodSelect = elements.moodSelect;
        this.durationInput = elements.durationInput;
        this.tempoInput = elements.tempoInput;
        this.keySelect = elements.keySelect;
        this.styleInput = elements.styleInput;
        this.instrumentsInput = elements.instrumentsInput;
        this.lyricsTextarea = elements.lyricsTextarea;
        
        // Modal elements
        this.templateModal = elements.templateModal;
        this.modalTitle = elements.modalTitle;
        this.modalDescription = elements.modalDescription;
        this.modalPreview = elements.modalPreview;
        this.modalApplyBtn = elements.modalApplyBtn;
        this.modalCancelBtn = elements.modalCancelBtn;
        this.modalCloseBtn = elements.modalCloseBtn;

        this._setupEventListeners();
    }

    /**
     * Set up event listeners.
     * @private
     */
    _setupEventListeners() {
        // Modal buttons
        if (this.modalApplyBtn) {
            this.modalApplyBtn.addEventListener('click', () => this.applyCurrentTemplate());
        }

        if (this.modalCancelBtn) {
            this.modalCancelBtn.addEventListener('click', () => this.closeModal());
        }

        if (this.modalCloseBtn) {
            this.modalCloseBtn.addEventListener('click', () => this.closeModal());
        }

        // Close modal on background click
        if (this.templateModal) {
            this.templateModal.addEventListener('click', (e) => {
                if (e.target === this.templateModal) {
                    this.closeModal();
                }
            });
        }
    }

    /**
     * Show template preview modal.
     * @param {Object} template - Template object
     */
    showTemplatePreview(template) {
        if (!template || !this.templateModal) return;
        
        this.currentTemplate = template;
        
        // Update modal content
        if (this.modalTitle) {
            this.modalTitle.textContent = template.name;
        }
        
        if (this.modalDescription) {
            this.modalDescription.textContent = template.description;
        }
        
        if (this.modalPreview) {
            this.updateModalPreview(template);
        }
        
        // Show modal
        this.templateModal.classList.remove('hidden');
        
        // Call preview callback
        if (this.onTemplatePreview) {
            this.onTemplatePreview(template);
        }
    }

    /**
     * Update modal preview content.
     * @param {Object} template - Template object
     */
    updateModalPreview(template) {
        if (!this.modalPreview) return;
        
        const formData = this.getTemplateFormData(template);
        
        const previewHTML = `
            <div class="space-y-4">
                <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                    <h4 class="font-medium text-slate-900 dark:text-white mb-2">Template Details</h4>
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div>
                            <span class="text-slate-500 dark:text-slate-400">Category:</span>
                            <span class="ml-2 text-slate-900 dark:text-white">${this.formatCategoryName(template.category)}</span>
                        </div>
                        <div>
                            <span class="text-slate-500 dark:text-slate-400">Difficulty:</span>
                            <span class="ml-2 text-slate-900 dark:text-white">${this.formatDifficultyText(template.difficulty)}</span>
                        </div>
                        <div>
                            <span class="text-slate-500 dark:text-slate-400">Estimated Time:</span>
                            <span class="ml-2 text-slate-900 dark:text-white">${template.estimated_time || '5-10'} minutes</span>
                        </div>
                        <div>
                            <span class="text-slate-500 dark:text-slate-400">Popularity:</span>
                            <span class="ml-2 text-slate-900 dark:text-white">${template.popularity}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                    <h4 class="font-medium text-slate-900 dark:text-white mb-2">Form Data Preview</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Title:</span>
                            <span class="text-slate-900 dark:text-white">${formData.title}</span>
                        </div>
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Artist:</span>
                            <span class="text-slate-900 dark:text-white">${formData.artist}</span>
                        </div>
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Genre:</span>
                            <span class="text-slate-900 dark:text-white">${formData.genre}</span>
                        </div>
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Mood:</span>
                            <span class="text-slate-900 dark:text-white">${formData.mood}</span>
                        </div>
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Duration:</span>
                            <span class="text-slate-900 dark:text-white">${formData.duration}</span>
                        </div>
                        <div class="flex">
                            <span class="w-24 text-slate-500 dark:text-slate-400">Tempo:</span>
                            <span class="text-slate-900 dark:text-white">${formData.tempo} BPM</span>
                        </div>
                    </div>
                </div>
                
                ${template.tags && template.tags.length ? `
                <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                    <h4 class="font-medium text-slate-900 dark:text-white mb-2">Tags</h4>
                    <div class="flex flex-wrap gap-2">
                        ${template.tags.map(tag => `
                            <span class="inline-block px-2 py-1 rounded text-xs bg-primary/10 text-primary dark:bg-primary/20">
                                ${tag}
                            </span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${template.notes ? `
                <div class="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                    <h4 class="font-medium text-amber-900 dark:text-amber-300 mb-2 flex items-center gap-2">
                        <span class="material-symbols-outlined text-sm">lightbulb</span>
                        Template Notes
                    </h4>
                    <p class="text-sm text-amber-800 dark:text-amber-400">${template.notes}</p>
                </div>
                ` : ''}
            </div>
        `;
        
        this.modalPreview.innerHTML = previewHTML;
    }

    /**
     * Apply current template to form.
     */
    applyCurrentTemplate() {
        if (!this.currentTemplate) return;
        
        const formData = this.getTemplateFormData(this.currentTemplate);
        this.applyFormData(formData);
        
        // Close modal
        this.closeModal();
        
        // Call applied callback
        if (this.onTemplateApplied) {
            this.onTemplateApplied(this.currentTemplate, formData);
        }
        
        // Show success notification
        this.showSuccessNotification(this.currentTemplate.name);
    }

    /**
     * Apply template by ID.
     * @param {string} templateId - Template ID
     * @returns {Promise<boolean>} Success status
     */
    async applyTemplateById(templateId) {
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                const template = data.template;
                const formData = this.getTemplateFormData(template);
                this.applyFormData(formData);
                
                // Call applied callback
                if (this.onTemplateApplied) {
                    this.onTemplateApplied(template, formData);
                }
                
                this.showSuccessNotification(template.name);
                return true;
            } else {
                throw new Error(data.error || 'Failed to load template');
            }
        } catch (error) {
            console.error('Error applying template:', error);
            this.showErrorNotification(`Failed to apply template: ${error.message}`);
            return false;
        }
    }

    /**
     * Get form data from template.
     * @param {Object} template - Template object
     * @returns {Object} Form data
     */
    getTemplateFormData(template) {
        // Use template's form_data if available, otherwise generate from template metadata
        if (template.form_data && typeof template.form_data === 'object') {
            return {
                title: template.form_data.title || template.name,
                artist: template.form_data.artist || 'Various Artists',
                genre: template.form_data.genre || template.category,
                mood: template.form_data.mood || template.tags?.[0] || 'energetic',
                duration: template.form_data.duration || '3:00',
                tempo: template.form_data.tempo || '120',
                key: template.form_data.key || 'C',
                style: template.form_data.style || template.subcategory,
                instruments: template.form_data.instruments || template.tags?.join(', ') || '',
                lyrics: template.form_data.lyrics || ''
            };
        }
        
        // Generate form data from template metadata
        return {
            title: template.name,
            artist: 'Various Artists',
            genre: template.category,
            mood: template.tags?.[0] || 'energetic',
            duration: '3:00',
            tempo: '120',
            key: 'C',
            style: template.subcategory,
            instruments: template.tags?.join(', ') || '',
            lyrics: ''
        };
    }

    /**
     * Apply form data to input fields.
     * @param {Object} formData - Form data object
     */
    applyFormData(formData) {
        if (!formData) return;
        
        // Apply to each input field if element exists
        if (this.titleInput && formData.title) {
            this.titleInput.value = formData.title;
            this.triggerInputChange(this.titleInput);
        }
        
        if (this.artistInput && formData.artist) {
            this.artistInput.value = formData.artist;
            this.triggerInputChange(this.artistInput);
        }
        
        if (this.genreSelect && formData.genre) {
            this.setSelectValue(this.genreSelect, formData.genre);
        }
        
        if (this.moodSelect && formData.mood) {
            this.setSelectValue(this.moodSelect, formData.mood);
        }
        
        if (this.durationInput && formData.duration) {
            this.durationInput.value = formData.duration;
            this.triggerInputChange(this.durationInput);
        }
        
        if (this.tempoInput && formData.tempo) {
            this.tempoInput.value = formData.tempo;
            this.triggerInputChange(this.tempoInput);
        }
        
        if (this.keySelect && formData.key) {
            this.setSelectValue(this.keySelect, formData.key);
        }
        
        if (this.styleInput && formData.style) {
            this.styleInput.value = formData.style;
            this.triggerInputChange(this.styleInput);
        }
        
        if (this.instrumentsInput && formData.instruments) {
            this.instrumentsInput.value = formData.instruments;
            this.triggerInputChange(this.instrumentsInput);
        }
        
        if (this.lyricsTextarea && formData.lyrics) {
            this.lyricsTextarea.value = formData.lyrics;
            this.triggerInputChange(this.lyricsTextarea);
        }
        
        // Focus on title input for user convenience
        if (this.titleInput) {
            this.titleInput.focus();
        }
    }

    /**
     * Set select element value.
     * @param {HTMLSelectElement} select - Select element
     * @param {string} value - Value to set
     */
    setSelectValue(select, value) {
        if (!select) return;
        
        // Try exact match first
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === value) {
                select.selectedIndex = i;
                this.triggerInputChange(select);
                return;
            }
        }
        
        // Try case-insensitive match
        const lowerValue = value.toLowerCase();
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value.toLowerCase() === lowerValue) {
                select.selectedIndex = i;
                this.triggerInputChange(select);
                return;
            }
        }
        
        // If no match found, set first option
        if (select.options.length > 0) {
            select.selectedIndex = 0;
            this.triggerInputChange(select);
        }
    }

    /**
     * Trigger input change event.
     * @param {HTMLElement} element - Input element
     */
    triggerInputChange(element) {
        if (!element) return;
        
        // Dispatch change event
        element.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Also dispatch input event for real-time validation
        element.dispatchEvent(new Event('input', { bubbles: true }));
    }

    /**
     * Close template modal.
     */
    closeModal() {
        if (this.templateModal) {
            this.templateModal.classList.add('hidden');
        }
        this.currentTemplate = null;
    }

    /**
     * Show success notification.
     * @param {string} templateName - Template name
     */
    showSuccessNotification(templateName) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 z-50 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in';
        notification.innerHTML = `
            <span class="material-symbols-outlined">check_circle</span>
            <div>
                <p class="font-medium">Template Applied!</p>
                <p class="text-sm opacity-90">"${templateName}" has been applied to the form.</p>
            </div>
            <button class="ml-auto text-white/80 hover:text-white">
                <span class="material-symbols-outlined">close</span>
            </button>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Add close button event
        const closeBtn = notification.querySelector('button');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Show error notification.
     * @param {string} message - Error message
     */
    showErrorNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 z-50 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in';
        notification.innerHTML = `
            <span class="material-symbols-outlined">error</span>
            <div>
                <p class="font-medium">Template Error</p>
                <p class="text-sm opacity-90">${message}</p>
            </div>
            <button class="ml-auto text-white/80 hover:text-white">
                <span class="material-symbols-outlined">close</span>
            </button>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Add close button event
        const closeBtn = notification.querySelector('button');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Format category name for display.
     * @param {string} category - Category name
     * @returns {string} Formatted category name
     */
    formatCategoryName(category) {
        return category
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Format difficulty text.
     * @param {string} difficulty - Difficulty level
     * @returns {string} Formatted difficulty text
     */
    formatDifficultyText(difficulty) {
        const texts = {
            'beginner': 'Beginner',
            'easy': 'Easy',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'expert': 'Expert'
        };
        
        return texts[difficulty] || difficulty;
    }

    /**
     * Set callback for template applied.
     * @param {Function} callback - Callback function with template and formData parameters
     */
    setOnTemplateApplied(callback) {
        this.onTemplateApplied = callback;
    }

    /**
     * Set callback for template preview.
     * @param {Function} callback - Callback function with template parameter
     */
    setOnTemplatePreview(callback) {
        this.onTemplatePreview = callback;
    }

    /**
     * Get current template.
     * @returns {Object|null} Current template object
     */
    getCurrentTemplate() {
        return this.currentTemplate;
    }

    /**
     * Clear form data.
     */
    clearForm() {
        if (this.titleInput) this.titleInput.value = '';
        if (this.artistInput) this.artistInput.value = '';
        if (this.genreSelect) this.genreSelect.selectedIndex = 0;
        if (this.moodSelect) this.moodSelect.selectedIndex = 0;
        if (this.durationInput) this.durationInput.value = '3:00';
        if (this.tempoInput) this.tempoInput.value = '120';
        if (this.keySelect) this.keySelect.selectedIndex = 0;
        if (this.styleInput) this.styleInput.value = '';
        if (this.instrumentsInput) this.instrumentsInput.value = '';
        if (this.lyricsTextarea) this.lyricsTextarea.value = '';
        
        // Trigger change events
        if (this.titleInput) this.triggerInputChange(this.titleInput);
        if (this.artistInput) this.triggerInputChange(this.artistInput);
        if (this.genreSelect) this.triggerInputChange(this.genreSelect);
        if (this.moodSelect) this.triggerInputChange(this.moodSelect);
        if (this.durationInput) this.triggerInputChange(this.durationInput);
        if (this.tempoInput) this.triggerInputChange(this.tempoInput);
        if (this.keySelect) this.triggerInputChange(this.keySelect);
        if (this.styleInput) this.triggerInputChange(this.styleInput);
        if (this.instrumentsInput) this.triggerInputChange(this.instrumentsInput);
        if (this.lyricsTextarea) this.triggerInputChange(this.lyricsTextarea);
    }

    /**
     * Get current form data.
     * @returns {Object} Current form data
     */
    getFormData() {
        return {
            title: this.titleInput?.value || '',
            artist: this.artistInput?.value || '',
            genre: this.genreSelect?.value || '',
            mood: this.moodSelect?.value || '',
            duration: this.durationInput?.value || '',
            tempo: this.tempoInput?.value || '',
            key: this.keySelect?.value || '',
            style: this.styleInput?.value || '',
            instruments: this.instrumentsInput?.value || '',
            lyrics: this.lyricsTextarea?.value || ''
        };
    }

    /**
     * Validate form data.
     * @returns {Object} Validation result with isValid and errors
     */
    validateForm() {
        const errors = [];
        const formData = this.getFormData();
        
        if (!formData.title?.trim()) {
            errors.push('Title is required');
        }
        
        if (!formData.artist?.trim()) {
            errors.push('Artist is required');
        }
        
        if (!formData.genre) {
            errors.push('Genre is required');
        }
        
        if (!formData.mood) {
            errors.push('Mood is required');
        }
        
        // Validate duration format (MM:SS)
        if (formData.duration && !/^\d{1,2}:\d{2}$/.test(formData.duration)) {
            errors.push('Duration must be in MM:SS format');
        }
        
        // Validate tempo (numeric, 40-240)
        if (formData.tempo) {
            const tempo = parseInt(formData.tempo, 10);
            if (isNaN(tempo) || tempo < 40 || tempo > 240) {
                errors.push('Tempo must be between 40 and 240 BPM');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors,
            formData: formData
        };
    }

    /**
     * Show form validation errors.
     * @param {Array} errors - Error messages
     */
    showValidationErrors(errors) {
        if (!errors || !errors.length) return;
        
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 z-50 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg animate-slide-in';
        notification.innerHTML = `
            <div class="flex items-start gap-3">
                <span class="material-symbols-outlined">error</span>
                <div>
                    <p class="font-medium">Form Validation Errors</p>
                    <ul class="text-sm opacity-90 mt-1 space-y-1">
                        ${errors.map(error => `<li>• ${error}</li>`).join('')}
                    </ul>
                </div>
                <button class="ml-auto text-white/80 hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Add close button event
        const closeBtn = notification.querySelector('button');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 8000);
    }

    /**
     * Highlight invalid form fields.
     * @param {Array} errors - Error messages
     */
    highlightInvalidFields(errors) {
        // Reset all field styles first
        const fields = [
            this.titleInput, this.artistInput, this.genreSelect,
            this.moodSelect, this.durationInput, this.tempoInput
        ];
        
        fields.forEach(field => {
            if (field) {
                field.classList.remove('border-red-500', 'ring-2', 'ring-red-500/20');
            }
        });
        
        // Apply error styles based on errors
        if (errors.includes('Title is required') && this.titleInput) {
            this.titleInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
        
        if (errors.includes('Artist is required') && this.artistInput) {
            this.artistInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
        
        if (errors.includes('Genre is required') && this.genreSelect) {
            this.genreSelect.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
        
        if (errors.includes('Mood is required') && this.moodSelect) {
            this.moodSelect.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
        
        if (errors.includes('Duration must be in MM:SS format') && this.durationInput) {
            this.durationInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
        
        if (errors.includes('Tempo must be between 40 and 240 BPM') && this.tempoInput) {
            this.tempoInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateApplier;
} else {
    window.TemplateApplier = TemplateApplier;
}