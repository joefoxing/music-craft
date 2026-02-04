# Unified Card System Documentation

## Overview

The Unified Card System is a comprehensive, reusable component architecture that consolidates all card implementations across the Music Cover Generator application. It provides a standardized interface for creating and managing cards while maintaining design consistency and improving maintainability.

## Architecture

### Core Components

1. **BaseCard** - Foundation class providing core card functionality
2. **Specialized Cards** - Specific implementations for different use cases
3. **CardFactory** - Factory pattern for creating cards
4. **CardManager** - Manages collections of cards
5. **CardUtils** - Utility functions for card operations

### Card Types

#### 1. HistoryCard
- **Purpose**: Display callback history entries
- **Features**: Status badges, timestamp, task ID display
- **Variants**: `default`, `compact`, `detailed`

#### 2. SongCard
- **Purpose**: Display audio tracks in library
- **Features**: Audio controls, metadata, favorite toggle, tags
- **Variants**: `default` (with controls), `minimal` (compact view)

#### 3. TemplateCard
- **Purpose**: Display music generation templates
- **Features**: Category badges, difficulty indicators, popularity stars
- **Variants**: `default`, `compact`, `detailed`

#### 4. LyricCard
- **Purpose**: Display generated lyrics
- **Features**: Expandable content, editing capabilities
- **Variants**: `default`, `compact`, `expanded`

#### 5. AudioPlayerCard
- **Purpose**: Display audio players in history modals
- **Features**: Full audio controls, download options
- **Variants**: `default`, `compact`

#### 6. VideoPlayerCard
- **Purpose**: Display video players in history modals
- **Features**: Video controls, status indicators
- **Variants**: `default`, `compact`

#### 7. ActivityFeedCard
- **Purpose**: Display activity feed items
- **Features**: Activity icons, timestamps, user info
- **Variants**: `default`, `compact`

## Usage Examples

### Basic Card Creation

```javascript
// Create a history card
const historyCard = new HistoryCard({
    data: {
        id: 'hist-123',
        task_id: 'abc-def-123',
        timestamp: new Date(),
        status_code: 200,
        callback_type: 'complete',
        tracks_count: 3
    },
    variant: 'default',
    clickable: true,
    hoverable: true
});

// Set up callbacks
historyCard.setCallbacks({
    onAction: (action, data, event) => {
        console.log('Action:', action, 'Data:', data);
    },
    onClick: (card, event) => {
        console.log('Card clicked:', card.getState());
    }
});

// Create and get the DOM element
const cardElement = historyCard.createElement();
document.getElementById('container').appendChild(cardElement);
```

### Using Card Factory

```javascript
// Auto-detect card type from data
const data = { timestamp: new Date(), task_id: 'abc123' };
const card = CardFactory.createCardFromData(data);

// Create multiple cards of the same type
const historyDataArray = [
    { id: 1, task_id: 'task-1', timestamp: new Date() },
    { id: 2, task_id: 'task-2', timestamp: new Date() }
];

const cards = CardFactory.createCards('history', historyDataArray, {
    clickable: true,
    onAction: handleHistoryAction
});
```

### Using Card Manager

```javascript
// Create a manager for a container
const manager = new CardManager({
    container: document.getElementById('history-container'),
    cardType: 'history',
    config: {
        enableSelection: true,
        enableSorting: true,
        enableFiltering: true,
        itemsPerPage: 20
    }
});

// Set up callbacks
manager.setCallbacks({
    onCardClick: (card, event) => {
        console.log('Card clicked:', card.data);
    },
    onCardAction: (card, action, event) => {
        console.log('Action:', action, 'Card:', card.data);
    }
});

// Add cards
manager.addCard(historyCard1);
manager.addCard(historyCard2);

// Render cards
manager.renderCards();

// Apply filters
manager.setFilters({
    search: 'task-1',
    status: 'success'
});

// Sort cards
manager.setSorting('timestamp', 'desc');
```

### Using Helper Functions

```javascript
// Quick creation using helpers
const songCard = CardHelpers.createSongCard({
    id: 'song-123',
    title: 'Amazing Song',
    artist: 'Great Artist',
    duration: 180,
    audio_url: '/path/to/audio.mp3'
}, {
    showControls: true,
    onAction: handleSongAction
});

// Create manager for container
const songManager = CardHelpers.createManagerForContainer(
    '#song-container',
    'song',
    {
        enableSelection: true,
        config: { itemsPerPage: 12 }
    }
);
```

## Configuration Options

### BaseCard Options

```javascript
{
    id: 'card-123',                    // Optional card ID
    className: 'custom-class',         // Additional CSS classes
    attributes: { 'data-custom': 'value' }, // Custom attributes
    interactive: true,                 // Enable keyboard navigation
    selectable: false,                // Enable selection
    hoverable: true,                  // Enable hover effects
    clickable: true,                 // Enable click handling
    theme: 'auto',                    // 'light', 'dark', 'auto'
    size: 'medium',                  // 'small', 'medium', 'large'
    variant: 'default'               // Card style variant
}
```

### CardManager Options

```javascript
{
    container: document.getElementById('container'), // Container element
    cardType: 'history',                          // Default card type
    enableSelection: false,                       // Enable card selection
    enableSorting: false,                        // Enable sorting
    enableFiltering: false,                      // Enable filtering
    enablePagination: false,                     // Enable pagination
    itemsPerPage: 20,                          // Items per page
    config: {
        // Additional configuration
    }
}
```

## Card Variants

### HistoryCard Variants

- **`default`**: Standard view with all information
- **`compact`**: Minimal view with essential information only
- **`detailed`**: Extended view with additional metadata

### SongCard Variants

- **`default`**: Full card with audio controls and metadata
- **`minimal`**: Compact view without controls

### TemplateCard Variants

- **`default`**: Standard template card with all features
- **`compact`**: Minimal template card
- **`detailed`**: Extended template card with additional info

## Styling

### CSS Classes

Cards automatically generate and manage these CSS classes:

- `.unified-card` - Base card class
- `.history-card` - History card specific
- `.song-card` - Song card specific
- `.template-card` - Template card specific
- `.lyric-card` - Lyric card specific
- `.audio-player-card` - Audio player card specific
- `.video-player-card` - Video player card specific
- `.activity-feed-card` - Activity feed card specific

### Custom Styling

```css
/* Customize card appearance */
.unified-card {
    /* Custom base styles */
}

.history-card {
    /* History-specific styles */
}

/* Hover effects */
.unified-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Selection state */
.unified-card.selected {
    border-color: #f20df2;
    box-shadow: 0 0 0 2px rgba(242, 13, 242, 0.2);
}
```

## Events and Callbacks

### Available Callbacks

```javascript
// BaseCard callbacks
{
    onClick: (card, event) => {},           // Card clicked
    onAction: (action, data, event) => {}, // Action button clicked
    onSelect: (card, selected) => {},      // Card selected/deselected
    onExpand: (card, expanded) => {},       // Card expanded/collapsed
    onHover: (card, isHovering) => {}      // Card hover state changed
}

// CardManager callbacks
{
    onCardClick: (card, event) => {},         // Card clicked
    onCardAction: (card, action, event) => {},// Card action triggered
    onCardSelect: (card, selected) => {},      // Card selection changed
    onCardExpand: (card, expanded) => {}      // Card expansion changed
}
```

### Keyboard Navigation

Cards support keyboard navigation:

- **`Enter/Space`**: Activate card (if interactive)
- **`Escape`**: Deselect card or collapse expanded card
- **`Arrow Keys`**: Navigate between cards (in manager)

## Integration Guide

### Updating Existing Components

1. **HistoryManager**: Updated to use `HistoryCard`
2. **SongLibrary**: Updated to use `SongCard`
3. **TemplateGallery**: Updated to use `TemplateCard`

### Migrating Custom Cards

```javascript
// Old implementation
function createCustomCard(data) {
    const card = document.createElement('div');
    card.className = 'custom-card';
    // ... manual DOM creation
    return card;
}

// New implementation
class CustomCard extends BaseCard {
    createElement() {
        const card = super.createElement();
        // Build your custom content
        return card;
    }
}

// Usage
const customCard = new CustomCard({
    data: yourData,
    variant: 'custom'
});
```

## Best Practices

### 1. Data Structure
```javascript
// Use consistent data structure
{
    id: 'unique-id',
    title: 'Display Title',
    description: 'Description',
    timestamp: new Date(),
    status: 'active', // or 'inactive', 'pending'
    metadata: {
        // Additional data
    }
}
```

### 2. Callback Management
```javascript
// Always set up callbacks
card.setCallbacks({
    onAction: handleAction,
    onClick: handleClick
});

// Clean up in manager
manager.setCallbacks({
    onCardAction: handleManagerAction
});
```

### 3. Performance
```javascript
// Use manager for multiple cards
const manager = new CardManager({
    container: container,
    cardType: type
});

// Batch operations
manager.addCards(cardsArray);
manager.renderCards();
```

### 4. Accessibility
```javascript
// Ensure interactive cards are focusable
const card = new HistoryCard({
    interactive: true,
    clickable: true
});

// Add ARIA attributes as needed
card.getElement().setAttribute('aria-label', 'History entry');
```

## Troubleshooting

### Common Issues

1. **Card not rendering**
   - Check if container exists
   - Verify data structure
   - Ensure callbacks are set

2. **Events not firing**
   - Verify callback functions are set
   - Check event propagation
   - Ensure card is interactive

3. **Styling issues**
   - Check CSS class conflicts
   - Verify Tailwind classes are loaded
   - Ensure dark mode classes

### Debug Mode

```javascript
// Enable debug logging
window.cardSystem.setDebug(true);

// Check card state
console.log(card.getState());

// Verify manager status
console.log(manager.getCards());
```

## Migration from Old System

### Step 1: Replace Card Creation
```javascript
// Old
const card = createHistoryCard(data);

// New
const card = new HistoryCard({ data });
```

### Step 2: Update Event Handling
```javascript
// Old
card.addEventListener('click', handler);

// New
card.setCallbacks({
    onClick: handler
});
```

### Step 3: Use Manager for Collections
```javascript
// Old - Manual DOM management
container.innerHTML = '';
cards.forEach(card => container.appendChild(card));

// New - Use CardManager
const manager = new CardManager({ container, cardType: 'history' });
manager.addCards(cards);
manager.renderCards();
```

## Future Enhancements

### Planned Features

1. **Drag & Drop**: Card reordering
2. **Virtual Scrolling**: Large card collections
3. **Animation System**: Smooth transitions
4. **Theme System**: Dynamic theming
5. **Export/Import**: Card configuration

### API Extensions

```javascript
// Planned methods
card.animate('slideIn');
card.setTheme('dark');
card.enableDragDrop();

manager.enableVirtualScroll();
manager.exportConfig();
```

## Support

For questions or issues:

1. Check this documentation
2. Review example implementations
3. Use browser developer tools for debugging
4. Test with the provided helper functions

The Unified Card System provides a robust foundation for all card-based UI components in the application, ensuring consistency, maintainability, and extensibility.