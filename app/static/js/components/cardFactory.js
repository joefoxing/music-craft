/**
 * Card Factory and Manager
 * Provides a unified interface for creating and managing all card types
 */

console.log('Card Factory loaded');

/**
 * Card Factory - Creates different types of cards based on configuration
 */
class CardFactory {
    /**
     * Create a card based on type and options
     * @param {string} type - Card type ('history', 'song', 'template', 'lyric', 'audio-player', 'video-player', 'activity', 'add-button')
     * @param {Object} options - Card options
     * @returns {BaseCard} Created card instance
     */
    static createCard(type, options = {}) {
        switch (type.toLowerCase()) {
            case 'history':
                return new HistoryCard(options);
            case 'song':
                return new SongCard(options);
            case 'template':
                return new TemplateCard(options);
            case 'lyric':
                return new LyricCard(options);
            case 'audio-player':
                return new AudioPlayerCard(options);
            case 'video-player':
                return new VideoPlayerCard(options);
            case 'activity':
                return new ActivityFeedCard(options);
            case 'add-button':
                return new AddButtonCard(options);
            default:
                console.warn(`Unknown card type: ${type}. Using default BaseCard.`);
                return new BaseCard(options);
        }
    }
    
    /**
     * Create multiple cards of the same type
     * @param {string} type - Card type
     * @param {Array} dataArray - Array of data objects
     * @param {Object} commonOptions - Common options for all cards
     * @returns {Array} Array of card instances
     */
    static createCards(type, dataArray, commonOptions = {}) {
        return dataArray.map((data, index) => {
            const options = {
                ...commonOptions,
                data,
                id: commonOptions.idPrefix ? `${commonOptions.idPrefix}-${index}` : undefined
            };
            return this.createCard(type, options);
        });
    }
    
    /**
     * Create a card from template data (auto-detects type)
     * @param {Object} data - Data object with type indicator
     * @param {Object} options - Additional options
     * @returns {BaseCard} Created card instance
     */
    static createCardFromData(data, options = {}) {
        // Auto-detect card type based on data structure
        if (data.timestamp && data.task_id) {
            return this.createCard('history', { data, ...options });
        } else if (data.audio_url || data.duration !== undefined) {
            return this.createCard('song', { data, ...options });
        } else if (data.category && data.description) {
            return this.createCard('template', { data, ...options });
        } else if (data.content || data.lyrics) {
            return this.createCard('lyric', { data, ...options });
        } else if (data.video_url || data.video_task_id) {
            return this.createCard('video-player', { data, ...options });
        } else if (data.activity_type || data.type) {
            return this.createCard('activity', { data, ...options });
        } else {
            // Default fallback
            return this.createCard('default', { data, ...options });
        }
    }
}

/**
 * Card Manager - Manages collections of cards
 */
class CardManager {
    constructor(options = {}) {
        this.cards = [];
        this.container = options.container || null;
        this.cardType = options.cardType || 'default';
        this.options = options;
        this.callbacks = {
            onCardClick: null,
            onCardAction: null,
            onCardSelect: null,
            onCardExpand: null
        };
        
        // Configuration
        this.config = {
            enableSelection: options.enableSelection || false,
            enableSorting: options.enableSorting || false,
            enableFiltering: options.enableFiltering || false,
            enablePagination: options.enablePagination || false,
            itemsPerPage: options.itemsPerPage || 20,
            ...options.config
        };
        
        // State
        this.state = {
            selectedCards: new Set(),
            currentPage: 1,
            sortField: null,
            sortDirection: 'asc',
            filters: {}
        };
    }
    
    /**
     * Initialize the card manager
     */
    initialize() {
        if (this.container) {
            this.setupEventListeners();
        }
    }
    
    /**
     * Setup event listeners for the container
     */
    setupEventListeners() {
        if (!this.container) return;
        
        // Event delegation for card actions
        this.container.addEventListener('click', (e) => {
            const cardElement = e.target.closest('.unified-card');
            if (!cardElement) return;
            
            const cardIndex = parseInt(cardElement.dataset.cardIndex);
            const card = this.cards[cardIndex];
            
            if (!card) return;
            
            // Handle action button clicks
            const actionButton = e.target.closest('[data-action]');
            if (actionButton) {
                const action = actionButton.dataset.action;
                this.handleCardAction(card, action, e);
                return;
            }
            
            // Handle card clicks
            if (this.callbacks.onCardClick) {
                this.callbacks.onCardClick(card, e);
            }
        });
        
        // Handle keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
    }
    
    /**
     * Add a card to the manager
     * @param {BaseCard} card - Card instance
     * @param {number} index - Optional index to insert at
     */
    addCard(card, index = null) {
        // Set up card callbacks
        card.setCallbacks({
            onClick: (card, e) => this.handleCardClick(card, e),
            onAction: (action, data, e) => this.handleCardAction(card, action, e),
            onSelect: (card, selected) => this.handleCardSelect(card, selected),
            onExpand: (card, expanded) => this.handleCardExpand(card, expanded)
        });
        
        if (index !== null && index >= 0 && index < this.cards.length) {
            this.cards.splice(index, 0, card);
        } else {
            this.cards.push(card);
        }
        
        this.updateCardIndexes();
    }
    
    /**
     * Remove a card from the manager
     * @param {BaseCard|number} card - Card instance or index
     */
    removeCard(card) {
        let index;
        
        if (typeof card === 'number') {
            index = card;
        } else {
            index = this.cards.indexOf(card);
        }
        
        if (index > -1) {
            const removedCard = this.cards.splice(index, 1)[0];
            removedCard.destroy();
            this.updateCardIndexes();
        }
    }
    
    /**
     * Clear all cards
     */
    clearCards() {
        this.cards.forEach(card => card.destroy());
        this.cards = [];
        this.state.selectedCards.clear();
        
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
    
    /**
     * Render cards to container
     */
    renderCards() {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        
        const cardsToRender = this.getVisibleCards();
        
        cardsToRender.forEach((card, index) => {
            const cardElement = card.getElement();
            cardElement.dataset.cardIndex = this.cards.indexOf(card);
            this.container.appendChild(cardElement);
        });
    }
    
    /**
     * Get visible cards based on current filters and pagination
     * @returns {Array} Visible cards
     */
    getVisibleCards() {
        let visibleCards = [...this.cards];
        
        // Apply filters
        if (this.config.enableFiltering && Object.keys(this.state.filters).length > 0) {
            visibleCards = visibleCards.filter(card => this.applyFilters(card));
        }
        
        // Apply sorting
        if (this.config.enableSorting && this.state.sortField) {
            visibleCards = this.applySorting(visibleCards);
        }
        
        // Apply pagination
        if (this.config.enablePagination) {
            const startIndex = (this.state.currentPage - 1) * this.config.itemsPerPage;
            const endIndex = startIndex + this.config.itemsPerPage;
            visibleCards = visibleCards.slice(startIndex, endIndex);
        }
        
        return visibleCards;
    }
    
    /**
     * Apply filters to a card
     * @param {BaseCard} card - Card to filter
     * @returns {boolean} Whether card passes filters
     */
    applyFilters(card) {
        const data = card.data || {};
        
        return Object.entries(this.state.filters).every(([filterKey, filterValue]) => {
            if (!filterValue) return true;
            
            switch (filterKey) {
                case 'search':
                    const searchTerm = filterValue.toLowerCase();
                    return this.searchInCard(data, searchTerm);
                case 'status':
                    return data.status === filterValue;
                case 'category':
                    return data.category === filterValue;
                case 'type':
                    return data.type === filterValue;
                default:
                    return true;
            }
        });
    }
    
    /**
     * Search in card data
     * @param {Object} data - Card data
     * @param {string} searchTerm - Search term
     * @returns {boolean} Whether search term is found
     */
    searchInCard(data, searchTerm) {
        const searchableFields = ['title', 'name', 'description', 'artist', 'content', 'lyrics'];
        
        return searchableFields.some(field => {
            const value = data[field];
            return value && value.toString().toLowerCase().includes(searchTerm);
        });
    }
    
    /**
     * Apply sorting to cards
     * @param {Array} cards - Cards to sort
     * @returns {Array} Sorted cards
     */
    applySorting(cards) {
        const { sortField, sortDirection } = this.state;
        
        return cards.sort((a, b) => {
            const aValue = this.getSortValue(a, sortField);
            const bValue = this.getSortValue(b, sortField);
            
            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            if (aValue > bValue) comparison = 1;
            
            return sortDirection === 'desc' ? -comparison : comparison;
        });
    }
    
    /**
     * Get sort value for a card
     * @param {BaseCard} card - Card to get value from
     * @param {string} field - Sort field
     * @returns {*} Sort value
     */
    getSortValue(card, field) {
        const data = card.data || {};
        
        switch (field) {
            case 'title':
            case 'name':
                return (data.title || data.name || '').toLowerCase();
            case 'date':
            case 'timestamp':
                return new Date(data.timestamp || data.created_at || 0);
            case 'duration':
                return data.duration || 0;
            case 'size':
                return data.file_size || 0;
            case 'popularity':
                return data.popularity || 0;
            default:
                return data[field] || '';
        }
    }
    
    /**
     * Handle card click
     * @param {BaseCard} card - Clicked card
     * @param {Event} e - Click event
     */
    handleCardClick(card, e) {
        if (this.callbacks.onCardClick) {
            this.callbacks.onCardClick(card, e);
        }
    }
    
    /**
     * Handle card action
     * @param {BaseCard} card - Card that triggered action
     * @param {string} action - Action type
     * @param {Event} e - Event
     */
    handleCardAction(card, action, e) {
        if (this.callbacks.onCardAction) {
            this.callbacks.onCardAction(card, action, e);
        }
    }
    
    /**
     * Handle card selection
     * @param {BaseCard} card - Selected/deselected card
     * @param {boolean} selected - Selection state
     */
    handleCardSelect(card, selected) {
        const cardIndex = this.cards.indexOf(card);
        
        if (selected) {
            this.state.selectedCards.add(cardIndex);
        } else {
            this.state.selectedCards.delete(cardIndex);
        }
        
        if (this.callbacks.onCardSelect) {
            this.callbacks.onCardSelect(card, selected);
        }
    }
    
    /**
     * Handle card expansion
     * @param {BaseCard} card - Expanded/collapsed card
     * @param {boolean} expanded - Expansion state
     */
    handleCardExpand(card, expanded) {
        if (this.callbacks.onCardExpand) {
            this.callbacks.onCardExpand(card, expanded);
        }
    }
    
    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyboardNavigation(e) {
        const selectedIndexes = Array.from(this.state.selectedCards);
        const focusedIndex = this.getFocusedCardIndex();
        
        switch (e.key) {
            case 'ArrowDown':
            case 'ArrowUp':
                e.preventDefault();
                this.navigateCards(e.key === 'ArrowDown' ? 1 : -1, focusedIndex);
                break;
            case ' ':
            case 'Enter':
                e.preventDefault();
                if (focusedIndex !== -1 && this.config.enableSelection) {
                    const card = this.cards[focusedIndex];
                    card.toggleSelection();
                }
                break;
            case 'Escape':
                this.clearSelection();
                break;
        }
    }
    
    /**
     * Navigate between cards using keyboard
     * @param {number} direction - Direction (-1 for up, 1 for down)
     * @param {number} currentIndex - Current focused index
     */
    navigateCards(direction, currentIndex) {
        const visibleCards = this.getVisibleCards();
        const visibleIndexes = visibleCards.map(card => this.cards.indexOf(card));
        
        let nextIndex = currentIndex;
        const currentVisibleIndex = visibleIndexes.indexOf(currentIndex);
        
        if (currentVisibleIndex !== -1) {
            nextIndex = Math.max(0, Math.min(visibleIndexes.length - 1, currentVisibleIndex + direction));
            const targetCardIndex = visibleIndexes[nextIndex];
            const targetCard = this.cards[targetCardIndex];
            
            if (targetCard && targetCard.getElement()) {
                targetCard.getElement().focus();
            }
        }
    }
    
    /**
     * Get currently focused card index
     * @returns {number} Focused card index or -1
     */
    getFocusedCardIndex() {
        const activeElement = document.activeElement;
        if (!activeElement || !activeElement.classList.contains('unified-card')) {
            return -1;
        }
        
        return parseInt(activeElement.dataset.cardIndex) || -1;
    }
    
    /**
     * Clear all selections
     */
    clearSelection() {
        this.state.selectedCards.forEach(index => {
            const card = this.cards[index];
            if (card) {
                card.deselect();
            }
        });
        this.state.selectedCards.clear();
    }
    
    /**
     * Get selected cards
     * @returns {Array} Selected card instances
     */
    getSelectedCards() {
        return Array.from(this.state.selectedCards)
            .map(index => this.cards[index])
            .filter(card => card);
    }
    
    /**
     * Set filters
     * @param {Object} filters - Filter object
     */
    setFilters(filters) {
        this.state.filters = { ...filters };
        this.state.currentPage = 1;
        this.renderCards();
    }
    
    /**
     * Set sorting
     * @param {string} field - Sort field
     * @param {string} direction - Sort direction ('asc' or 'desc')
     */
    setSorting(field, direction = 'asc') {
        this.state.sortField = field;
        this.state.sortDirection = direction;
        this.renderCards();
    }
    
    /**
     * Set pagination
     * @param {number} page - Page number
     */
    setPage(page) {
        if (page >= 1 && page <= this.getTotalPages()) {
            this.state.currentPage = page;
            this.renderCards();
        }
    }
    
    /**
     * Get total pages
     * @returns {number} Total pages
     */
    getTotalPages() {
        const totalItems = this.cards.length;
        return Math.ceil(totalItems / this.config.itemsPerPage);
    }
    
    /**
     * Update card indexes after adding/removing cards
     */
    updateCardIndexes() {
        this.cards.forEach((card, index) => {
            if (card.getElement()) {
                card.getElement().dataset.cardIndex = index;
            }
        });
    }
    
    /**
     * Set callbacks
     * @param {Object} callbacks - Callback functions
     */
    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }
    
    /**
     * Get all cards
     * @returns {Array} All card instances
     */
    getCards() {
        return [...this.cards];
    }
    
    /**
     * Get card by index
     * @param {number} index - Card index
     * @returns {BaseCard|null} Card instance or null
     */
    getCard(index) {
        return this.cards[index] || null;
    }
    
    /**
     * Destroy the card manager and clean up
     */
    destroy() {
        this.clearCards();
        this.container = null;
        this.callbacks = {};
    }
}

/**
 * Unified Card System - Main entry point
 */
class UnifiedCardSystem {
    constructor() {
        this.factories = {
            card: CardFactory,
            manager: CardManager
        };
    }
    
    /**
     * Create a single card
     * @param {string} type - Card type
     * @param {Object} data - Card data
     * @param {Object} options - Card options
     * @returns {BaseCard} Created card
     */
    createCard(type, data, options = {}) {
        return this.factories.card.createCard(type, { data, ...options });
    }
    
    /**
     * Create a card manager
     * @param {Object} options - Manager options
     * @returns {CardManager} Created manager
     */
    createManager(options = {}) {
        return new this.factories.manager(options);
    }
    
    /**
     * Create cards from array of data
     * @param {string} type - Card type
     * @param {Array} dataArray - Array of data objects
     * @param {Object} options - Common options
     * @returns {Array} Array of created cards
     */
    createCards(type, dataArray, options = {}) {
        return this.factories.card.createCards(type, dataArray, options);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CardFactory,
        CardManager,
        UnifiedCardSystem
    };
} else {
    window.CardFactory = CardFactory;
    window.CardManager = CardManager;
    window.UnifiedCardSystem = UnifiedCardSystem;
}