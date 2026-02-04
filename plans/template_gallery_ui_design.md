# Template Gallery UI Design

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

## 3. Template Card Design

### Template Card HTML Structure
```html
<div class="template-card group relative rounded-xl overflow-hidden bg-white dark:bg-surface-dark border border-slate-200 dark:border-border-dark hover:border-primary/50 transition-all hover:shadow-lg hover:shadow-primary/5" data-template-id="template_001">
  <!-- Category badge -->
  <div class="absolute top-3 left-3 z-10">
    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-500 dark:bg-purple-500/20 dark:text-purple-400">
      <span class="material-symbols-outlined text-[14px]">graphic_eq</span>
      Electronic
    </span>
  </div>
  
  <!-- Popularity badge -->
  <div class="absolute top-3 right-3 z-10">
    <span class="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400">
      <span class="material-symbols-outlined text-[14px]">star</span>
      95
    </span>
  </div>
  
  <!-- Template image -->
  <div class="relative h-40 overflow-hidden bg-slate-100 dark:bg-slate-900">
    <img src="https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=300&fit=crop" 
         alt="Cyberpunk Synthwave template" 
         class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
         loading="lazy">
    <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
  </div>
  
  <!-- Template content -->
  <div class="p-4">
    <div class="flex items-start justify-between mb-2">
      <h4 class="font-bold text-slate-900 dark:text-white text-lg group-hover:text-primary transition-colors truncate pr-2">
        Cyberpunk Synthwave
      </h4>
      <button class="template-preview-btn text-slate-400 hover:text-white p-1 -mt-1 -mr-1">
        <span class="material-symbols-outlined text-[20px]">info</span>
      </button>
    </div>
    
    <p class="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-2">
      A cyberpunk synthwave track with pulsating bass, arpeggiated synthesizers, and nostalgic 80s atmosphere.
    </p>
    
    <!-- Tags -->
    <div class="flex flex-wrap gap-1.5 mb-4">
      <span class="inline-block px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
        synthwave
      </span>
      <span class="inline-block px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
        cyberpunk
      </span>
      <span class="inline-block px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
        80s
      </span>
    </div>
    
    <!-- Metadata -->
    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-4">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">speed</span>
          120 BPM
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">schedule</span>
          2:30
        </span>
      </div>
      <span class="flex items-center gap-1">
        <span class="material-symbols-outlined text-[14px]">bolt</span>
        Beginner
      </span>
    </div>
    
    <!-- Apply button -->
    <button class="apply-template-btn w-full py-2.5 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 group/btn">
      <span class="material-symbols-outlined text-[18px] group-hover/btn:rotate-12 transition-transform">auto_awesome</span>
      Use This Template
    </button>
  </div>
</div>
```

## 4. JavaScript Component Implementation

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
