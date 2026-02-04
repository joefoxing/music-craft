/**
 * Enhanced Dashboard Initialization
 * Initializes ActivityFeed and TemplateGallery components for the enhanced index page.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing enhanced dashboard components...');
    
    // Initialize Activity Feed
    initializeActivityFeed();
    
    // Initialize Template Gallery
    initializeTemplateGallery();
    
    console.log('Enhanced dashboard components initialized.');
});

/**
 * Initialize Activity Feed component.
 */
function initializeActivityFeed() {
    console.log('Initializing Activity Feed...');
    
    // Check if ActivityFeed class is available
    if (typeof ActivityFeed === 'undefined') {
        console.error('ActivityFeed class not found. Make sure activityFeed.js is loaded.');
        return;
    }
    
    // Get DOM elements
    const feedContainer = document.getElementById('activityFeedContainer');
    const loadingState = document.getElementById('activityLoading');
    const emptyState = document.getElementById('activityEmpty');
    const errorState = document.getElementById('activityError');
    const refreshBtn = document.getElementById('activityRefreshBtn');
    const filterSelect = document.getElementById('activityFilter');
    const searchInput = document.getElementById('activitySearch');
    const statsTotal = document.getElementById('statsTotal');
    const statsToday = document.getElementById('statsToday');
    const statsTemplates = document.getElementById('statsTemplates');
    const statsSuccess = document.getElementById('statsSuccess');
    const activityCount = document.getElementById('activityCount');
    
    if (!feedContainer) {
        console.error('Activity feed container not found.');
        return;
    }
    
    // Create ActivityFeed instance
    const activityFeed = new ActivityFeed();
    
    // Initialize with DOM elements
    activityFeed.initialize({
        feedContainer: feedContainer,
        loadingState: loadingState,
        emptyState: emptyState,
        errorState: errorState,
        refreshBtn: refreshBtn,
        filterSelect: filterSelect,
        searchInput: searchInput,
        statsTotal: statsTotal,
        statsToday: statsToday,
        statsTemplates: statsTemplates,
        statsSuccess: statsSuccess
    });
    
    // Set callbacks
    activityFeed.setOnActivityClick(function(activity) {
        console.log('Activity clicked:', activity);
        // Handle activity click - could show details modal, etc.
        alert(`Activity clicked: ${activity.description}`);
    });
    
    activityFeed.setOnTemplateApply(function(templateId) {
        console.log('Template apply clicked:', templateId);
        // Handle template apply - could navigate to cover generator with template pre-filled
        alert(`Applying template: ${templateId}`);
    });
    
    // Load activities
    activityFeed.loadActivities();
    
    // Store instance globally for debugging/access
    window.activityFeed = activityFeed;
    
    console.log('Activity Feed initialized.');
}

/**
 * Initialize Template Gallery component.
 */
function initializeTemplateGallery() {
    console.log('Initializing Template Gallery...');
    
    // Check if TemplateGallery class is available
    if (typeof TemplateGallery === 'undefined') {
        console.error('TemplateGallery class not found. Make sure templateGallery.js is loaded.');
        return;
    }
    
    // Get DOM elements (these IDs need to exist in the HTML)
    const galleryContainer = document.getElementById('templateGalleryContainer');
    const loadingState = document.getElementById('templateLoading');
    const emptyState = document.getElementById('templateEmpty');
    const errorState = document.getElementById('templateError');
    const refreshBtn = document.getElementById('templateRefreshBtn');
    const searchInput = document.getElementById('templateSearch');
    const categoryFilter = document.getElementById('templateCategoryFilter');
    const subcategoryFilter = document.getElementById('templateSubcategoryFilter'); // This element doesn't exist in HTML
    const difficultyFilter = document.getElementById('templateDifficultyFilter');
    const sortSelect = document.getElementById('templateSortSelect');
    const statsTotal = document.getElementById('templateStatsTotal');
    const statsPopular = document.getElementById('templateStatsPopular');
    const statsEasy = document.getElementById('templateStatsEasy');
    const statsAdvanced = document.getElementById('templateStatsAdvanced');
    
    if (!galleryContainer) {
        console.error('Template gallery container not found. Checking for alternative selectors...');
        
        // Try to find the gallery container by class or other means
        const possibleContainers = document.querySelectorAll('[id*="template"], [id*="gallery"]');
        console.log('Possible containers:', possibleContainers);
        
        // If still not found, we can't initialize
        if (!possibleContainers.length) {
            console.error('Template gallery container not found in DOM.');
            return;
        }
    }
    
    // Create TemplateGallery instance
    const templateGallery = new TemplateGallery();
    
    // Initialize with DOM elements (some may be null if not found)
    templateGallery.initialize({
        galleryContainer: galleryContainer,
        loadingState: loadingState,
        emptyState: emptyState,
        errorState: errorState,
        refreshBtn: refreshBtn,
        searchInput: searchInput,
        categoryFilter: categoryFilter,
        subcategoryFilter: subcategoryFilter,
        difficultyFilter: difficultyFilter,
        sortSelect: sortSelect,
        statsTotal: statsTotal,
        statsPopular: statsPopular,
        statsEasy: statsEasy,
        statsAdvanced: statsAdvanced
    });
    
    // Set callbacks
    templateGallery.setOnTemplateSelect(function(template) {
        console.log('Template selected:', template);
        // Handle template selection - could show preview modal
        showTemplatePreview(template);
    });
    
    templateGallery.setOnTemplateApply(function(template) {
        console.log('Template apply clicked:', template);
        // Handle template apply - could navigate to cover generator with template pre-filled
        applyTemplateToGenerator(template);
    });
    
    templateGallery.setOnTemplateApplyWithMusicGenerator(function(template) {
        console.log('Apply with Music Generator clicked:', template);
        // Handle template apply with Music Generator
        applyTemplateToMusicGenerator(template);
    });
    
    templateGallery.setOnTemplateApplyWithCoverGenerator(function(template) {
        console.log('Apply with Cover Generator clicked:', template);
        // Handle template apply with Cover Generator
        applyTemplateToGenerator(template);
    });
    
    // Load templates
    templateGallery.loadTemplates();
    
    // Store instance globally for debugging/access
    window.templateGallery = templateGallery;
    
    console.log('Template Gallery initialized.');
}

/**
 * Show template preview modal.
 * @param {Object} template - Template object
 */
function showTemplatePreview(template) {
    // Create or show a modal with template details
    console.log('Showing template preview:', template.name);
    
    // Simple alert for now - could be replaced with a proper modal
    alert(`Template Preview: ${template.name}\n\n${template.description}\n\nCategory: ${template.category}\nDifficulty: ${template.difficulty}\nPopularity: ${template.popularity}%`);
}

/**
 * Apply template to cover generator.
 * @param {Object} template - Template object
 */
function applyTemplateToGenerator(template) {
    console.log('Applying template to generator:', template.name);
    
    // Store template in sessionStorage for use on cover generator page
    try {
        sessionStorage.setItem('selectedTemplate', JSON.stringify(template));
        console.log('Template stored in sessionStorage.');
    } catch (e) {
        console.error('Failed to store template in sessionStorage:', e);
    }
    
    // Show confirmation dialog
    const confirmed = confirm(`Apply template "${template.name}" to Cover Generator?\n\nThis will navigate to the Cover Generator page with the template pre-filled.`);
    
    if (confirmed) {
        // Navigate to cover generator page
        console.log('Navigating to /cover-generator');
        window.location.href = '/cover-generator';
    } else {
        console.log('Template application cancelled by user.');
        // Optionally remove from sessionStorage if cancelled
        sessionStorage.removeItem('selectedTemplate');
    }
}

/**
 * Apply template to music generator.
 * @param {Object} template - Template object
 */
function applyTemplateToMusicGenerator(template) {
    console.log('Applying template to music generator:', template.name);
    
    // Store template in sessionStorage for use on music generator page
    try {
        sessionStorage.setItem('selectedMusicTemplate', JSON.stringify(template));
        console.log('Music template stored in sessionStorage.');
    } catch (e) {
        console.error('Failed to store template in sessionStorage:', e);
    }
    
    // Show confirmation dialog
    const confirmed = confirm(`Apply template "${template.name}" to Music Generator?\n\nThis will navigate to the Music Generator page with the template pre-filled.`);
    
    if (confirmed) {
        // Navigate to music generator page
        console.log('Navigating to /music-generator');
        window.location.href = '/music-generator';
    } else {
        console.log('Template application cancelled by user.');
        // Optionally remove from sessionStorage if cancelled
        sessionStorage.removeItem('selectedMusicTemplate');
    }
}

/**
 * Fallback initialization if DOM elements are missing.
 * This creates missing elements and sets up basic functionality.
 */
function initializeFallbackComponents() {
    console.log('Setting up fallback components...');
    
    // Check if we need to create missing elements for template gallery
    const templateSection = document.querySelector('section:has(h2:contains("Template Library"))');
    if (templateSection && !document.getElementById('templateGalleryContainer')) {
        console.log('Creating fallback template gallery container...');
        
        // Create a simple container
        const container = document.createElement('div');
        container.id = 'templateGalleryContainer';
        container.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
        
        // Find where to insert it (after the header section)
        const header = templateSection.querySelector('div.flex-col.gap-2');
        if (header) {
            header.parentNode.insertBefore(container, header.nextSibling);
        }
        
        // Create loading state
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'templateLoading';
        loadingDiv.className = 'text-center py-8';
        loadingDiv.innerHTML = '<div class="inline-flex items-center gap-2 text-slate-500 dark:text-slate-400"><span class="material-symbols-outlined animate-spin">sync</span><span>Loading templates...</span></div>';
        container.appendChild(loadingDiv);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeActivityFeed,
        initializeTemplateGallery,
        showTemplatePreview,
        applyTemplateToGenerator
    };
}