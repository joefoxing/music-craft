/**
 * Card System Index
 * Main entry point for the Unified Card System
 * 
 * This file exports all card components and utilities for easy importing
 * throughout the application.
 */

console.log('Card System loaded');

// Import all card components
import './unifiedCard.js';
import './specializedCards.js';
import './additionalCards.js';
import './cardFactory.js';
import './addButton.js';

/**
 * Main Card System class that provides a unified interface
 */
class CardSystem {
    constructor() {
        this.unifiedCardSystem = new UnifiedCardSystem();
    }
    
    /**
     * Create a single card of any supported type
     * @param {string} type - Card type ('history', 'song', 'template', 'lyric', 'audio-player', 'video-player', 'activity')
     * @param {Object} data - Data object for the card
     * @param {Object} options - Additional options
     * @returns {BaseCard} Created card instance
     */
    createCard(type, data, options = {}) {
        return this.unifiedCardSystem.createCard(type, data, options);
    }
    
    /**
     * Create a card manager for handling collections of cards
     * @param {Object} options - Manager configuration options
     * @returns {CardManager} Created manager instance
     */
    createManager(options = {}) {
        return this.unifiedCardSystem.createManager(options);
    }
    
    /**
     * Create multiple cards of the same type
     * @param {string} type - Card type
     * @param {Array} dataArray - Array of data objects
     * @param {Object} options - Common options for all cards
     * @returns {Array} Array of card instances
     */
    createCards(type, dataArray, options = {}) {
        return this.unifiedCardSystem.createCards(type, dataArray, options);
    }
    
    /**
     * Auto-detect card type from data and create appropriate card
     * @param {Object} data - Data object with type indicators
     * @param {Object} options - Additional options
     * @returns {BaseCard} Created card instance
     */
    createCardFromData(data, options = {}) {
        return CardFactory.createCardFromData(data, options);
    }
}

/**
 * Global card system instance
 */
window.cardSystem = new CardSystem();

/**
 * Convenience functions for common card operations
 */
const CardHelpers = {
    /**
     * Quick create a history card
     * @param {Object} historyData - History entry data
     * @param {Object} options - Additional options
     * @returns {HistoryCard} History card instance
     */
    createHistoryCard(historyData, options = {}) {
        return new HistoryCard({ data: historyData, ...options });
    },
    
    /**
     * Quick create a song card
     * @param {Object} songData - Song data
     * @param {Object} options - Additional options
     * @returns {SongCard} Song card instance
     */
    createSongCard(songData, options = {}) {
        return new SongCard({ data: songData, ...options });
    },
    
    /**
     * Quick create a template card
     * @param {Object} templateData - Template data
     * @param {Object} options - Additional options
     * @returns {TemplateCard} Template card instance
     */
    createTemplateCard(templateData, options = {}) {
        return new TemplateCard({ data: templateData, ...options });
    },
    
    /**
     * Quick create a lyric card
     * @param {Object} lyricData - Lyric data
     * @param {Object} options - Additional options
     * @returns {LyricCard} Lyric card instance
     */
    createLyricCard(lyricData, options = {}) {
        return new LyricCard({ data: lyricData, ...options });
    },
    
    /**
     * Quick create an audio player card
     * @param {Object} audioData - Audio track data
     * @param {Object} options - Additional options
     * @returns {AudioPlayerCard} Audio player card instance
     */
    createAudioPlayerCard(audioData, options = {}) {
        return new AudioPlayerCard({ data: audioData, ...options });
    },
    
    /**
     * Quick create a video player card
     * @param {Object} videoData - Video data
     * @param {Object} options - Additional options
     * @returns {VideoPlayerCard} Video player card instance
     */
    createVideoPlayerCard(videoData, options = {}) {
        return new VideoPlayerCard({ data: videoData, ...options });
    },
    
    /**
     * Quick create an activity feed card
     * @param {Object} activityData - Activity data
     * @param {Object} options - Additional options
     * @returns {ActivityFeedCard} Activity feed card instance
     */
    createActivityCard(activityData, options = {}) {
        return new ActivityFeedCard({ data: activityData, ...options });
    },
    
    /**
     * Create a card manager for a container
     * @param {HTMLElement|string} container - Container element or selector
     * @param {string} cardType - Type of cards to manage
     * @param {Object} options - Manager options
     * @returns {CardManager} Card manager instance
     */
    createManagerForContainer(container, cardType, options = {}) {
        const containerEl = typeof container === 'string' ? 
            document.querySelector(container) : container;
        
        if (!containerEl) {
            throw new Error(`Container not found: ${container}`);
        }
        
        return new CardManager({
            container: containerEl,
            cardType,
            ...options
        });
    }
};

// Export globally
window.CardHelpers = CardHelpers;

// Example usage documentation (for developers)
/*
USAGE EXAMPLES:

// 1. Create a single card
const historyCard = new HistoryCard({
    data: { id: 1, task_id: 'abc123', timestamp: new Date() },
    clickable: true,
    onAction: (action, data) => console.log(action, data)
});

// 2. Create using helpers
const songCard = CardHelpers.createSongCard(songData, {
    showControls: true,
    onAction: handleSongAction
});

// 3. Create a card manager
const manager = CardHelpers.createManagerForContainer('#container', 'history', {
    enableSelection: true,
    enableSorting: true,
    onCardClick: handleCardClick
});

// 4. Add cards to manager
manager.addCard(historyCard);
manager.renderCards();

// 5. Use the main card system
const cardSystem = new CardSystem();
const templateCard = cardSystem.createCard('template', templateData);
const manager = cardSystem.createManager({
    container: document.getElementById('gallery'),
    enableFiltering: true
});
*/