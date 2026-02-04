# Activity Feed Component Design

## Overview
The Activity Feed component will replace the placeholder "Recent Generations" section in the dashboard with real-time activity data from the history system.

## Component Architecture

### 1. JavaScript Component: `activity-feed.js`
Location: `app/static/js/components/activityFeed.js`

**Responsibilities:**
- Fetch activity data from `/api/user-activity` endpoint
- Render activity cards in the dashboard
- Handle user interactions (play audio, view details, etc.)
- Provide filtering and sorting options
- Show loading/empty/error states

**Key Functions:**
- `ActivityFeed.initialize()` - Initialize component with DOM elements
- `ActivityFeed.loadActivities()` - Fetch and render activities
- `ActivityFeed.createActivityCard()` - Create HTML for a single activity card
- `ActivityFeed.filterActivities()` - Filter activities by type/status
- `ActivityFeed.refresh()` - Manually refresh the feed

### 2. Data Structure
The `/api/user-activity` endpoint will return an array of activity objects with this structure:
```json
{
  "activities": [
    {
      "id": "entry_id",
      "task_id": "task_123",
      "timestamp": "2024-01-12T01:30:00Z",
      "type": "audio" | "video",
      "status": "success" | "failed" | "processing",
      "title": "Generated track title",
      "description": "Track description or prompt",
      "duration": "02:14",
      "image_url": "https://...",
      "audio_url": "https://...",
      "video_url": "https://...",
      "user": {
        "id": "user_id",
        "name": "User Name",
        "avatar": "https://..."
      },
      "metadata": {
        "model": "V4",
        "style": "Synthwave",
        "tags": ["cyberpunk", "upbeat"]
      }
    }
  ]
}
```

### 3. Activity Card Design
Each activity card will have:
- **Header**: User avatar + name, timestamp, status badge
- **Thumbnail**: Generated image or video thumbnail
- **Content**: Title, description, metadata tags
- **Media Controls**: Play/pause button for audio, play button for video
- **Actions**: View details, download, create video (if applicable)
- **Footer**: Duration, model info, quick actions

### 4. Integration Points

**With Existing Components:**
- Use `AudioPlayerComponent` for audio playback
- Use `HistoryManager` for viewing detailed history
- Use existing notification system for errors/success messages
- Use existing video creation modal for video generation

**DOM Structure in index.html:**
Replace lines 223-341 with:
```html
<!-- Activity Feed -->
<section class="flex flex-col gap-4" id="activityFeedSection">
  <div class="flex items-center justify-between">
    <h3 class="text-xl font-bold dark:text-white text-slate-900">Recent Activity</h3>
    <div class="flex items-center gap-3">
      <!-- Filter dropdown -->
      <select id="activityFilter" class="bg-surface-dark text-white text-sm rounded-lg px-3 py-1.5 border border-border-dark">
        <option value="all">All Activities</option>
        <option value="audio">Audio Only</option>
        <option value="video">Video Only</option>
        <option value="today">Today</option>
      </select>
      <!-- Refresh button -->
      <button id="refreshActivities" class="p-1.5 rounded hover:bg-white/10 text-white">
        <span class="material-symbols-outlined text-[20px]">refresh</span>
      </button>
    </div>
  </div>
  
  <!-- Loading state -->
  <div id="activityLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-4">
    <!-- Skeleton cards will be inserted here -->
  </div>
  
  <!-- Empty state -->
  <div id="activityEmpty" class="hidden text-center py-12">
    <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">music_off</span>
    <p class="text-slate-500 dark:text-slate-400">No recent activity yet.</p>
    <p class="text-sm text-slate-400 mt-1">Generate your first cover to see it here!</p>
  </div>
  
  <!-- Error state -->
  <div id="activityError" class="hidden text-center py-12">
    <span class="material-symbols-outlined text-4xl text-red-400 mb-3">error</span>
    <p class="text-slate-500 dark:text-slate-400">Failed to load activity feed.</p>
    <button id="retryActivities" class="mt-3 px-4 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-bold rounded-lg">
      Retry
    </button>
  </div>
  
  <!-- Activity cards container -->
  <div id="activityCards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-4">
    <!-- Activity cards will be dynamically inserted here -->
  </div>
</section>
```

### 5. Implementation Steps

**Step 1: Create Activity Feed Component**
- Create `app/static/js/components/activityFeed.js`
- Implement core functionality (fetching, rendering, filtering)
- Add event listeners for filtering and refresh

**Step 2: Update index.html**
- Replace placeholder section with new activity feed structure
- Include the new component script
- Add necessary CSS classes

**Step 3: Update Backend**
- Ensure `/api/user-activity` endpoint returns the correct data format
- Add user information to activity data (if available)
- Handle pagination for large activity sets

**Step 4: Integration Testing**
- Test loading states
- Test error handling
- Test filtering functionality
- Test audio/video playback integration

### 6. Styling Considerations
- Maintain consistency with existing card designs
- Use Tailwind CSS classes from the current design
- Ensure dark/light theme compatibility
- Responsive design for mobile/tablet/desktop

### 7. Performance Considerations
- Implement lazy loading for images
- Debounce filter/search inputs
- Cache activity data with appropriate TTL
- Use Intersection Observer for infinite scroll (future enhancement)

### 8. Accessibility
- Proper ARIA labels for interactive elements
- Keyboard navigation support
- Screen reader compatibility
- Color contrast compliance

## Next Steps
1. Create the `activityFeed.js` component file
2. Update `index.html` with the new structure
3. Test the component with mock data
4. Integrate with the actual `/api/user-activity` endpoint
5. Add comprehensive error handling
6. Document the component for future maintenance