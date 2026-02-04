/**
 * Template Data Loader Utility
 * Loads template data from sessionStorage and applies it to forms on page load.
 */

class TemplateDataLoader {
    /**
     * Initialize template data loader for music generator page.
     */
    static initializeForMusicGenerator() {
        console.log('Initializing template data loader for music generator...');
        
        // Check for template data in sessionStorage
        const templateData = sessionStorage.getItem('selectedMusicTemplate');
        
        if (templateData) {
            try {
                const template = JSON.parse(templateData);
                console.log('Found template data:', template.name);
                
                // Apply template to music generator form
                this.applyTemplateToMusicGenerator(template);
                
                // Clear the sessionStorage after applying
                sessionStorage.removeItem('selectedMusicTemplate');
                console.log('Template data applied and cleared from sessionStorage.');
                
                // Show notification
                this.showTemplateAppliedNotification(template.name, 'Music Generator');
            } catch (error) {
                console.error('Error parsing template data:', error);
                sessionStorage.removeItem('selectedMusicTemplate');
            }
        } else {
            console.log('No template data found in sessionStorage for music generator.');
        }
    }
    
    /**
     * Initialize template data loader for cover generator page.
     */
    static initializeForCoverGenerator() {
        console.log('Initializing template data loader for cover generator...');
        
        // Check for template data in sessionStorage
        const templateData = sessionStorage.getItem('selectedTemplate');
        
        if (templateData) {
            try {
                const template = JSON.parse(templateData);
                console.log('Found template data:', template.name);
                
                // Apply template to cover generator form
                this.applyTemplateToCoverGenerator(template);
                
                // Clear the sessionStorage after applying
                sessionStorage.removeItem('selectedTemplate');
                console.log('Template data applied and cleared from sessionStorage.');
                
                // Show notification
                this.showTemplateAppliedNotification(template.name, 'Cover Generator');
            } catch (error) {
                console.error('Error parsing template data:', error);
                sessionStorage.removeItem('selectedTemplate');
            }
        } else {
            console.log('No template data found in sessionStorage for cover generator.');
        }
    }
    
    /**
     * Apply template to music generator form.
     * @param {Object} template - Template object
     */
    static applyTemplateToMusicGenerator(template) {
        // Get form elements
        const musicPrompt = document.getElementById('musicPrompt');
        const instrumentalToggle = document.getElementById('instrumentalToggle');
        const vocalsToggle = document.getElementById('vocalsToggle');
        const charCount = document.getElementById('charCount');
        
        // Additional fields for music generator
        const promptInput = document.getElementById('promptInput');
        const styleInput = document.getElementById('styleInput');
        const titleInput = document.getElementById('titleInput');
        const modelSelect = document.getElementById('modelSelect');
        const vocalGender = document.getElementById('vocalGender');
        const negativeTags = document.getElementById('negativeTags');
        
        // Apply music description (main prompt)
        if (musicPrompt && template.prompt) {
            // Set the prompt text
            musicPrompt.value = template.prompt;
            
            // Update character count
            if (charCount) {
                charCount.textContent = template.prompt.length;
            }
            
            // Trigger input event for any listeners
            musicPrompt.dispatchEvent(new Event('input', { bubbles: true }));
            musicPrompt.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Apply style prompt (used for generation)
        if (promptInput && template.prompt) {
            promptInput.value = template.prompt;
            promptInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const promptChars = document.getElementById('promptChars');
            if (promptChars) {
                promptChars.textContent = template.prompt.length;
            }
        }
        
        // Apply style details
        if (styleInput && template.style) {
            styleInput.value = template.style;
            styleInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const styleChars = document.getElementById('styleChars');
            if (styleChars) {
                styleChars.textContent = template.style.length;
            }
        }
        
        // Apply title
        if (titleInput && template.name) {
            titleInput.value = template.name;
            titleInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const titleChars = document.getElementById('titleChars');
            if (titleChars) {
                titleChars.textContent = template.name.length;
            }
        }
        
        // Apply model if specified in metadata
        if (modelSelect && template.metadata && template.metadata.model) {
            const modelValue = template.metadata.model;
            for (let i = 0; i < modelSelect.options.length; i++) {
                if (modelSelect.options[i].value === modelValue) {
                    modelSelect.selectedIndex = i;
                    modelSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }
        
        // Apply vocal gender if specified
        if (vocalGender && template.metadata && template.metadata.vocalGender) {
            this.setSelectOrInputValue(vocalGender, template.metadata.vocalGender);
        }
        
        // Apply negative tags
        if (negativeTags && template.tags && Array.isArray(template.tags)) {
            negativeTags.value = template.tags.join(', ');
            negativeTags.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // Set instrumental toggle based on template data
        if (instrumentalToggle && template.instrumental !== undefined) {
            instrumentalToggle.checked = template.instrumental;
            instrumentalToggle.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Set vocals toggle (opposite of instrumental)
        if (vocalsToggle && template.instrumental !== undefined) {
            vocalsToggle.checked = !template.instrumental;
            vocalsToggle.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Enable custom mode to ensure style and title are used
        this.enableCustomMode();
        
        // Apply any additional template data
        this.applyAdditionalTemplateData(template);
    }
    
    /**
     * Enable custom mode in the music generator UI.
     */
    static enableCustomMode() {
        // Try to call global setMode function (from music generator page)
        if (typeof setMode === 'function') {
            setMode(true);
        }
        // Alternatively, click the custom mode button
        const customModeBtn = document.getElementById('customModeBtn');
        if (customModeBtn) {
            customModeBtn.click();
        }
        // Also ensure the mode manager is updated
        if (typeof modeManager !== 'undefined' && modeManager.setMode) {
            modeManager.setMode(true);
        }
    }
    
    /**
     * Apply template to cover generator form.
     * @param {Object} template - Template object
     */
    static applyTemplateToCoverGenerator(template) {
        // Get form elements
        const promptInput = document.getElementById('promptInput');
        const styleInput = document.getElementById('styleInput');
        const titleInput = document.getElementById('titleInput');
        const modelSelect = document.getElementById('modelSelect');
        const instrumentalToggle = document.getElementById('instrumentalToggle');
        
        // Apply prompt (intentionally left empty to allow custom lyrics)
        if (promptInput) {
            promptInput.value = '';
            promptInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // Apply style
        if (styleInput && template.style) {
            styleInput.value = template.style;
            styleInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const styleChars = document.getElementById('styleChars');
            if (styleChars) {
                styleChars.textContent = template.style.length;
            }
        }
        
        // Apply title
        if (titleInput && template.name) {
            titleInput.value = template.name;
            titleInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const titleChars = document.getElementById('titleChars');
            if (titleChars) {
                titleChars.textContent = template.name.length;
            }
        }
        
        // Apply model if specified in metadata
        if (modelSelect && template.metadata && template.metadata.model) {
            const modelValue = template.metadata.model;
            for (let i = 0; i < modelSelect.options.length; i++) {
                if (modelSelect.options[i].value === modelValue) {
                    modelSelect.selectedIndex = i;
                    modelSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }
        
        // Apply instrumental toggle
        if (instrumentalToggle && template.instrumental !== undefined) {
            instrumentalToggle.checked = template.instrumental;
            instrumentalToggle.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Apply any additional template data
        this.applyAdditionalTemplateData(template);
    }
    
    /**
     * Apply additional template data to any matching form fields.
     * @param {Object} template - Template object
     */
    static applyAdditionalTemplateData(template) {
        // Apply BPM if template has bpm field and there's a tempo input
        const tempoInput = document.getElementById('tempoInput') || document.getElementById('bpmInput');
        if (tempoInput && template.bpm) {
            tempoInput.value = template.bpm;
            tempoInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // Apply tags to style or description fields
        if (template.tags && Array.isArray(template.tags)) {
            const tagsString = template.tags.join(', ');
            
            // Try to find a tags input
            const tagsInput = document.getElementById('tagsInput') || document.getElementById('negativeTags');
            if (tagsInput) {
                tagsInput.value = tagsString;
                tagsInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        
        // Apply category/subcategory if relevant fields exist
        if (template.category) {
            const categoryInput = document.getElementById('categoryInput') || document.getElementById('genreSelect');
            if (categoryInput) {
                this.setSelectOrInputValue(categoryInput, template.category);
            }
        }
        
        if (template.subcategory) {
            const subcategoryInput = document.getElementById('subcategoryInput') || document.getElementById('styleSelect');
            if (subcategoryInput) {
                this.setSelectOrInputValue(subcategoryInput, template.subcategory);
            }
        }
    }
    
    /**
     * Set value for either select or input element.
     * @param {HTMLElement} element - Input or select element
     * @param {string} value - Value to set
     */
    static setSelectOrInputValue(element, value) {
        if (!element || !value) return;
        
        if (element.tagName === 'SELECT') {
            // For select elements
            for (let i = 0; i < element.options.length; i++) {
                if (element.options[i].value === value || 
                    element.options[i].text.toLowerCase() === value.toLowerCase()) {
                    element.selectedIndex = i;
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    return;
                }
            }
        } else {
            // For input/textarea elements
            element.value = value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
    
    /**
     * Show notification that template was applied.
     * @param {string} templateName - Template name
     * @param {string} pageName - Page name (Music Generator or Cover Generator)
     */
    static showTemplateAppliedNotification(templateName, pageName) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 z-50 bg-primary text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in';
        notification.innerHTML = `
            <span class="material-symbols-outlined">auto_awesome</span>
            <div>
                <p class="font-medium">Template Applied!</p>
                <p class="text-sm opacity-90">"${templateName}" has been applied to ${pageName}.</p>
            </div>
            <button class="ml-auto text-white/80 hover:text-white" onclick="this.parentElement.remove()">
                <span class="material-symbols-outlined">close</span>
            </button>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateDataLoader;
} else {
    window.TemplateDataLoader = TemplateDataLoader;
}