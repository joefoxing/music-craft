/**
 * Unified Card System for Music Cover Generator
 * A comprehensive, reusable card component system that consolidates all card implementations
 * across the application with consistent styling, behavior, and maintainability.
 */

console.log('Unified Card System loaded');

/**
 * Base Card class providing core card functionality
 */
class BaseCard {
    constructor(options = {}) {
        this.options = {
            id: options.id || null,
            className: options.className || '',
            attributes: options.attributes || {},
            interactive: options.interactive !== false,
            selectable: options.selectable || false,
            hoverable: options.hoverable !== false,
            clickable: options.clickable || false,
            theme: options.theme || 'auto', // 'light', 'dark', 'auto'
            size: options.size || 'medium', // 'small', 'medium', 'large'
            variant: options.variant || 'default', // 'default', 'minimal', 'detailed'
            ...options
        };
        
        this.element = null;
        this.eventHandlers = new Map();
        this.state = {
            selected: false,
            loading: false,
            expanded: false,
            active: false
        };
        
        this.callbacks = {
            onClick: null,
            onSelect: null,
            onExpand: null,
            onAction: null,
            onHover: null
        };
    }
    
    /**
     * Create the base card element
     * @returns {HTMLElement} Card element
     */
    createElement() {
        const card = document.createElement('div');
        card.className = this.buildCardClasses();
        card.dataset.cardType = this.constructor.name.replace('Card', '').toLowerCase();
        
        if (this.options.id) {
            card.id = this.options.id;
        }
        
        // Set custom attributes
        Object.entries(this.options.attributes).forEach(([key, value]) => {
            card.setAttribute(key, value);
        });
        
        // Add event listeners
        this.setupEventListeners(card);
        
        this.element = card;
        return card;
    }
    
    /**
     * Build CSS classes for the card
     * @returns {string} CSS classes
     */
    buildCardClasses() {
        const classes = ['unified-card'];
        
        // Base styling
        classes.push('bg-white', 'dark:bg-surface-dark', 'rounded-xl', 'border', 'border-slate-200', 'dark:border-border-dark', 'shadow-sm');
        
        // Interactive states
        if (this.options.interactive) {
            classes.push('transition-all', 'duration-200');
        }
        
        if (this.options.hoverable) {
            classes.push('hover:shadow-lg', 'hover:border-primary/50');
        }
        
        if (this.options.clickable) {
            classes.push('cursor-pointer');
        }
        
        // Size variants
        switch (this.options.size) {
            case 'small':
                classes.push('p-3');
                break;
            case 'large':
                classes.push('p-8');
                break;
            default:
                classes.push('p-6');
        }
        
        // Style variants
        switch (this.options.variant) {
            case 'minimal':
                classes.push('shadow-none', 'border-0', 'bg-transparent', 'dark:bg-transparent');
                break;
            case 'detailed':
                classes.push('shadow-xl', 'border-2');
                break;
        }
        
        // State classes
        if (this.state.selected) {
            classes.push('ring-2', 'ring-primary', 'border-primary');
        }
        
        if (this.state.loading) {
            classes.push('opacity-60', 'pointer-events-none');
        }
        
        if (this.state.expanded) {
            classes.push('shadow-2xl', 'ring-1', 'ring-primary/20');
        }
        
        // Custom classes
        if (this.options.className) {
            classes.push(...this.options.className.split(' '));
        }
        
        return classes.join(' ');
    }
    
    /**
     * Setup event listeners for the card
     * @param {HTMLElement} card - Card element
     */
    setupEventListeners(card) {
        if (this.options.clickable) {
            card.addEventListener('click', (e) => this.handleClick(e));
        }
        
        if (this.options.selectable) {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('button, a, input, select, textarea')) {
                    this.toggleSelection();
                }
            });
        }
        
        if (this.options.hoverable) {
            card.addEventListener('mouseenter', () => this.handleHover(true));
            card.addEventListener('mouseleave', () => this.handleHover(false));
        }
        
        // Keyboard accessibility
        card.setAttribute('tabindex', this.options.interactive ? '0' : '-1');
        card.addEventListener('keydown', (e) => this.handleKeydown(e));
    }
    
    /**
     * Handle card click events
     * @param {Event} e - Click event
     */
    handleClick(e) {
        if (this.callbacks.onClick) {
            this.callbacks.onClick(this, e);
        }
    }
    
    /**
     * Handle card hover events
     * @param {boolean} isHovering - Whether hovering
     */
    handleHover(isHovering) {
        this.state.active = isHovering;
        
        if (this.callbacks.onHover) {
            this.callbacks.onHover(this, isHovering);
        }
        
        // Add/remove hover state classes
        if (this.element) {
            if (isHovering) {
                this.element.classList.add('card-hover');
            } else {
                this.element.classList.remove('card-hover');
            }
        }
    }
    
    /**
     * Handle keyboard events for accessibility
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeydown(e) {
        switch (e.key) {
            case 'Enter':
            case ' ':
                if (this.options.interactive) {
                    e.preventDefault();
                    this.handleClick(e);
                }
                break;
            case 'Escape':
                this.handleEscape();
                break;
        }
    }
    
    /**
     * Handle escape key
     */
    handleEscape() {
        if (this.state.expanded) {
            this.collapse();
        } else if (this.state.selected && this.options.selectable) {
            this.deselect();
        }
    }
    
    /**
     * Toggle card selection
     */
    toggleSelection() {
        if (this.state.selected) {
            this.deselect();
        } else {
            this.select();
        }
    }
    
    /**
     * Select the card
     */
    select() {
        this.state.selected = true;
        this.updateStateClasses();
        
        if (this.callbacks.onSelect) {
            this.callbacks.onSelect(this, true);
        }
    }
    
    /**
     * Deselect the card
     */
    deselect() {
        this.state.selected = false;
        this.updateStateClasses();
        
        if (this.callbacks.onSelect) {
            this.callbacks.onSelect(this, false);
        }
    }
    
    /**
     * Expand the card
     */
    expand() {
        this.state.expanded = true;
        this.updateStateClasses();
        
        if (this.callbacks.onExpand) {
            this.callbacks.onExpand(this, true);
        }
    }
    
    /**
     * Collapse the card
     */
    collapse() {
        this.state.expanded = false;
        this.updateStateClasses();
        
        if (this.callbacks.onExpand) {
            this.callbacks.onExpand(this, false);
        }
    }
    
    /**
     * Set loading state
     * @param {boolean} loading - Loading state
     */
    setLoading(loading) {
        this.state.loading = loading;
        this.updateStateClasses();
    }
    
    /**
     * Update CSS classes based on current state
     */
    updateStateClasses() {
        if (!this.element) return;
        
        // Remove all state classes
        this.element.classList.remove('ring-2', 'ring-primary', 'border-primary', 'opacity-60', 'pointer-events-none', 'shadow-2xl', 'ring-1', 'ring-primary/20');
        
        // Re-add based on current state
        if (this.state.selected) {
            this.element.classList.add('ring-2', 'ring-primary', 'border-primary');
        }
        
        if (this.state.loading) {
            this.element.classList.add('opacity-60', 'pointer-events-none');
        }
        
        if (this.state.expanded) {
            this.element.classList.add('shadow-2xl', 'ring-1', 'ring-primary/20');
        }
        
        // Rebuild main classes
        this.element.className = this.buildCardClasses();
    }
    
    /**
     * Add a custom event handler
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
        
        if (this.element) {
            this.element.addEventListener(event, handler);
        }
    }
    
    /**
     * Remove a custom event handler
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
        
        if (this.element) {
            this.element.removeEventListener(event, handler);
        }
    }
    
    /**
     * Set callbacks
     * @param {Object} callbacks - Callback functions
     */
    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }
    
    /**
     * Get the card element
     * @returns {HTMLElement} Card element
     */
    getElement() {
        return this.element;
    }
    
    /**
     * Get card state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Destroy the card and clean up event listeners
     */
    destroy() {
        if (this.element) {
            // Remove all custom event listeners
            this.eventHandlers.forEach((handlers, event) => {
                handlers.forEach(handler => {
                    this.element.removeEventListener(event, handler);
                });
            });
            
            // Remove element
            this.element.remove();
        }
        
        this.element = null;
        this.eventHandlers.clear();
    }
}

/**
 * Utility functions for card system
 */
const CardUtils = {
    /**
     * Create a status badge element
     * @param {string} status - Status type
     * @param {string} text - Status text
     * @returns {HTMLElement} Badge element
     */
    createStatusBadge(status, text) {
        const badge = document.createElement('span');
        badge.className = `status-badge ${this.getStatusBadgeClasses(status)}`;
        badge.textContent = text;
        return badge;
    },
    
    /**
     * Get CSS classes for status badges
     * @param {string} status - Status type
     * @returns {string} CSS classes
     */
    getStatusBadgeClasses(status) {
        const statusClasses = {
            success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
            warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
            pending: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
        };
        
        return statusClasses[status] || statusClasses.info;
    },
    
    /**
     * Create an action button
     * @param {string} text - Button text
     * @param {string} icon - Material icon name
     * @param {string} variant - Button variant
     * @param {Function} onClick - Click handler
     * @returns {HTMLElement} Button element
     */
    createActionButton(text, icon, variant = 'primary', onClick = null) {
        const button = document.createElement('button');
        button.className = `action-btn ${this.getButtonClasses(variant)}`;
        button.setAttribute('data-action', text.toLowerCase().replace(/\s+/g, '-'));
        
        button.innerHTML = `
            ${icon ? `<span class="material-symbols-outlined text-sm mr-1">${icon}</span>` : ''}
            <span>${text}</span>
        `;
        
        if (onClick) {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                onClick(e);
            });
        }
        
        return button;
    },
    
    /**
     * Get CSS classes for action buttons
     * @param {string} variant - Button variant
     * @returns {string} CSS classes
     */
    getButtonClasses(variant) {
        const variantClasses = {
            primary: 'bg-primary hover:bg-primary-dark text-white',
            secondary: 'bg-slate-600 hover:bg-slate-700 text-white',
            success: 'bg-green-600 hover:bg-green-700 text-white',
            danger: 'bg-red-600 hover:bg-red-700 text-white',
            warning: 'bg-yellow-600 hover:bg-yellow-700 text-white',
            info: 'bg-blue-600 hover:bg-blue-700 text-white'
        };
        
        const baseClasses = 'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center';
        return `${baseClasses} ${variantClasses[variant] || variantClasses.primary}`;
    },
    
    /**
     * Create a metadata item
     * @param {string} label - Metadata label
     * @param {string} value - Metadata value
     * @param {string} icon - Optional icon
     * @returns {HTMLElement} Metadata element
     */
    createMetadataItem(label, value, icon = null) {
        const item = document.createElement('div');
        item.className = 'metadata-item';
        
        const content = icon ? `
            <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-slate-500 text-sm">${icon}</span>
                <span class="text-slate-600 dark:text-slate-400">${value}</span>
            </div>
        ` : `<span class="text-slate-600 dark:text-slate-400">${value}</span>`;
        
        item.innerHTML = `
            <p class="text-xs text-slate-500 dark:text-slate-400">${label}</p>
            ${content}
        `;
        
        return item;
    },
    
    /**
     * Format duration in MM:SS or HH:MM:SS format
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration
     */
    formatDuration(seconds) {
        if (!seconds) return '--:--';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },
    
    /**
     * Format file size in human readable format
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize(bytes) {
        if (!bytes) return '--';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${Math.round(bytes / Math.pow(1024, i) * 10) / 10} ${sizes[i]}`;
    },
    
    /**
     * Format time ago from date
     * @param {Date|string} date - Date object or string
     * @returns {string} Formatted time ago
     */
    formatTimeAgo(date) {
        const now = new Date();
        const inputDate = new Date(date);
        const diffMs = now - inputDate;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return `${Math.floor(diffDays / 7)}w ago`;
    },
    
    /**
     * Create a tag element
     * @param {string} text - Tag text
     * @param {string} variant - Tag variant
     * @returns {HTMLElement} Tag element
     */
    createTag(text, variant = 'default') {
        const tag = document.createElement('span');
        tag.className = `tag tag-${variant}`;
        tag.textContent = text;
        return tag;
    },
    
    /**
     * Create an icon element
     * @param {string} icon - Icon name
     * @param {string} className - Additional CSS classes
     * @returns {HTMLElement} Icon element
     */
    createIcon(icon, className = '') {
        const iconElement = document.createElement('span');
        iconElement.className = `material-symbols-outlined ${className}`;
        iconElement.textContent = icon;
        return iconElement;
    }
};

/**
 * Export for use in other modules
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        BaseCard,
        CardUtils
    };
} else {
    window.BaseCard = BaseCard;
    window.CardUtils = CardUtils;
}