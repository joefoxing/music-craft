/**
 * Sidebar Component - Your Playlists Module
 * 
 * Features:
 * - Fetches 3 most recently created playlists from /api/playlists
 * - Loading states with skeleton placeholders
 * - Empty state with "Create your first playlist" CTA
 * - Error state with retry functionality
 * - Caching with localStorage fallback
 * - Responsive: collapses to icon-only below 768px
 * - Accessibility: ARIA labels, focus management, keyboard navigation
 */

(function() {
    'use strict';

    if (window.__sidebarPlaylistsInitialized) {
        return;
    }
    window.__sidebarPlaylistsInitialized = true;

    // ============================================
    // Configuration
    // ============================================
    const CONFIG = {
        API_ENDPOINT: '/api/playlists?limit=3&sort=created_at:desc',
        CACHE_KEY: 'sidebar_playlists_cache',
        CACHE_TTL: 5 * 60 * 1000, // 5 minutes
        MOBILE_BREAKPOINT: 768,
        THUMBNAIL_SIZE: 60,
        MAX_TITLE_LINES: 2,
        RETRY_DELAY: 2000,
        MAX_RETRIES: 3
    };

    // ============================================
    // State Management
    // ============================================
    const state = {
        playlists: [],
        cachedData: null,
        isLoading: false,
        hasError: false,
        errorMessage: '',
        retryCount: 0,
        isCompact: false,
        abortController: null,
        hasRendered: false,
        isFetching: false,
        lastLoadAt: 0
    };

    // ============================================
    // DOM Element References
    // ============================================
    let elements = {};

    function initializeElements() {
        elements = {
            container: document.getElementById('your-playlists-container'),
            loading: document.getElementById('playlists-loading'),
            empty: document.getElementById('playlists-empty'),
            error: document.getElementById('playlists-error'),
            list: document.getElementById('playlists-list'),
            listCompact: document.getElementById('playlists-list-compact'),
            retryBtn: document.getElementById('playlists-retry-btn'),
            viewAllLink: document.querySelector('.sidebar-playlists-view-all')
        };
    }

    // ============================================
    // Utility Functions
    // ============================================

    /**
     * Format a date as relative time (e.g., "2 hours ago")
     * @param {string|Date} dateString - ISO date string or Date object
     * @returns {string} Relative time string
     */
    function formatRelativeTime(dateString) {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        // Time intervals in seconds
        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };

        if (seconds < 60) return 'Just now';
        
        for (const [unit, secondsInUnit] of Object.entries(intervals)) {
            const count = Math.floor(seconds / secondsInUnit);
            if (count >= 1) {
                return count === 1 
                    ? `1 ${unit} ago` 
                    : `${count} ${unit}s ago`;
            }
        }
        
        return date.toLocaleDateString();
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Truncate text to fit within max lines
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    function truncateText(text, maxLength = 50) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }

    /**
     * Compare playlists for changes to avoid unnecessary re-rendering.
     * @param {Array} current - Current playlists
     * @param {Array} next - Next playlists
     * @returns {boolean} True if arrays are equivalent
     */
    function arePlaylistsEqual(current, next) {
        if (current === next) return true;
        if (!Array.isArray(current) || !Array.isArray(next)) return false;
        if (current.length !== next.length) return false;

        for (let i = 0; i < current.length; i += 1) {
            const a = current[i] || {};
            const b = next[i] || {};
            if (
                a.id !== b.id ||
                a.name !== b.name ||
                a.created_at !== b.created_at ||
                a.updated_at !== b.updated_at ||
                a.audio_count !== b.audio_count ||
                a.cover_image_url !== b.cover_image_url
            ) {
                return false;
            }
        }

        return true;
    }

    /**
     * Get cached playlists from localStorage
     * @returns {Object|null} Cached data or null
     */
    function getCachedPlaylists() {
        try {
            const cached = localStorage.getItem(CONFIG.CACHE_KEY);
            if (!cached) return null;
            
            const data = JSON.parse(cached);
            const now = Date.now();
            
            // Check if cache is still valid
            if (data.timestamp && (now - data.timestamp) < CONFIG.CACHE_TTL) {
                return data;
            }
            
            // Cache expired, remove it
            localStorage.removeItem(CONFIG.CACHE_KEY);
            return null;
        } catch (e) {
            console.warn('[Sidebar] Error reading cache:', e);
            return null;
        }
    }

    /**
     * Save playlists to localStorage cache
     * @param {Array} playlists - Playlists to cache
     */
    function setCachedPlaylists(playlists) {
        try {
            const data = {
                playlists: playlists,
                timestamp: Date.now()
            };
            localStorage.setItem(CONFIG.CACHE_KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('[Sidebar] Error writing cache:', e);
        }
    }

    /**
     * Clear the playlists cache
     */
    function clearCache() {
        try {
            localStorage.removeItem(CONFIG.CACHE_KEY);
        } catch (e) {
            console.warn('[Sidebar] Error clearing cache:', e);
        }
    }

    // ============================================
    // API Functions
    // ============================================

    /**
     * Fetch playlists from the API
     * @returns {Promise<Array>} Array of playlists
     */
    async function fetchPlaylists() {
        // Cancel any pending request
        if (state.abortController) {
            state.abortController.abort();
        }
        
        state.abortController = new AbortController();
        
        try {
            const response = await fetch(CONFIG.API_ENDPOINT, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                signal: state.abortController.signal,
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Please log in to view your playlists');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to load playlists');
            }

            return data.data?.playlists || [];
        } catch (error) {
            if (error.name === 'AbortError') {
                throw error;
            }
            console.error('[Sidebar] Fetch error:', error);
            throw error;
        }
    }

    // ============================================
    // Rendering Functions
    // ============================================

    /**
     * Create a playlist list item HTML
     * @param {Object} playlist - Playlist data
     * @param {boolean} isCompact - Whether to render in compact mode
     * @returns {HTMLElement} Playlist item element
     */
    function createPlaylistItem(playlist, isCompact = false) {
        const li = document.createElement('li');
        const relativeTime = formatRelativeTime(playlist.created_at);
        const trackCount = playlist.audio_count || 0;
        const coverUrl = playlist.cover_image_url || '/static/images/default-playlist.svg';
        
        // Create accessible label
        const ariaLabel = `${escapeHtml(playlist.name)}, ${trackCount} track${trackCount !== 1 ? 's' : ''}, created ${relativeTime}`;
        
        li.className = 'group';
        
        if (isCompact) {
            // Compact view (icon only for mobile)
            li.innerHTML = `
                <a href="/playlist/${escapeHtml(playlist.id)}" 
                   class="flex items-center justify-center p-3 rounded-xl transition-all duration-300 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-indigo-600 dark:hover:text-indigo-300"
                   aria-label="${ariaLabel}"
                   data-playlist-id="${escapeHtml(playlist.id)}">
                    <img src="${escapeHtml(coverUrl)}" 
                         alt="" 
                         class="w-10 h-10 rounded-lg object-cover shadow-sm"
                         width="40" 
                         height="40"
                         loading="lazy"
                         onerror="this.onerror=null;this.src='/static/images/default-playlist.svg'">
                </a>
            `;
        } else {
            // Full view with details
            li.innerHTML = `
                <a href="/playlist/${escapeHtml(playlist.id)}" 
                   class="flex items-center gap-3.5 px-3 py-2.5 rounded-xl transition-all duration-300 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-indigo-600 dark:hover:text-indigo-300 group/playlist"
                   aria-label="${ariaLabel}"
                   data-playlist-id="${escapeHtml(playlist.id)}">
                    <div class="relative flex-shrink-0">
                        <img src="${escapeHtml(coverUrl)}" 
                             alt="" 
                             class="w-[60px] h-[60px] rounded-lg object-cover shadow-sm group-hover/playlist:shadow-md transition-shadow"
                             width="60" 
                             height="60"
                             loading="lazy"
                             onerror="this.onerror=null;this.src='/static/images/default-playlist.svg'">
                        <div class="absolute inset-0 bg-black/0 group-hover/playlist:bg-black/20 transition-colors rounded-lg flex items-center justify-center">
                            <span class="material-symbols-outlined text-white text-2xl opacity-0 group-hover/playlist:opacity-100 transition-opacity drop-shadow-lg">play_arrow</span>
                        </div>
                    </div>
                    <div class="flex-1 min-w-0 overflow-hidden">
                        <p class="font-medium text-sm line-clamp-2 leading-snug group-hover/playlist:text-indigo-600 dark:group-hover/playlist:text-indigo-300 transition-colors">
                            ${escapeHtml(truncateText(playlist.name, 60))}
                        </p>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-xs text-slate-500 dark:text-slate-400">
                                ${trackCount} track${trackCount !== 1 ? 's' : ''}
                            </span>
                            <span class="text-xs text-slate-400 dark:text-slate-500">${relativeTime}</span>
                        </div>
                    </div>
                </a>
            `;
        }
        
        // Add click handler for client-side navigation
        const link = li.querySelector('a');
        link.addEventListener('click', handlePlaylistClick);
        
        return li;
    }

    /**
     * Handle playlist item click for client-side routing
     * @param {Event} event - Click event
     */
    function handlePlaylistClick(event) {
        const link = event.currentTarget;
        const href = link.getAttribute('href');
        
        // Allow default behavior for middle-click, ctrl+click, etc.
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
            return;
        }
        
        // Check if we should use client-side routing
        if (window.router && typeof window.router.navigate === 'function') {
            event.preventDefault();
            const playlistId = link.getAttribute('data-playlist-id');
            
            // Store focus for restoration
            const focusedElement = document.activeElement;
            sessionStorage.setItem('sidebar_last_focus', focusedElement.id || '');
            
            window.router.navigate(href);
        }
    }

    /**
     * Update the UI based on current state
     */
    function updateUI() {
        if (!elements.container) return;

        // Hide all states first
        elements.loading.classList.add('hidden');
        elements.empty.classList.add('hidden');
        elements.error.classList.add('hidden');
        elements.list.classList.add('hidden');
        elements.listCompact.classList.add('hidden');
        
        if (state.isLoading) {
            elements.loading.classList.remove('hidden');
            if (elements.viewAllLink) {
                elements.viewAllLink.classList.remove('opacity-100');
                elements.viewAllLink.classList.add('opacity-0');
            }
        } else if (state.hasError) {
            elements.error.classList.remove('hidden');
            // Focus the retry button for accessibility
            setTimeout(() => {
                elements.retryBtn?.focus();
            }, 100);
        } else if (state.playlists.length === 0) {
            elements.empty.classList.remove('hidden');
            if (elements.viewAllLink) {
                elements.viewAllLink.classList.remove('opacity-100');
                elements.viewAllLink.classList.add('opacity-0');
            }
        } else {
            // Show appropriate list view based on compact mode
            if (state.isCompact) {
                elements.listCompact.classList.remove('hidden');
                elements.listCompact.classList.add('flex');
            } else {
                elements.list.classList.remove('hidden');
                elements.list.classList.add('flex');
            }
            
            if (elements.viewAllLink) {
                elements.viewAllLink.classList.remove('opacity-0');
                elements.viewAllLink.classList.add('opacity-100');
            }
        }
    }

    /**
     * Render the playlists list
     */
    function renderPlaylists() {
        if (!elements.list || !elements.listCompact) return;
        
        // Clear existing content
        elements.list.innerHTML = '';
        elements.listCompact.innerHTML = '';
        
        // Render each playlist
        state.playlists.forEach(playlist => {
            elements.list.appendChild(createPlaylistItem(playlist, false));
            elements.listCompact.appendChild(createPlaylistItem(playlist, true));
        });

        state.hasRendered = true;
        
        // Update ARIA count
        const count = state.playlists.length;
        const label = `List of ${count} recent playlist${count !== 1 ? 's' : ''}`;
        elements.list.setAttribute('aria-label', label);
        elements.listCompact.setAttribute('aria-label', label);
    }

    // ============================================
    // Main Functions
    // ============================================

    /**
     * Load playlists from API or cache
     */
    async function loadPlaylists() {
        // Check if user is authenticated (container exists)
        if (!elements.container) {
            return;
        }

        const now = Date.now();
        if (state.isFetching || (now - state.lastLoadAt) < 10000) {
            return;
        }
        state.isFetching = true;
        state.lastLoadAt = now;

        state.hasError = false;

        try {
            // Try to get cached data first for immediate display
            const cached = getCachedPlaylists();
            if (cached && cached.playlists) {
                state.playlists = cached.playlists;
                state.cachedData = cached.playlists;
                renderPlaylists();
                // Don't show loading if we have cached data
                if (state.playlists.length > 0) {
                    state.isLoading = false;
                    updateUI();
                }
            }

            if (state.playlists.length === 0) {
                state.isLoading = true;
                updateUI();
            }

            // Fetch fresh data
            const playlists = await fetchPlaylists();
            
            if (!arePlaylistsEqual(state.playlists, playlists)) {
                state.playlists = playlists;
                renderPlaylists();
            }
            state.retryCount = 0;
            
            // Cache the new data
            setCachedPlaylists(playlists);
            
            if (!state.hasRendered && state.playlists.length > 0) {
                renderPlaylists();
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                return; // Request was cancelled, don't update state
            }
            
            state.hasError = true;
            state.errorMessage = error.message;
            
            // If we have cached data, keep showing it but log the error
            if (state.cachedData && state.cachedData.length > 0) {
                console.warn('[Sidebar] Using cached data due to fetch error:', error.message);
                state.hasError = false;
                state.playlists = state.cachedData;
            } else {
                state.playlists = [];
            }
            
            // Increment retry count for exponential backoff
            state.retryCount++;
        } finally {
            state.isLoading = false;
            state.isFetching = false;
            updateUI();
        }
    }

    /**
     * Retry loading playlists
     */
    async function retryLoad() {
        // Exponential backoff
        const delay = Math.min(CONFIG.RETRY_DELAY * Math.pow(2, state.retryCount - 1), 10000);
        
        if (state.retryCount >= CONFIG.MAX_RETRIES) {
            state.retryCount = 0; // Reset for next time
        }
        
        if (delay > 0) {
            await new Promise(resolve => setTimeout(resolve, delay));
        }
        
        await loadPlaylists();
    }

    /**
     * Check viewport and update compact mode
     */
    function checkViewport() {
        const wasCompact = state.isCompact;
        state.isCompact = window.innerWidth < CONFIG.MOBILE_BREAKPOINT;
        
        if (wasCompact !== state.isCompact) {
            updateUI();
        }
    }

    /**
     * Handle visibility change (tab becomes active)
     */
    function handleVisibilityChange() {
        if (!document.hidden) {
            // Refresh data when tab becomes visible (if cache might be stale)
            const cached = getCachedPlaylists();
            if (!cached) {
                loadPlaylists();
            }
        }
    }

    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} event - Keyboard event
     */
    function handleKeyNavigation(event) {
        // Only handle if we're in the playlists section
        if (!elements.container?.contains(document.activeElement)) return;
        
        const items = state.isCompact 
            ? elements.listCompact?.querySelectorAll('a') 
            : elements.list?.querySelectorAll('a');
        
        if (!items || items.length === 0) return;
        
        const currentIndex = Array.from(items).indexOf(document.activeElement);
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                items[nextIndex].focus();
                break;
            case 'ArrowUp':
                event.preventDefault();
                const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                items[prevIndex].focus();
                break;
            case 'Home':
                event.preventDefault();
                items[0].focus();
                break;
            case 'End':
                event.preventDefault();
                items[items.length - 1].focus();
                break;
        }
    }

    /**
     * Refresh playlists (public API)
     */
    function refresh() {
        clearCache();
        state.retryCount = 0;
        loadPlaylists();
    }

    /**
     * Get current playlists (public API)
     * @returns {Array} Current playlists
     */
    function getPlaylists() {
        return [...state.playlists];
    }

    // ============================================
    // Initialization
    // ============================================

    function init() {
        initializeElements();
        
        if (!elements.container) {
            console.log('[Sidebar] Playlists container not found, skipping initialization');
            return;
        }

        // Check initial viewport
        checkViewport();

        // Set up event listeners
        elements.retryBtn?.addEventListener('click', retryLoad);
        window.addEventListener('resize', debounce(checkViewport, 150));
        document.addEventListener('visibilitychange', handleVisibilityChange);
        elements.container.addEventListener('keydown', handleKeyNavigation);

        // Load initial data
        loadPlaylists();

        console.log('[Sidebar] Your Playlists component initialized');
    }

    /**
     * Debounce utility function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ============================================
    // Expose Public API
    // ============================================
    window.SidebarPlaylists = {
        refresh,
        getPlaylists,
        clearCache,
        loadPlaylists
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

// ============================================
// Mobile Menu Toggle (existing functionality)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
});

// Mobile menu
function toggleMobileMenu() {
    const sidebar = document.getElementById('main-sidebar') || document.querySelector('aside');
    if (!sidebar) return;
    
    const isHidden = sidebar.classList.contains('hidden');
    
    if (isHidden) {
        // Open sidebar
        sidebar.classList.remove('hidden');
        // Ensure flex is added for layout
        sidebar.classList.add('flex'); 
        
        // Add mobile styling
        sidebar.classList.add('fixed', 'inset-y-0', 'left-0', 'z-50', 'h-full', 'shadow-2xl');
        
        // Create backdrop
        let backdrop = document.getElementById('sidebar-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'sidebar-backdrop';
            backdrop.className = 'fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm transition-opacity opacity-0';
            backdrop.onclick = toggleMobileMenu;
            document.body.appendChild(backdrop);
            // Animate in
            requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
        }
    } else {
        // Close sidebar
        sidebar.classList.add('hidden');
        sidebar.classList.remove('flex');
        
        // Remove mobile styling
        sidebar.classList.remove('fixed', 'inset-y-0', 'left-0', 'z-50', 'h-full', 'shadow-2xl');
        
        // Remove backdrop
        const backdrop = document.getElementById('sidebar-backdrop');
        if (backdrop) {
            backdrop.classList.add('opacity-0');
            setTimeout(() => {
                if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
            }, 300);
        }
    }
}

// ============================================
// Dashboard Dropdown Menu
// ============================================

(function() {
    'use strict';

    if (window.__dashboardDropdownInitialized) {
        return;
    }
    window.__dashboardDropdownInitialized = true;

    let isDropdownOpen = false;
    let currentDropdown = null;

    function initDashboardDropdown() {
        const mainBtn = document.getElementById('dashboard-main-btn');
        const menuBtn = document.getElementById('dashboard-menu-btn');
        const dropdown = document.getElementById('dashboard-dropdown');

        if (!dropdown) return;

        // Function to handle button clicks
        const handleButtonClick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleDropdown(dropdown);
        };

        // Add click listeners to both buttons
        if (mainBtn) {
            mainBtn.addEventListener('click', handleButtonClick);
        }
        if (menuBtn) {
            menuBtn.addEventListener('click', handleButtonClick);
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && (!mainBtn || !mainBtn.contains(e.target)) && (!menuBtn || !menuBtn.contains(e.target))) {
                closeDropdown(dropdown);
            }
        });

        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isDropdownOpen) {
                closeDropdown(dropdown);
            }
        });
    }

    function initCreateDropdown() {
        const mainBtn = document.getElementById('create-main-btn');
        const menuBtn = document.getElementById('create-menu-btn');
        const dropdown = document.getElementById('create-dropdown');

        if (!dropdown) return;

        // Function to handle button clicks
        const handleButtonClick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleDropdown(dropdown);
        };

        // Add click listeners to both buttons
        if (mainBtn) {
            mainBtn.addEventListener('click', handleButtonClick);
        }
        if (menuBtn) {
            menuBtn.addEventListener('click', handleButtonClick);
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && (!mainBtn || !mainBtn.contains(e.target)) && (!menuBtn || !menuBtn.contains(e.target))) {
                closeDropdown(dropdown);
            }
        });

        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isDropdownOpen) {
                closeDropdown(dropdown);
            }
        });
    }

    function toggleDropdown(dropdown) {
        if (isDropdownOpen && currentDropdown === dropdown) {
            closeDropdown(dropdown);
        } else {
            openDropdown(dropdown);
        }
    }

    function openDropdown(dropdown) {
        // Close any other open dropdown
        if (currentDropdown && currentDropdown !== dropdown) {
            closeDropdown(currentDropdown);
        }

        dropdown.classList.remove('hidden');
        isDropdownOpen = true;
        currentDropdown = dropdown;
    }

    function closeDropdown(dropdown) {
        dropdown.classList.add('hidden');
        isDropdownOpen = false;
        if (currentDropdown === dropdown) {
            currentDropdown = null;
        }
    }

    function initAddRemoveDropdown() {
        const mainBtn = document.getElementById('addremove-main-btn');
        const menuBtn = document.getElementById('addremove-menu-btn');
        const dropdown = document.getElementById('addremove-dropdown');

        if (!dropdown) return;

        // Function to handle button clicks
        const handleButtonClick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleDropdown(dropdown);
        };

        // Add click listeners to both buttons
        if (mainBtn) {
            mainBtn.addEventListener('click', handleButtonClick);
        }
        if (menuBtn) {
            menuBtn.addEventListener('click', handleButtonClick);
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && (!mainBtn || !mainBtn.contains(e.target)) && (!menuBtn || !menuBtn.contains(e.target))) {
                closeDropdown(dropdown);
            }
        });

        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isDropdownOpen) {
                closeDropdown(dropdown);
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initDashboardDropdown();
            initCreateDropdown();
            initAddRemoveDropdown();
        });
    } else {
        initDashboardDropdown();
        initCreateDropdown();
        initAddRemoveDropdown();
    }

})();

// ============================================
// Create Dropdown Menu
// ============================================

(function() {
    'use strict';

    if (window.__createDropdownInitialized) {
        return;
    }
    window.__createDropdownInitialized = true;

    // Note: The functions are defined in the dashboard dropdown module above
    // and called from the initialization section

})();

// ============================================
// Add/Remove Dropdown Menu
// ============================================

(function() {
    'use strict';

    if (window.__addRemoveDropdownInitialized) {
        return;
    }
    window.__addRemoveDropdownInitialized = true;

    // Note: The functions are defined in the dashboard dropdown module above
    // and called from the initialization section

})();
// ============================================
// Sidebar Collapse Toggle
// ============================================

(function() {
    'use strict';

    const STORAGE_KEY = 'sidebar_collapsed';
    const sidebar = document.getElementById('main-sidebar');
    const btn = document.getElementById('sidebar-collapse-btn');
    const icon = document.getElementById('sidebar-collapse-icon');

    if (!sidebar || !btn) return;

    const collapseLabels = sidebar.querySelectorAll(
        'h1, p.text-xs.text-slate-500, .text-sm.font-semibold, ' +
        '.text-sm.font-medium, .sidebar-playlists-title, ' +
        '#your-playlists-container h3, #your-playlists-container a.sidebar-playlists-view-all, ' +
        'button span:not(.material-symbols-outlined), a span:not(.material-symbols-outlined)'
    );

    function applyCollapsed(collapsed, animate) {
        if (collapsed) {
            sidebar.classList.add('sidebar-collapsed');
            if (icon) icon.textContent = 'chevron_right';
            btn.title = 'Expand sidebar';
        } else {
            sidebar.classList.remove('sidebar-collapsed');
            if (icon) icon.textContent = 'chevron_left';
            btn.title = 'Collapse sidebar';
        }
    }

    // Restore saved state
    const saved = localStorage.getItem(STORAGE_KEY) === 'true';
    applyCollapsed(saved);

    btn.addEventListener('click', function() {
        const isNowCollapsed = !sidebar.classList.contains('sidebar-collapsed');
        applyCollapsed(isNowCollapsed);
        localStorage.setItem(STORAGE_KEY, isNowCollapsed ? 'true' : 'false');
    });
})();