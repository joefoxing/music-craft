# Template Library System Design

## Overview
The Template Library provides curated prompt templates for the music generation system, making it easier for users to create high-quality music by providing pre-designed prompts with proven results.

## System Architecture

### 1. Template Data Structure

**JSON Template Format:**
```json
{
  "templates": [
    {
      "id": "template_001",
      "name": "Cyberpunk Synthwave",
      "category": "electronic",
      "subcategory": "synthwave",
      "prompt": "A cyberpunk synthwave track with pulsating bass, arpeggiated synthesizers, and nostalgic 80s atmosphere. Features driving rhythm, neon-lit cityscape vibes, and emotional melodic hooks.",
      "style": "synthwave, cyberpunk, 80s, retro-futuristic",
      "tags": ["electronic", "synth", "nostalgic", "driving", "atmospheric"],
      "bpm": 120,
      "duration": "2:30",
      "instrumental": true,
      "difficulty": "beginner",
      "popularity": 95,
      "author": "System",
      "created_at": "2024-01-01",
      "example_audio_url": "https://...",
      "example_image_url": "https://...",
      "metadata": {
        "model": "V4",
        "temperature": 0.8,
        "top_p": 0.95,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1
      }
    }
  ],
  "categories": [
    {
      "id": "electronic",
      "name": "Electronic",
      "description": "Electronic music styles",
      "icon": "graphic_eq",
      "color": "purple"
    },
    {
      "id": "ambient",
      "name": "Ambient",
      "description": "Atmospheric and relaxing music",
      "icon": "waves",
      "color": "blue"
    },
    {
      "id": "cinematic",
      "name": "Cinematic",
      "description": "Orchestral and film score music",
      "icon": "movie",
      "color": "amber"
    },
    {
      "id": "hiphop",
      "name": "Hip Hop & Lo-fi",
      "description": "Beat-based and relaxed styles",
      "icon": "headphones",
      "color": "green"
    },
    {
      "id": "rock",
      "name": "Rock & Metal",
      "description": "Guitar-driven music",
      "icon": "music_note",
      "color": "red"
    },
    {
      "id": "world",
      "name": "World & Ethnic",
      "description": "Cultural and traditional music",
      "icon": "public",
      "color": "teal"
    }
  ]
}
```

### 2. Storage Strategy

**Option 1: JSON File Storage**
- Location: `app/static/templates/templates.json`
- Simple, no database required
- Easy to version control
- Suitable for 20-100 templates

**Option 2: Database Storage**
- Add `Template` model to `app/models.py`
- Store templates in SQLite database
- More scalable for future expansion
- Allows user-created templates

**Recommendation for Phase 1:** Use JSON file storage for simplicity.

### 3. Backend API Endpoints

**GET /api/templates**
- Returns all templates with optional filtering
- Query parameters: `category`, `difficulty`, `search`
- Response: `{ "success": true, "templates": [...], "categories": [...] }`

**GET /api/templates/{id}**
- Returns a specific template by ID
- Response: `{ "success": true, "template": {...} }`

**POST /api/templates/apply**
- Applies a template to the current session
- Body: `{ "template_id": "template_001", "user_id": "optional" }`
- Response: `{ "success": true, "prompt": "...", "style": "...", "instrumental": true }`

### 4. Frontend Component Design

**Template Gallery Component:**
Location: `app/static/js/components/templateGallery.js`

**Features:**
- Grid display of template cards
- Category filtering
- Search functionality
- Preview modal with example audio
- One-click application to prompt input

**Template Card Design:**
```html
<div class="template-card" data-template-id="template_001">
  <div class="template-image">
    <img src="example_image_url" alt="Template preview">
    <div class="template-category-badge">Electronic</div>
  </div>
  <div class="template-content">
    <h4 class="template-title">Cyberpunk Synthwave</h4>
    <p class="template-description">A cyberpunk synthwave track with pulsating bass...</p>
    <div class="template-tags">
      <span class="tag">synthwave</span>
      <span class="tag">cyberpunk</span>
      <span class="tag">80s</span>
    </div>
    <div class="template-meta">
      <span class="meta-item">120 BPM</span>
      <span class="meta-item">2:30</span>
      <span class="meta-item">★ 95</span>
    </div>
    <button class="apply-template-btn">Use Template</button>
  </div>
</div>
```

### 5. Integration with Existing UI

**Location in index.html:**
Add template gallery below the "Quick Tags" section (line 213-220):

```html
<!-- Template Library -->
<section class="flex flex-col gap-4 mt-8">
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-xl font-bold dark:text-white text-slate-900">Template Library</h3>
      <p class="text-sm text-slate-500 dark:text-slate-400">Start with curated prompts for better results</p>
    </div>
    <div class="flex items-center gap-3">
      <!-- Category filter -->
      <select id="templateCategoryFilter" class="bg-surface-dark text-white text-sm rounded-lg px-3 py-1.5 border border-border-dark">
        <option value="all">All Categories</option>
        <option value="electronic">Electronic</option>
        <option value="ambient">Ambient</option>
        <option value="cinematic">Cinematic</option>
        <option value="hiphop">Hip Hop & Lo-fi</option>
        <option value="rock">Rock & Metal</option>
        <option value="world">World & Ethnic</option>
      </select>
      <!-- Search input -->
      <div class="relative">
        <input type="text" id="templateSearch" placeholder="Search templates..." class="bg-surface-dark text-white text-sm rounded-lg pl-10 pr-3 py-1.5 border border-border-dark w-48">
        <span class="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">search</span>
      </div>
    </div>
  </div>
  
  <!-- Loading state -->
  <div id="templateLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <!-- Skeleton cards -->
  </div>
  
  <!-- Empty state -->
  <div id="templateEmpty" class="hidden text-center py-12">
    <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">description</span>
    <p class="text-slate-500 dark:text-slate-400">No templates found.</p>
    <p class="text-sm text-slate-400 mt-1">Try a different search or category.</p>
  </div>
  
  <!-- Template cards container -->
  <div id="templateCards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <!-- Template cards will be dynamically inserted here -->
  </div>
  
  <!-- View more button (for pagination) -->
  <div id="templatePagination" class="hidden text-center mt-6">
    <button id="loadMoreTemplates" class="px-6 py-2 bg-surface-dark hover:bg-opacity-80 text-white text-sm font-medium rounded-lg border border-border-dark">
      Load More Templates
    </button>
  </div>
</section>
```

### 6. Template Application Flow

1. User clicks "Use Template" on a template card
2. JavaScript fetches template details from `/api/templates/{id}`
3. Template prompt, style, and settings are applied to the form:
   - Set `promptInput.value` to template prompt
   - Set `styleInput.value` to template style
   - Set `instrumentalToggle.checked` to template instrumental value
   - Update character counters
4. Show success notification: "Template applied! Ready to generate."
5. Optionally highlight the applied template in the gallery

### 7. Initial Template Collection (20+ Templates)

**Electronic (6 templates):**
1. Cyberpunk Synthwave
2. Lo-fi Study Beats
3. Deep House Groove
4. Drum & Bass Energy
5. Ambient Techno
6. Future Bass Drop

**Ambient (4 templates):**
7. Calm Meditation
8. Space Exploration
9. Rainy Day Piano
10. Forest Atmosphere

**Cinematic (4 templates):**
11. Epic Trailer Music
12. Emotional Piano Score
13. Suspense Thriller
14. Fantasy Adventure

**Hip Hop & Lo-fi (3 templates):**
15. Boom Bap Beat
16. Jazz Hop Loop
17. Chill Lo-fi

**Rock & Metal (2 templates):**
18. Alternative Rock Anthem
19. Progressive Metal Riff

**World & Ethnic (2 templates):**
20. Traditional Japanese
21. African Drum Circle

### 8. Implementation Steps

**Phase 1A: Backend Setup**
1. Create template JSON structure
2. Implement `/api/templates` endpoint
3. Create template service for loading templates

**Phase 1B: Frontend Component**
1. Create `TemplateGallery` JavaScript component
2. Add template gallery HTML to index.html
3. Implement template filtering and search
4. Add template application functionality

**Phase 1C: Template Creation**
1. Create 20+ curated templates in JSON format
2. Add example images/audio where available
3. Test template application flow

**Phase 1D: Integration & Testing**
1. Test end-to-end template application
2. Ensure responsive design
3. Test with different screen sizes
4. Validate accessibility

### 9. Future Enhancements

**Phase 2 (Post-v1.0):**
- User-created templates
- Template ratings and reviews
- Template collections/playlists
- AI-powered template suggestions
- Template versioning
- Template import/export

**Phase 3:**
- Collaborative template editing
- Template marketplace
- Advanced template variables
- Template A/B testing
- Integration with external prompt libraries

### 10. Technical Considerations

**Performance:**
- Lazy load template images
- Implement client-side caching
- Use virtual scrolling for large template collections
- Compress template JSON

**Security:**
- Sanitize template content
- Validate template JSON structure
- Rate limit template API calls
- Prevent XSS in user-generated templates (future)

**Accessibility:**
- Keyboard navigation for template gallery
- Screen reader support
- Proper ARIA labels
- Color contrast compliance

## Success Metrics
- Increased prompt quality (measured by generation success rate)
- Reduced time to first generation
- Higher user engagement with template features
- Positive user feedback on template usefulness