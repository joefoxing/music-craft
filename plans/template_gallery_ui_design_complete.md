# Template Gallery UI Design - Complete

## Overview
The Template Gallery UI provides an interactive interface for users to browse, search, and apply music generation templates. It integrates with the backend template API and provides a seamless user experience.

## 1. Component Architecture

### JavaScript Component: `TemplateGallery`
Location: `app/static/js/components/templateGallery.js`

**Responsibilities:**
- Fetch templates from `/api/templates` endpoint
- Render template cards in a responsive grid
- Handle filtering by category and search
- Manage template selection and application
- Show loading, empty, and error states
- Provide template preview functionality

**Key Methods:**
- `TemplateGallery.initialize()` - Initialize component with DOM elements
- `TemplateGallery.loadTemplates()` - Fetch and render templates
- `TemplateGallery.createTemplateCard()` - Create HTML for a single template card
- `TemplateGallery.filterTemplates()` - Filter templates based on user input
- `TemplateGallery.applyTemplate()` - Apply a template to the prompt form
- `TemplateGallery.showTemplatePreview()` - Show detailed template preview

## 2. HTML Structure

### Integration in `index.html`
Add the following after the "Quick Tags" section (around line 220):

```html
<!-- Template Library Section -->
<section class="flex flex-col gap-6 mt-8" id="templateLibrarySection">
  <!-- Header with title and controls -->
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
    <div class="flex flex-col gap-1">
      <h3 class="text-2xl font-bold dark:text-white text-slate-900">Template Library</h3>
      <p class="text-sm text-slate-500 dark:text-slate-400">
        Start with curated prompts for better results. Click any template to apply it.
      </p>
    </div>
    
    <!-- Controls -->
    <div class="flex flex-wrap items-center gap-3">
      <!-- Category filter -->
      <div class="relative">
        <select id="templateCategoryFilter" 
                class="appearance-none bg-surface-dark text-white text-sm rounded-lg pl-10 pr-8 py-2.5 border border-border-dark hover:border-primary/50 focus:border-primary focus:ring-1 focus:ring-primary transition-colors cursor-pointer min-w-[180px]">
          <option value="all">All Categories</option>
          <option value="electronic">🎛️ Electronic</option>
          <option value="ambient">🌊 Ambient</option>
          <option value="cinematic">🎬 Cinematic</option>
          <option value="hiphop">🎧 Hip Hop & Lo-fi</option>
          <option value="rock">🎸 Rock & Metal</option>
          <option value="world">🌍 World & Ethnic</option>
        </select>
        <span class="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">category</span>
        <span class="material-symbols-outlined absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">expand_more</span>
      </div>
      
      <!-- Search input -->
      <div class="relative">
        <input type="text" 
               id="templateSearch" 
               placeholder="Search templates..." 
               class="bg-surface-dark text-white text-sm rounded-lg pl-10 pr-4 py-2.5 border border-border-dark hover:border-primary/50 focus:border-primary focus:ring-1 focus:ring-primary transition-colors w-full md:w-64">
        <span class="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">search</span>
      </div>
      
      <!-- Sort dropdown -->
      <div class="relative">
        <select id="templateSort" 
                class="appearance-none bg-surface-dark text-white text-sm rounded-lg pl-10 pr-8 py-2.5 border border-border-dark hover:border-primary/50 focus:border-primary focus:ring-1 focus:ring-primary transition-colors cursor-pointer min-w-[140px]">
          <option value="popularity">Most Popular</option>
          <option value="recent">Recently Added</option>
          <option value="name">A to Z</option>
        </select>
        <span class="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">sort</span>
        <span class="material-symbols-outlined absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">expand_more</span>
      </div>
      
      <!-- Refresh button -->
      <button id="refreshTemplates" 
              class="p-2.5 rounded-lg bg-surface-dark border border-border-dark hover:bg-white/5 hover:border-primary/30 text-slate-400 hover:text-white transition-colors"
              title="Refresh templates">
        <span class="material-symbols-outlined text-[20px]">refresh</span>
      </button>
    </div>
  </div>
  
  <!-- Stats bar -->
  <div id="templateStats" class="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
    <span id="templateCount">Loading templates...</span>
    <span class="hidden md:inline">•</span>
    <div id="activeFilters" class="hidden md:flex items-center gap-2">
      <span>Filters:</span>
      <div class="flex flex-wrap gap-1.5">
        <!-- Active filter chips will be inserted here -->
      </div>
      <button id="clearFilters" class="text-primary hover:text-primary-dark text-xs font-medium">
        Clear all
      </button>
    </div>
  </div>
  
  <!-- Loading state -->
  <div id="templateLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Skeleton cards (3) -->
    <div class="template-card-skeleton rounded-xl bg-white dark:bg-surface-dark border border-slate-200 dark:border-border-dark p-4 animate-pulse">
      <div class="h-40 rounded-lg bg-slate-200 dark:bg-white/10 mb-4"></div>
      <div class="h-4 bg-slate-200 dark:bg-white/10 rounded mb-2 w-3/4"></div>
      <div class="h-3 bg-slate-200 dark:bg-white/5 rounded mb-3 w-1/2"></div>
      <div class="flex gap-2 mb-4">
        <div class="h-6 bg-slate-200 dark:bg-white/5 rounded-full w-16"></div>
        <div class="h-6 bg-slate-200 dark:bg-white/5 rounded-full w-12"></div>
      </div>
      <div class="h-10 bg-slate-200 dark:bg-white/10 rounded-lg"></div>
    </div>
    <!-- Repeat 2 more skeleton cards -->
  </div>
  
  <!-- Empty state -->
  <div id="templateEmpty" class="hidden text-center py-16">
    <div class="max-w-md mx-auto">
      <span class="material-symbols-outlined text-6xl text-slate-400 mb-4">description</span>
      <h4 class="text-xl font-bold text-slate-700 dark:text-slate-300 mb-2">No templates found</h4>
      <p class="text-slate-500 dark:text-slate-400 mb-6">
        Try adjusting your search or filter criteria. If you're looking for something specific, it might not exist yet.
      </p>
      <button id="resetTemplateFilters" 
              class="px-6 py-2.5 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors">
        Reset Filters
      </button>
    </div>
  </div>
  
  <!-- Error state -->
  <div id="templateError" class="hidden text-center py-16">
    <div class="max-w-md mx-auto">
      <span class="material-symbols-outlined text-6xl text-red-400 mb-4">error</span>
      <h4 class="text-xl font-bold text-slate-700 dark:text-slate-300 mb-2">Failed to load templates</h4>
      <p class="text-slate-500 dark:text-slate-400 mb-6" id="templateErrorMessage">
        There was an error loading the template library. Please try again.
      </p>
      <button id="retryTemplates" 
              class="px-6 py-2.5 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors">
        Retry Loading
      </button>
    </div>
  </div>
  
  <!-- Template cards container -->
  <div id="templateCards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Template cards will be dynamically inserted here -->
  </div>
  
  <!-- Load more button (for pagination) -->
  <div id="templatePagination" class="hidden text-center mt-8">
    <button id="loadMoreTemplates" 
            class="px-8 py-3 bg-surface-dark hover:bg-opacity-80 text-white text-sm font-medium rounded-lg border border-border-dark transition-colors flex items-center justify-center gap-2 mx-auto">
      <span class="material-symbols-outlined text-[18px]">add</span>
      Load More Templates
    </button>
    <p class="text-xs text-slate-500 dark:text-slate-400 mt-2" id="templatePaginationInfo">
      Showing <span id="shownCount">0</span> of <span id="totalCount">0</span> templates
    </p>
  </div>
</section>

<!-- Template Preview Modal -->
<div id="templatePreviewModal" class="hidden fixed inset-0 z-50 overflow-y-auto">
  <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
    <!-- Background overlay -->
    <div class="fixed inset-0 transition-opacity bg-black/70" aria-hidden="true"></div>
    
    <!-- Modal panel -->
    <div class="inline-block align-bottom bg-white dark:bg-background-dark rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
      <div class="px-6 py-4 bg-white dark:bg-background-dark">
        <!-- Modal content will be dynamically inserted here -->
      </div>
    </div>
  </div>
</div>
```

## 3. JavaScript Component Implementation

### File: `app/static/js/components/templateGallery.js`
```javascript
/**
 * Template Gallery component for the Music Cover Generator.
 * Handles loading, filtering, and displaying template cards.
 */
class TemplateGallery {
  constructor() {
    this.templates = [];
    this.filteredTemplates = [];
    this.categories = [];
    this.currentFilters = {
      category: 'all',
      search: '',
      sort: 'popularity'
    };
    this.currentPage = 1;
    this.templatesPerPage = 9;
    
    // DOM Elements (will be initialized)
    this.container = null;
    this.cardsContainer = null;
    this.loadingState = null;
    this.emptyState = null;
    this.errorState = null;
    this.categoryFilter = null;
    this.searchInput = null;
    this.sortSelect = null;
    this.refreshBtn = null;
    this.templateCount = null;
    this.loadMoreBtn = null;
    this.paginationContainer = null;
  }
  
  /**
   * Initialize the template gallery.
   * @param {Object} elements - DOM element references
   */
  initialize(elements) {
    this.container = elements.container;
    this.cardsContainer = elements.cardsContainer;
    this.loadingState = elements.loadingState;
    this.emptyState = elements.emptyState;
    this.errorState = elements.errorState;
    this.categoryFilter = elements.categoryFilter;
    this.searchInput = elements.searchInput;
    this.sortSelect = elements.sortSelect;
    this.refreshBtn = elements.refreshBtn;
    this.templateCount = elements.templateCount;
    this.loadMoreBtn = elements.loadMoreBtn;
    this.paginationContainer = elements.paginationContainer;
    
    this._setupEventListeners();
    this.loadTemplates();
  }
  
  /**
   * Set up event listeners.
   * @private
   */
  _setupEventListeners() {
    // Category filter
    if (this.categoryFilter) {
      this.categoryFilter.addEventListener('change', (e) => {
        this.currentFilters.category = e.target.value;
        this.filterTemplates();
      });
    }
    
    // Search input with debounce
    if (this.searchInput) {
      let searchTimeout;
      this.searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.currentFilters.search = e.target.value.trim();
          this.filterTemplates();
        }, 300);
      });
    }
    
    // Sort select
    if (this.sortSelect) {
      this.sortSelect.addEventListener('change', (e) => {
        this.currentFilters.sort = e.target.value;
        this.filterTemplates();
      });
    }
    
    // Refresh button
    if (this.refreshBtn) {
      this.refreshBtn.addEventListener('click', () => {
        this.loadTemplates();
      });
    }
    
    // Load more button
    if (this.loadMoreBtn) {
      this.loadMoreBtn.addEventListener('click', () => {
        this.loadMoreTemplates();
      });
    }
    
    // Retry button (in error state)
    const retryBtn = document.getElementById('retryTemplates');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadTemplates();
      });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('resetTemplateFilters');
    if (resetFiltersBtn) {
      resetFiltersBtn.addEventListener('click', () => {
        this.resetFilters();
      });
    }
  }
  
  /**
   * Load templates from API.
   */
  async loadTemplates() {
    this.showLoading();
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (this.currentFilters.category !== 'all') {
        params.append('category', this.currentFilters.category);
      }
      if (this.currentFilters.search) {
        params.append('search', this.currentFilters.search);
      }
      params.append('sort_by', this.currentFilters.sort);
      
      const response = await fetch(`/api/templates?${params.toString()}`);
      const data = await response.json();
      
      if (data.success) {
        this.templates = data.templates;
        this.categories = data.categories;
        this.filteredTemplates = [...this.templates];
        
        this.updateStats();
        this.renderTemplates();
        
        if (this.templates.length === 0) {
          this.showEmpty();
        } else {
          this.showContent();
        }
      } else {
        throw new Error(data.error || 'Failed to load templates');
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      this.showError(`Failed to load templates: ${error.message}`);
    }
  }
  
  /**
   * Filter templates based on current filters.
   */
  filterTemplates() {
    let filtered = [...this.templates];
    
    // Apply category filter
    if (this.currentFilters.category !== 'all') {
      filtered = filtered.filter(template => 
        template.category === this.currentFilters.category
      );
    }
    
    // Apply search filter
    if (this.currentFilters.search) {
      const searchTerm = this.currentFilters.search.toLowerCase();
      filtered = filtered.filter(template => {
        const name = template.name.toLowerCase();
        const description = template.description.toLowerCase();
        const tags = template.tags.join(' ').toLowerCase();
        const style = template.style?.toLowerCase() || '';
        
        return name.includes(searchTerm) ||
               description.includes(searchTerm) ||
               tags.includes(searchTerm) ||
               style.includes(searchTerm);
      });
    }
    
    // Apply sorting
    switch (this.currentFilters.sort) {
      case 'popularity':
        filtered.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
        break;
      case 'recent':
        filtered.sort((a, b) => {
          const dateA = new Date(a.updated_at || a.created_at || '2000-01-01');
          const dateB = new Date(b.updated_at || b.created_at || '2000-01-01');
          return dateB - dateA;
        });
        break;
      case 'name':
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }
    
    this.filteredTemplates = filtered;
    this.currentPage = 1;
    this.renderTemplates();
    this.updateStats();
  }
  
  /**
   * Reset all filters to default.
   */
  resetFilters() {
    this.currentFilters = {
      category: 'all',
      search: '',
      sort: 'popularity'
    };
    
    if (this.categoryFilter) this.categoryFilter.value = 'all';
    if (this.searchInput) this.searchInput.value = '';
    if (this.sortSelect) this.sortSelect.value = 'popularity';
    
    this.filterTemplates();
  }
  
  /**
   * Load more templates (pagination).
   */
  loadMoreTemplates() {
    this.currentPage++;
    this.renderTemplates();
  }
  
  /**
   * Render templates to the DOM.
   */
  renderTemplates() {
    if (!this.cardsContainer) return;
    
    // Clear container if it's the first page
    if (this.currentPage === 1) {
      this.cardsContainer.innerHTML = '';
    }
    
    // Calculate which templates to show
    const startIndex = 0; // For now, show all (implement pagination later)
    const endIndex = this.filteredTemplates.length;
    const templatesToShow = this.filteredT