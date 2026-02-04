/**
 * TemplateGallery component for the Music Cover Generator application.
 * Displays and filters music generation templates.
 */

console.log('TemplateGallery script loaded');

class TemplateGallery {
    constructor() {
        this.allTemplates = [];
        this.filteredTemplates = [];
        
        // DOM Elements (will be initialized by the main app)
        this.galleryContainer = null;
        this.loadingState = null;
        this.emptyState = null;
        this.errorState = null;
        this.refreshBtn = null;
        this.searchInput = null;
        this.categoryFilter = null;
        this.subcategoryFilter = null;
        this.difficultyFilter = null;
        this.sortSelect = null;
        this.statsTotal = null;
        this.statsPopular = null;
        this.statsEasy = null;
        this.statsAdvanced = null;
        
        // Pagination
        this.currentPage = 1;
        this.pageSize = 12;
        this.hasMore = true;
        
        // Callbacks
        this.onTemplateSelect = null;
        this.onTemplateApply = null;
        this.onTemplateApplyWithMusicGenerator = null;
        this.onTemplateApplyWithCoverGenerator = null;
        
        // Filter options
        this.categories = [];
        this.subcategories = [];
        
        // Active context menu tracking
        this.activeContextMenu = null;
    }

    /**
     * Initialize template gallery with DOM elements.
     * @param {Object} elements - DOM element references
     */
    initialize(elements) {
        this.galleryContainer = elements.galleryContainer;
        this.loadingState = elements.loadingState;
        this.emptyState = elements.emptyState;
        this.errorState = elements.errorState;
        this.refreshBtn = elements.refreshBtn;
        this.searchInput = elements.searchInput;
        this.categoryFilter = elements.categoryFilter;
        this.subcategoryFilter = elements.subcategoryFilter;
        this.difficultyFilter = elements.difficultyFilter;
        this.sortSelect = elements.sortSelect;
        this.statsTotal = elements.statsTotal;
        this.statsPopular = elements.statsPopular;
        this.statsEasy = elements.statsEasy;
        this.statsAdvanced = elements.statsAdvanced;

        this._setupEventListeners();
    }

    /**
     * Set up event listeners.
     * @private
     */
    _setupEventListeners() {
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadTemplates());
        }

        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => this.searchTemplates());
        }

        if (this.categoryFilter) {
            this.categoryFilter.addEventListener('change', () => this.filterTemplates());
        }

        if (this.subcategoryFilter) {
            this.subcategoryFilter.addEventListener('change', () => this.filterTemplates());
        }

        if (this.difficultyFilter) {
            this.difficultyFilter.addEventListener('change', () => this.filterTemplates());
        }

        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => this.sortTemplates());
        }

        // Infinite scroll
        if (this.galleryContainer) {
            this.galleryContainer.addEventListener('scroll', () => this.handleScroll());
        }
    }

    /**
     * Show loading state.
     */
    showLoading() {
        if (this.loadingState) this.loadingState.classList.remove('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.galleryContainer) this.galleryContainer.classList.add('hidden');
    }

    /**
     * Show empty state.
     */
    showEmpty() {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.remove('hidden');
        if (this.errorState) this.errorState.classList.add('hidden');
        if (this.galleryContainer) this.galleryContainer.classList.add('hidden');
    }

    /**
     * Show error state.
     * @param {string} message - Error message to display
     */
    showError(message) {
        if (this.loadingState) this.loadingState.classList.add('hidden');
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.errorState) {
            this.errorState.classList.remove('hidden');
            const errorMessage = this.errorState.querySelector('.error-message');
            if (errorMessage && message) {
                errorMessage.textContent = message;
            }
        }
        if (this.galleryContainer) this.galleryContainer.classList.add('hidden');
    }

    /**
     * Show content state.
     */
    showContent() {
        console.log('showContent called');
        console.log('loadingState:', this.loadingState);
        console.log('galleryContainer:', this.galleryContainer);
        
        if (this.loadingState) {
            console.log('Adding hidden class to loadingState');
            this.loadingState.classList.add('hidden');
            // Also set inline style to ensure it's hidden
            this.loadingState.style.display = 'none';
            this.loadingState.style.visibility = 'hidden';
            this.loadingState.style.opacity = '0';
            console.log('loadingState classes after:', this.loadingState.className);
            // Check computed style
            const computedStyle = window.getComputedStyle(this.loadingState);
            console.log('loadingState display:', computedStyle.display);
            console.log('loadingState visibility:', computedStyle.visibility);
            console.log('loadingState opacity:', computedStyle.opacity);
        }
        if (this.emptyState) {
            this.emptyState.classList.add('hidden');
            this.emptyState.style.display = 'none';
        }
        if (this.errorState) {
            this.errorState.classList.add('hidden');
            this.errorState.style.display = 'none';
        }
        if (this.galleryContainer) {
            console.log('Removing hidden class from galleryContainer');
            this.galleryContainer.classList.remove('hidden');
            // Ensure it's visible
            this.galleryContainer.style.display = 'grid';
            this.galleryContainer.style.visibility = 'visible';
            this.galleryContainer.style.opacity = '1';
            console.log('galleryContainer classes after:', this.galleryContainer.className);
            // Check computed style
            const computedStyle = window.getComputedStyle(this.galleryContainer);
            console.log('galleryContainer display:', computedStyle.display);
            console.log('galleryContainer visibility:', computedStyle.visibility);
        }
    }

    /**
     * Load templates from API.
     * @param {boolean} reset - Whether to reset pagination
     */
    async loadTemplates(reset = true) {
        console.log('Loading templates...');
        
        if (reset) {
            this.currentPage = 1;
            this.hasMore = true;
            this.showLoading();
        }

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.pageSize
            });

            // Add filters if active
            if (this.categoryFilter && this.categoryFilter.value !== 'all') {
                params.append('category', this.categoryFilter.value);
            }
            if (this.subcategoryFilter && this.subcategoryFilter.value !== 'all') {
                params.append('subcategory', this.subcategoryFilter.value);
            }
            if (this.difficultyFilter && this.difficultyFilter.value !== 'all') {
                params.append('difficulty', this.difficultyFilter.value);
            }
            if (this.sortSelect && this.sortSelect.value !== 'default') {
                params.append('sort_by', this.sortSelect.value);
            }

            const url = `/api/templates?${params.toString()}`;
            console.log('Fetching templates from:', url);
            
            const response = await fetch(url, {
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('API response data:', data);
            
            if (response.ok && data.success) {
                const templates = data.data?.templates || [];
                const categories = data.data?.filters?.available_categories || [];
                const subcategories = data.data?.filters?.available_tags || [];
                
                console.log(`Loaded ${templates.length} templates`);
                
                if (reset) {
                    this.allTemplates = templates;
                    this.loadFilterOptions(categories, subcategories);
                } else {
                    this.allTemplates = [...this.allTemplates, ...templates];
                }
                
                this.filteredTemplates = [...this.allTemplates];
                this.hasMore = templates.length === this.pageSize;
                
                this.updateStats();
                this.renderTemplates();
                
                if (this.allTemplates.length === 0) {
                    console.log('No templates found, showing empty state');
                    this.showEmpty();
                } else {
                    console.log('Templates loaded, showing content');
                    this.showContent();
                }
            } else {
                console.error('API returned error:', data.error);
                throw new Error(data.error || 'Failed to load templates');
            }
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showError(`Failed to load templates: ${error.message}`);
        }
    }

    /**
     * Load filter options from API.
     */
    async loadFilterOptions(categories = null, subcategories = null) {
        try {
            if (!categories || !subcategories) {
                const response = await fetch('/api/templates/categories', {
                    credentials: 'include',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    categories = data.categories || [];
                    subcategories = data.subcategories || [];
                }
            }
            
            this.categories = categories;
            this.subcategories = subcategories;
            
            this.populateCategoryFilter();
            this.populateSubcategoryFilter();
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    /**
     * Populate category filter dropdown.
     */
    populateCategoryFilter() {
        if (!this.categoryFilter) return;
        
        // Clear existing options except "All"
        while (this.categoryFilter.options.length > 1) {
            this.categoryFilter.remove(1);
        }
        
        // Add category options
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = this.formatCategoryName(category);
            this.categoryFilter.appendChild(option);
        });
    }

    /**
     * Populate subcategory filter dropdown.
     */
    populateSubcategoryFilter() {
        if (!this.subcategoryFilter) return;
        
        // Clear existing options except "All"
        while (this.subcategoryFilter.options.length > 1) {
            this.subcategoryFilter.remove(1);
        }
        
        // Add subcategory options
        this.subcategories.forEach(subcategory => {
            const option = document.createElement('option');
            option.value = subcategory;
            option.textContent = this.formatSubcategoryName(subcategory);
            this.subcategoryFilter.appendChild(option);
        });
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
     * Format subcategory name for display.
     * @param {string} subcategory - Subcategory name
     * @returns {string} Formatted subcategory name
     */
    formatSubcategoryName(subcategory) {
        return subcategory
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Update statistics.
     */
    updateStats() {
        if (!this.allTemplates.length) {
            if (this.statsTotal) this.statsTotal.textContent = '0';
            if (this.statsPopular) this.statsPopular.textContent = '0';
            if (this.statsEasy) this.statsEasy.textContent = '0';
            if (this.statsAdvanced) this.statsAdvanced.textContent = '0';
            return;
        }
        
        const popularCount = this.allTemplates.filter(template => 
            template.popularity >= 80
        ).length;
        
        const easyCount = this.allTemplates.filter(template => 
            template.difficulty === 'beginner' || template.difficulty === 'easy'
        ).length;
        
        const advancedCount = this.allTemplates.filter(template => 
            template.difficulty === 'advanced' || template.difficulty === 'expert'
        ).length;
        
        if (this.statsTotal) this.statsTotal.textContent = this.allTemplates.length;
        if (this.statsPopular) this.statsPopular.textContent = popularCount;
        if (this.statsEasy) this.statsEasy.textContent = easyCount;
        if (this.statsAdvanced) this.statsAdvanced.textContent = advancedCount;
    }

    /**
     * Render template cards.
     */
    renderTemplates() {
        if (!this.galleryContainer) {
            console.error('galleryContainer is null');
            return;
        }
        
        if (this.currentPage === 1) {
            this.galleryContainer.innerHTML = '';
        }
        
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const templatesToRender = this.filteredTemplates.slice(startIndex, startIndex + this.pageSize);
        
        templatesToRender.forEach(template => {
            const card = this.createTemplateCard(template);
            this.galleryContainer.appendChild(card);
        });
        
        // Remove loading indicator if exists
        const loadingIndicator = this.galleryContainer.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Add loading indicator if there are more templates
        if (this.hasMore && this.filteredTemplates.length === this.allTemplates.length) {
            const indicator = document.createElement('div');
            indicator.className = 'loading-indicator text-center py-4 text-slate-500 dark:text-slate-400 col-span-full';
            indicator.innerHTML = '<span class="material-symbols-outlined animate-spin mr-2">sync</span> Loading more templates...';
            this.galleryContainer.appendChild(indicator);
        }
    }

    /**
     * Create a template card element using the unified card system.
     * @param {Object} template - Template object
     * @returns {HTMLElement} Template card element
     */
    createTemplateCard(template) {
        // Create a new TemplateCard instance
        const card = new TemplateCard({
            id: `template-card-${template.id}`,
            data: template,
            variant: 'default',
            clickable: true,
            hoverable: true
        });
        
        // Set up callbacks for template-specific actions
        card.setCallbacks({
            onAction: (action, data, event) => {
                this.handleTemplateCardAction(action, data, event);
            }
        });
        
        // Create and return the card element
        return card.createElement();
    }
    
    /**
     * Handle template card actions
     * @param {string} action - Action type
     * @param {Object} template - Template data
     * @param {Event} event - Event object
     */
    handleTemplateCardAction(action, template, event) {
        switch (action) {
            case 'preview':
                if (this.onTemplateSelect) {
                    this.onTemplateSelect(template);
                }
                break;
            case 'apply':
                if (this.onTemplateApply) {
                    this.onTemplateApply(template);
                }
                break;
            case 'apply-music-generator':
                if (this.onTemplateApplyWithMusicGenerator) {
                    this.onTemplateApplyWithMusicGenerator(template);
                }
                break;
            case 'apply-cover-generator':
                if (this.onTemplateApplyWithCoverGenerator) {
                    this.onTemplateApplyWithCoverGenerator(template);
                }
                break;
        }
    }

    /**
     * Get difficulty badge color.
     * @param {string} difficulty - Difficulty level
     * @returns {string} CSS class for difficulty badge
     */
    getDifficultyColor(difficulty) {
        const colors = {
            'beginner': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            'easy': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
            'intermediate': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            'advanced': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
            'expert': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        };
        
        return colors[difficulty] || colors.beginner;
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
     * Get popularity stars HTML.
     * @param {number} popularity - Popularity score (0-100)
     * @returns {string} Stars HTML
     */
    getPopularityStars(popularity) {
        const starCount = Math.round(popularity / 20); // 0-5 stars
        let stars = '';
        
        for (let i = 0; i < 5; i++) {
            if (i < starCount) {
                stars += '<span class="material-symbols-outlined text-sm">star</span>';
            } else {
                stars += '<span class="material-symbols-outlined text-sm text-slate-300 dark:text-slate-600">star</span>';
            }
        }
        
        return stars;
    }

    /**
     * Get template gradient based on category.
     * @param {string} category - Template category
     * @returns {string} CSS gradient classes
     */
    getTemplateGradient(category) {
        const gradients = {
            'pop': 'from-purple-500 to-pink-500',
            'rock': 'from-red-500 to-orange-500',
            'hip_hop': 'from-blue-500 to-cyan-500',
            'electronic': 'from-indigo-500 to-purple-500',
            'acoustic': 'from-green-500 to-emerald-500',
            'jazz': 'from-amber-500 to-yellow-500',
            'classical': 'from-slate-500 to-gray-500',
            'rnb': 'from-rose-500 to-pink-500',
            'metal': 'from-gray-700 to-black',
            'folk': 'from-brown-500 to-amber-500',
            'default': 'from-primary to-primary-dark'
        };
        
        return gradients[category] || gradients.default;
    }

    /**
     * Get template icon based on category.
     * @param {string} category - Template category
     * @returns {string} Material icon name
     */
    getTemplateIcon(category) {
        const icons = {
            'pop': 'music_note',
            'rock': 'rocket_launch',
            'hip_hop': 'mic',
            'electronic': 'bolt',
            'acoustic': 'piano',
            'jazz': 'saxophone',
            'classical': 'library_music',
            'rnb': 'favorite',
            'metal': 'volume_up',
            'folk': 'nature',
            'default': 'music_note'
        };
        
        return icons[category] || icons.default;
    }

    /**
     * Get template tags HTML.
     * @param {Array} tags - Template tags
     * @returns {string} Tags HTML
     */
    getTemplateTags(tags) {
        if (!tags || !tags.length) return '';
        
        const maxTags = 3;
        const tagsToShow = tags.slice(0, maxTags);
        
        return tagsToShow.map(tag => `
            <span class="inline-block px-2 py-1 rounded text-xs bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                ${tag}
            </span>
        `).join('');
    }

    /**
     * Setup event listeners for card buttons.
     * @param {HTMLElement} card - Template card element
     * @param {Object} template - Template object
     */
    setupCardEventListeners(card, template) {
        // Preview button
        const previewBtn = card.querySelector('.preview-btn');
        if (previewBtn && this.onTemplateSelect) {
            previewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.onTemplateSelect(template);
            });
        }
        
        // Apply button with context menu
        const applyBtn = card.querySelector('.apply-btn');
        const contextMenu = card.querySelector('.template-context-menu');
        const musicGeneratorBtn = contextMenu?.querySelector('.context-menu-item:nth-child(1)');
        const coverGeneratorBtn = contextMenu?.querySelector('.context-menu-item:nth-child(2)');
        console.log('Debug template card: applyBtn', applyBtn ? 'found' : 'null', 'contextMenu', contextMenu ? 'found' : 'null', 'musicGeneratorBtn', musicGeneratorBtn ? 'found' : 'null', 'coverGeneratorBtn', coverGeneratorBtn ? 'found' : 'null');
        
        if (applyBtn) {
            applyBtn.addEventListener('click', (e) => {
                console.log('Apply button clicked for template:', template.name);
                e.stopPropagation();
                this.toggleContextMenu(contextMenu, applyBtn);
            });
        }
        
        // Music Generator option
        if (musicGeneratorBtn && this.onTemplateApplyWithMusicGenerator) {
            musicGeneratorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.hideAllContextMenus();
                this.onTemplateApplyWithMusicGenerator(template);
            });
        }
        
        // Cover Generator option
        if (coverGeneratorBtn && this.onTemplateApplyWithCoverGenerator) {
            coverGeneratorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.hideAllContextMenus();
                this.onTemplateApplyWithCoverGenerator(template);
            });
        }
        
        // Whole card click
        if (this.onTemplateSelect) {
            card.addEventListener('click', () => {
                this.onTemplateSelect(template);
            });
        }
        
        // Close context menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!card.contains(e.target) && contextMenu && !contextMenu.classList.contains('hidden')) {
                contextMenu.classList.add('hidden');
            }
        });
    }
    
    /**
     * Toggle context menu visibility.
     * @param {HTMLElement} contextMenu - Context menu element
     * @param {HTMLElement} triggerBtn - Button that triggered the menu
     */
    toggleContextMenu(contextMenu, triggerBtn) {
        console.log('toggleContextMenu called', contextMenu, triggerBtn);
        if (!contextMenu) return;
        
        // Hide any other open context menus
        this.hideAllContextMenus();
        
        if (contextMenu.classList.contains('hidden')) {
            console.log('Showing context menu');
            contextMenu.classList.remove('hidden');
            this.activeContextMenu = contextMenu;
            
            // Position the menu
            this.positionContextMenu(contextMenu, triggerBtn);
        } else {
            console.log('Hiding context menu');
            contextMenu.classList.add('hidden');
            this.activeContextMenu = null;
        }
    }
    
    /**
     * Hide all context menus.
     */
    hideAllContextMenus() {
        document.querySelectorAll('.template-context-menu').forEach(menu => {
            menu.classList.add('hidden');
        });
        this.activeContextMenu = null;
    }
    
    /**
     * Position context menu relative to trigger button.
     * @param {HTMLElement} contextMenu - Context menu element
     * @param {HTMLElement} triggerBtn - Button that triggered the menu
     */
    positionContextMenu(contextMenu, triggerBtn) {
        const buttonRect = triggerBtn.getBoundingClientRect();
        const menuRect = contextMenu.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        // Default: position below button
        let top = buttonRect.bottom;
        let left = buttonRect.right - menuRect.width;
        
        // Check if menu would overflow bottom of viewport
        if (top + menuRect.height > viewportHeight - 10) {
            // Position above button instead
            top = buttonRect.top - menuRect.height - 5;
        }
        
        // Check if menu would overflow left of viewport
        if (left < 10) {
            left = 10;
        }
        
        contextMenu.style.position = 'fixed';
        contextMenu.style.top = `${top}px`;
        contextMenu.style.left = `${left}px`;
        contextMenu.style.zIndex = '1000';
    }

    /**
     * Filter templates based on active filters.
     */
    filterTemplates() {
        this.filteredTemplates = [...this.allTemplates];
        
        // Apply category filter
        if (this.categoryFilter && this.categoryFilter.value !== 'all') {
            this.filteredTemplates = this.filteredTemplates.filter(template =>
                template.category === this.categoryFilter.value
            );
        }
        
        // Apply subcategory filter
        if (this.subcategoryFilter && this.subcategoryFilter.value !== 'all') {
            this.filteredTemplates = this.filteredTemplates.filter(template =>
                template.subcategory === this.subcategoryFilter.value
            );
        }
        
        // Apply difficulty filter
        if (this.difficultyFilter && this.difficultyFilter.value !== 'all') {
            this.filteredTemplates = this.filteredTemplates.filter(template =>
                template.difficulty === this.difficultyFilter.value
            );
        }
        
        this.currentPage = 1;
        this.renderTemplates();
    }

    /**
     * Search templates.
     */
    searchTemplates() {
        if (!this.searchInput) return;
        
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        
        if (!searchTerm) {
            this.filteredTemplates = [...this.allTemplates];
        } else {
            this.filteredTemplates = this.allTemplates.filter(template => {
                const name = (template.name || '').toLowerCase();
                const description = (template.description || '').toLowerCase();
                const tags = (template.tags || []).map(tag => tag.toLowerCase());
                
                return name.includes(searchTerm) ||
                       description.includes(searchTerm) ||
                       tags.some(tag => tag.includes(searchTerm));
            });
        }
        
        this.currentPage = 1;
        this.renderTemplates();
    }

    /**
     * Sort templates.
     */
    sortTemplates() {
        if (!this.sortSelect) return;
        
        const sortValue = this.sortSelect.value;
        
        if (sortValue === 'default') {
            this.filteredTemplates = [...this.allTemplates];
        } else if (sortValue === 'popularity_desc') {
            this.filteredTemplates.sort((a, b) => b.popularity - a.popularity);
        } else if (sortValue === 'popularity_asc') {
            this.filteredTemplates.sort((a, b) => a.popularity - b.popularity);
        } else if (sortValue === 'difficulty_asc') {
            const difficultyOrder = { 'beginner': 0, 'easy': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4 };
            this.filteredTemplates.sort((a, b) =>
                (difficultyOrder[a.difficulty] || 5) - (difficultyOrder[b.difficulty] || 5)
            );
        } else if (sortValue === 'difficulty_desc') {
            const difficultyOrder = { 'beginner': 0, 'easy': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4 };
            this.filteredTemplates.sort((a, b) =>
                (difficultyOrder[b.difficulty] || 5) - (difficultyOrder[a.difficulty] || 5)
            );
        } else if (sortValue === 'name_asc') {
            this.filteredTemplates.sort((a, b) => a.name.localeCompare(b.name));
        } else if (sortValue === 'name_desc') {
            this.filteredTemplates.sort((a, b) => b.name.localeCompare(a.name));
        }
        
        this.currentPage = 1;
        this.renderTemplates();
    }

    /**
     * Handle scroll for infinite loading.
     */
    handleScroll() {
        if (!this.galleryContainer || !this.hasMore) return;
        
        const { scrollTop, scrollHeight, clientHeight } = this.galleryContainer;
        const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100;
        
        if (isNearBottom) {
            this.loadMoreTemplates();
        }
    }

    /**
     * Load more templates.
     */
    async loadMoreTemplates() {
        if (!this.hasMore) return;
        
        this.currentPage++;
        await this.loadTemplates(false);
    }

    /**
     * Set callback for template selection.
     * @param {Function} callback - Callback function with template parameter
     */
    setOnTemplateSelect(callback) {
        this.onTemplateSelect = callback;
    }

    /**
     * Set callback for template application.
     * @param {Function} callback - Callback function with template parameter
     */
    setOnTemplateApply(callback) {
        this.onTemplateApply = callback;
    }
    
    /**
     * Set callback for template application with Music Generator.
     * @param {Function} callback - Callback function with template parameter
     */
    setOnTemplateApplyWithMusicGenerator(callback) {
        this.onTemplateApplyWithMusicGenerator = callback;
    }
    
    /**
     * Set callback for template application with Cover Generator.
     * @param {Function} callback - Callback function with template parameter
     */
    setOnTemplateApplyWithCoverGenerator(callback) {
        this.onTemplateApplyWithCoverGenerator = callback;
    }

    /**
     * Get all templates.
     * @returns {Array} All templates
     */
    getAllTemplates() {
        return this.allTemplates;
    }

    /**
     * Get filtered templates.
     * @returns {Array} Filtered templates
     */
    getFilteredTemplates() {
        return this.filteredTemplates;
    }

    /**
     * Clear all templates.
     */
    clearTemplates() {
        this.allTemplates = [];
        this.filteredTemplates = [];
        this.currentPage = 1;
        this.hasMore = true;
        
        if (this.galleryContainer) {
            this.galleryContainer.innerHTML = '';
        }
        
        this.updateStats();
        this.showEmpty();
    }

    /**
     * Get template by ID.
     * @param {string} templateId - Template ID
     * @returns {Object|null} Template object or null
     */
    getTemplateById(templateId) {
        return this.allTemplates.find(template => template.id === templateId) || null;
    }

    /**
     * Apply template to form.
     * @param {Object} template - Template object
     * @returns {Object} Form data from template
     */
    getTemplateFormData(template) {
        return {
            title: template.form_data?.title || template.name,
            artist: template.form_data?.artist || 'Various Artists',
            genre: template.form_data?.genre || template.category,
            mood: template.form_data?.mood || template.tags?.[0] || 'energetic',
            duration: template.form_data?.duration || '3:00',
            tempo: template.form_data?.tempo || '120',
            key: template.form_data?.key || 'C',
            style: template.form_data?.style || template.subcategory,
            instruments: template.form_data?.instruments || template.tags?.join(', ') || ''
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateGallery;
} else {
    window.TemplateGallery = TemplateGallery;
}