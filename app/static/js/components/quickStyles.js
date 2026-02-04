/**
 * QuickStyles component for the Music Generator.
 * Provides a modal with searchable, categorized grid of style templates.
 */

class QuickStyles {
    constructor() {
        // DOM elements
        this.modal = null;
        this.browseBtn = null;
        this.closeBtn = null;
        this.cancelBtn = null;
        this.applySelectedBtn = null;
        this.searchInput = null;
        this.categoryFilter = null;
        this.templatesGrid = null;
        this.templatesLoading = null;
        this.templatesEmpty = null;
        this.templatesCount = null;
        this.cardTemplate = null;
        
        // Data
        this.allTemplates = [];
        this.filteredTemplates = [];
        this.selectedTemplate = null;
        
        // State
        this.isLoading = false;
        this.currentCategory = '';
        this.currentSearch = '';
        
        // Quick style mapping
        this.styleToTemplateId = {
            'cinematic': 'template_005',
            'lofi': 'template_003',
            'synthwave': 'template_001',
            'ambient': 'template_004',
            'jazz': 'template_008'
        };
        
        // Bind methods
        this.openModal = this.openModal.bind(this);
        this.closeModal = this.closeModal.bind(this);
        this.loadTemplates = this.loadTemplates.bind(this);
        this.renderTemplates = this.renderTemplates.bind(this);
        this.handleSearch = this.handleSearch.bind(this);
        this.handleCategoryChange = this.handleCategoryChange.bind(this);
        this.handleTemplateClick = this.handleTemplateClick.bind(this);
        this.applyTemplate = this.applyTemplate.bind(this);
        this.showNotification = this.showNotification.bind(this);
        this.setupQuickStyleButtons = this.setupQuickStyleButtons.bind(this);
        this.applyQuickStyle = this.applyQuickStyle.bind(this);
    }
    
    /**
     * Initialize QuickStyles component.
     */
    initialize() {
        this.cacheDomElements();
        this.setupEventListeners();
        this.setupQuickStyleButtons();
        console.log('QuickStyles component initialized.');
    }
    
    /**
     * Cache references to DOM elements.
     */
    cacheDomElements() {
        this.modal = document.getElementById('quickStylesModal');
        this.browseBtn = document.getElementById('browseTemplatesBtn');
        this.closeBtn = document.getElementById('closeQuickStylesModalBtn');
        this.cancelBtn = document.getElementById('cancelQuickStylesModalBtn');
        this.applySelectedBtn = document.getElementById('applySelectedTemplateBtn');
        this.searchInput = document.getElementById('templateSearch');
        this.categoryFilter = document.getElementById('templateCategory');
        this.templatesGrid = document.getElementById('templatesGrid');
        this.templatesLoading = document.getElementById('templatesLoading');
        this.templatesEmpty = document.getElementById('templatesEmpty');
        this.templatesCount = document.getElementById('templatesCount');
        this.cardTemplate = document.getElementById('templateCardTemplate');
        
        // Validate required elements
        if (!this.modal || !this.browseBtn) {
            console.error('Required DOM elements for QuickStyles not found.');
        }
    }
    
    /**
     * Set up event listeners.
     */
    setupEventListeners() {
        // Open modal
        if (this.browseBtn) {
            this.browseBtn.addEventListener('click', this.openModal);
        }
        
        // Close modal buttons
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', this.closeModal);
        }
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', this.closeModal);
        }
        
        // Apply selected template
        if (this.applySelectedBtn) {
            this.applySelectedBtn.addEventListener('click', () => {
                if (this.selectedTemplate) {
                    this.applyTemplate(this.selectedTemplate);
                }
            });
        }
        
        // Search input
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.handleSearch);
        }
        
        // Category filter
        if (this.categoryFilter) {
            this.categoryFilter.addEventListener('change', this.handleCategoryChange);
        }
        
        // Close modal on background click
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.closeModal();
                }
            });
        }
    }

    /**
     * Set up event listeners for inline quick style buttons.
     */
    setupQuickStyleButtons() {
        const buttons = document.querySelectorAll('.quick-style');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const style = e.target.dataset.style;
                if (style) {
                    this.applyQuickStyle(style);
                }
            });
        });
    }

    /**
     * Open the Quick Styles modal.
     */
    openModal() {
        if (!this.modal) return;
        
        // Reset selection
        this.selectedTemplate = null;
        this.applySelectedBtn.classList.add('hidden');
        
        // Show modal
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Load templates if not already loaded
        if (this.allTemplates.length === 0) {
            this.loadTemplates();
        } else {
            this.renderTemplates();
        }
    }
    
    /**
     * Close the Quick Styles modal.
     */
    closeModal() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
        // Reset filters
        if (this.searchInput) this.searchInput.value = '';
        if (this.categoryFilter) this.categoryFilter.value = '';
        this.currentSearch = '';
        this.currentCategory = '';
        // Clear selection
        this.selectedTemplate = null;
    }
    
    /**
     * Load templates from API.
     */
    async loadTemplates() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState(true);
        
        try {
            const response = await fetch('/api/templates?per_page=50');
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.allTemplates = data.data.templates || [];
                this.filteredTemplates = [...this.allTemplates];
                
                // Update UI
                this.updateTemplatesCount();
                this.renderTemplates();
                this.showLoadingState(false);
                
                // If no templates, show empty state
                if (this.allTemplates.length === 0) {
                    this.showEmptyState(true);
                } else {
                    this.showEmptyState(false);
                }
            } else {
                throw new Error(data.error || 'Failed to load templates');
            }
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showError('Failed to load templates. Please try again.');
            this.showLoadingState(false);
            this.showEmptyState(true);
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Show/hide loading state.
     * @param {boolean} show - Whether to show loading state
     */
    showLoadingState(show) {
        if (!this.templatesLoading || !this.templatesGrid || !this.templatesEmpty) return;
        
        if (show) {
            this.templatesLoading.classList.remove('hidden');
            this.templatesGrid.classList.add('hidden');
            this.templatesEmpty.classList.add('hidden');
        } else {
            this.templatesLoading.classList.add('hidden');
            this.templatesGrid.classList.remove('hidden');
        }
    }
    
    /**
     * Show/hide empty state.
     * @param {boolean} show - Whether to show empty state
     */
    showEmptyState(show) {
        if (!this.templatesEmpty || !this.templatesGrid) return;
        
        if (show) {
            this.templatesEmpty.classList.remove('hidden');
            this.templatesGrid.classList.add('hidden');
        } else {
            this.templatesEmpty.classList.add('hidden');
        }
    }
    
    /**
     * Update the templates count display.
     */
    updateTemplatesCount() {
        if (this.templatesCount) {
            this.templatesCount.textContent = this.filteredTemplates.length;
        }
    }
    
    /**
     * Render templates in the grid.
     */
    renderTemplates() {
        if (!this.templatesGrid || !this.cardTemplate) return;
        
        // Clear grid
        this.templatesGrid.innerHTML = '';
        
        // If no templates, show empty state
        if (this.filteredTemplates.length === 0) {
            this.showEmptyState(true);
            return;
        }
        
        // Create a card for each template
        this.filteredTemplates.forEach(template => {
            const card = this.createTemplateCard(template);
            this.templatesGrid.appendChild(card);
        });
        
        // Show grid
        this.templatesGrid.classList.remove('hidden');
        this.templatesEmpty.classList.add('hidden');
    }
    
    /**
     * Create a template card element.
     * @param {Object} template - Template object
     * @returns {HTMLElement} Template card element
     */
    createTemplateCard(template) {
        // Clone the template
        const card = this.cardTemplate.content.cloneNode(true).querySelector('.template-card');
        card.dataset.templateId = template.id;
        
        // Populate data
        const nameElem = card.querySelector('[data-template-name]');
        const categoryElem = card.querySelector('[data-template-category]');
        const bpmElem = card.querySelector('[data-template-bpm]');
        const descriptionElem = card.querySelector('[data-template-description]');
        const tagsContainer = card.querySelector('[data-template-tags]');
        const durationElem = card.querySelector('[data-template-duration]');
        const instrumentalElem = card.querySelector('[data-template-instrumental]');
        
        if (nameElem) nameElem.textContent = template.name;
        if (categoryElem) categoryElem.textContent = template.category;
        if (bpmElem) bpmElem.textContent = `${template.bpm || 120} BPM`;
        if (descriptionElem) descriptionElem.textContent = template.description;
        if (durationElem) durationElem.textContent = template.duration || '3:00';
        if (instrumentalElem) instrumentalElem.textContent = template.instrumental ? 'Instrumental' : 'With Vocals';
        
        // Render tags
        if (tagsContainer && template.tags && Array.isArray(template.tags)) {
            tagsContainer.innerHTML = '';
            template.tags.slice(0, 3).forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'inline-block px-2 py-1 rounded text-xs bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300';
                tagSpan.textContent = tag;
                tagsContainer.appendChild(tagSpan);
            });
        }
        
        // Apply button
        const applyBtn = card.querySelector('.apply-template-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleTemplateClick(template);
                this.applyTemplate(template);
            });
        }
        
        // Whole card click selects template (but does not apply)
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.apply-template-btn')) {
                this.handleTemplateClick(template);
            }
        });
        
        return card;
    }
    
    /**
     * Handle template selection (click on card).
     * @param {Object} template - Template object
     */
    handleTemplateClick(template) {
        // Remove previous selection
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('border-primary', 'ring-2', 'ring-primary/20');
            card.classList.add('border-slate-200', 'dark:border-border-dark');
        });
        
        // Highlight selected card
        const card = document.querySelector(`[data-template-id="${template.id}"]`);
        if (card) {
            card.classList.remove('border-slate-200', 'dark:border-border-dark');
            card.classList.add('border-primary', 'ring-2', 'ring-primary/20');
        }
        
        // Store selected template
        this.selectedTemplate = template;
        
        // Show apply selected button
        if (this.applySelectedBtn) {
            this.applySelectedBtn.classList.remove('hidden');
        }
    }
    
    /**
     * Apply a template to the music generator form.
     * @param {Object} template - Template object
     */
    applyTemplate(template) {
        // Apply to music prompt
        const musicPrompt = document.getElementById('musicPrompt');
        if (musicPrompt && template.prompt) {
            musicPrompt.value = template.prompt;
            musicPrompt.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Update character count if exists
            const promptChars = document.getElementById('musicPromptChars');
            if (promptChars) {
                promptChars.textContent = template.prompt.length;
            }
        }
        
        // Apply style input
        const styleInput = document.getElementById('styleInput');
        if (styleInput && template.style) {
            styleInput.value = template.style;
            styleInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            const styleChars = document.getElementById('styleChars');
            if (styleChars) {
                styleChars.textContent = template.style.length;
            }
        }
        
        // Apply instrumental toggle
        const instrumentalToggle = document.getElementById('instrumentalToggle');
        if (instrumentalToggle && template.instrumental !== undefined) {
            instrumentalToggle.checked = template.instrumental;
            instrumentalToggle.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Apply model if specified
        const modelSelect = document.getElementById('modelSelect');
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
        
        // Show notification
        this.showNotification(`"${template.name}" applied to music generator.`);
        
        // Close modal
        this.closeModal();
    }

    /**
     * Apply a quick style by fetching the corresponding template.
     * @param {string} style - Style identifier (cinematic, lofi, etc.)
     */
    async applyQuickStyle(style) {
        const templateId = this.styleToTemplateId[style];
        if (!templateId) {
            console.error(`No template mapping for style: ${style}`);
            return;
        }
        
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                const template = data.data.template;
                this.applyTemplate(template);
                this.showNotification(`"${template.name}" quick style applied.`);
            } else {
                throw new Error(data.error || 'Failed to load template');
            }
        } catch (error) {
            console.error(`Error applying quick style ${style}:`, error);
            this.showError(`Failed to apply quick style: ${error.message}`);
        }
    }
    
    /**
     * Handle search input.
     */
    handleSearch() {
        if (!this.searchInput) return;
        
        const searchTerm = this.searchInput.value.trim().toLowerCase();
        this.currentSearch = searchTerm;
        this.applyFilters();
    }
    
    /**
     * Handle category filter change.
     */
    handleCategoryChange() {
        if (!this.categoryFilter) return;
        
        const category = this.categoryFilter.value;
        this.currentCategory = category;
        this.applyFilters();
    }
    
    /**
     * Apply search and category filters.
     */
    applyFilters() {
        if (this.allTemplates.length === 0) return;
        
        let filtered = [...this.allTemplates];
        
        // Apply category filter
        if (this.currentCategory) {
            filtered = filtered.filter(template => 
                template.category === this.currentCategory ||
                template.subcategory === this.currentCategory
            );
        }
        
        // Apply search filter
        if (this.currentSearch) {
            filtered = filtered.filter(template => {
                const name = template.name?.toLowerCase() || '';
                const description = template.description?.toLowerCase() || '';
                const tags = template.tags?.map(tag => tag.toLowerCase()) || [];
                const style = template.style?.toLowerCase() || '';
                
                return name.includes(this.currentSearch) ||
                       description.includes(this.currentSearch) ||
                       tags.some(tag => tag.includes(this.currentSearch)) ||
                       style.includes(this.currentSearch);
            });
        }
        
        this.filteredTemplates = filtered;
        this.updateTemplatesCount();
        this.renderTemplates();
    }
    
    /**
     * Show error message.
     * @param {string} message - Error message
     */
    showError(message) {
        // Use existing notification system if available
        if (window.NotificationSystem && typeof window.NotificationSystem.showError === 'function') {
            window.NotificationSystem.showError(message);
        } else if (window.notificationSystem && window.notificationSystem.showError) {
            window.notificationSystem.showError(message);
        } else {
            console.error('QuickStyles error:', message);
            alert(message); // fallback
        }
    }
    
    /**
     * Show success notification.
     * @param {string} message - Notification message
     */
    showNotification(message) {
        // Use existing notification system if available
        if (window.NotificationSystem && typeof window.NotificationSystem.showSuccess === 'function') {
            window.NotificationSystem.showSuccess(message);
        } else if (window.notificationSystem && window.notificationSystem.showSuccess) {
            window.notificationSystem.showSuccess(message);
        } else {
            // Create a simple toast notification
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 z-50 bg-primary text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in';
            notification.innerHTML = `
                <span class="material-symbols-outlined">check_circle</span>
                <div>
                    <p class="font-medium">Template Applied</p>
                    <p class="text-sm opacity-90">${message}</p>
                </div>
                <button class="ml-auto text-white/80 hover:text-white" onclick="this.parentElement.remove()">
                    <span class="material-symbols-outlined">close</span>
                </button>
            `;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 5000);
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuickStyles;
} else {
    window.QuickStyles = QuickStyles;
}