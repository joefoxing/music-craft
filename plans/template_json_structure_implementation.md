# Template JSON Structure and Storage Implementation

## 1. JSON Schema Definition

### Template Object Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Music Generation Template",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique template identifier",
      "pattern": "^template_[a-zA-Z0-9]{3}$"
    },
    "name": {
      "type": "string",
      "description": "Template display name",
      "minLength": 3,
      "maxLength": 50
    },
    "description": {
      "type": "string",
      "description": "Brief description of the template",
      "maxLength": 200
    },
    "category": {
      "type": "string",
      "description": "Primary category ID",
      "enum": ["electronic", "ambient", "cinematic", "hiphop", "rock", "world"]
    },
    "subcategory": {
      "type": "string",
      "description": "Optional subcategory",
      "maxLength": 30
    },
    "prompt": {
      "type": "string",
      "description": "The main prompt text",
      "minLength": 20,
      "maxLength": 500
    },
    "style": {
      "type": "string",
      "description": "Style description or tags",
      "maxLength": 100
    },
    "tags": {
      "type": "array",
      "description": "Searchable tags",
      "items": {
        "type": "string",
        "maxLength": 20
      },
      "minItems": 1,
      "maxItems": 10
    },
    "bpm": {
      "type": "integer",
      "description": "Beats per minute suggestion",
      "minimum": 40,
      "maximum": 220
    },
    "duration": {
      "type": "string",
      "description": "Suggested duration in MM:SS format",
      "pattern": "^[0-5]?[0-9]:[0-5][0-9]$"
    },
    "instrumental": {
      "type": "boolean",
      "description": "Whether the template is instrumental"
    },
    "difficulty": {
      "type": "string",
      "description": "Difficulty level for users",
      "enum": ["beginner", "intermediate", "advanced"]
    },
    "popularity": {
      "type": "integer",
      "description": "Popularity score (0-100)",
      "minimum": 0,
      "maximum": 100
    },
    "author": {
      "type": "string",
      "description": "Template author",
      "default": "System"
    },
    "created_at": {
      "type": "string",
      "description": "Creation date in ISO format",
      "format": "date"
    },
    "updated_at": {
      "type": "string",
      "description": "Last update date in ISO format",
      "format": "date"
    },
    "example_audio_url": {
      "type": "string",
      "description": "URL to example audio",
      "format": "uri"
    },
    "example_image_url": {
      "type": "string",
      "description": "URL to example image",
      "format": "uri"
    },
    "metadata": {
      "type": "object",
      "description": "Additional generation parameters",
      "properties": {
        "model": {
          "type": "string",
          "description": "Recommended model",
          "enum": ["V4", "V3", "V2"]
        },
        "temperature": {
          "type": "number",
          "description": "Creativity parameter",
          "minimum": 0.0,
          "maximum": 1.0
        },
        "top_p": {
          "type": "number",
          "description": "Nucleus sampling parameter",
          "minimum": 0.0,
          "maximum": 1.0
        },
        "presence_penalty": {
          "type": "number",
          "description": "Presence penalty",
          "minimum": -2.0,
          "maximum": 2.0
        },
        "frequency_penalty": {
          "type": "number",
          "description": "Frequency penalty",
          "minimum": -2.0,
          "maximum": 2.0
        }
      }
    }
  },
  "required": ["id", "name", "category", "prompt", "tags"],
  "additionalProperties": false
}
```

### Category Object Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Template Category",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Category identifier"
    },
    "name": {
      "type": "string",
      "description": "Category display name"
    },
    "description": {
      "type": "string",
      "description": "Category description"
    },
    "icon": {
      "type": "string",
      "description": "Material icon name"
    },
    "color": {
      "type": "string",
      "description": "Tailwind color class",
      "enum": ["purple", "blue", "amber", "green", "red", "teal", "indigo", "pink", "cyan"]
    },
    "template_count": {
      "type": "integer",
      "description": "Number of templates in this category"
    }
  },
  "required": ["id", "name", "icon", "color"],
  "additionalProperties": false
}
```

## 2. Storage Structure

### Directory Structure
```
app/
├── static/
│   └── templates/
│       ├── templates.json          # Main template database
│       ├── categories.json         # Category definitions
│       └── images/                 # Template preview images (optional)
└── services/
    └── template_service.py         # Template loading and management
```

### File: `app/static/templates/templates.json`
```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-12",
  "template_count": 21,
  "templates": [
    {
      "id": "template_001",
      "name": "Cyberpunk Synthwave",
      "description": "A cyberpunk synthwave track with pulsating bass and nostalgic 80s atmosphere",
      "category": "electronic",
      "subcategory": "synthwave",
      "prompt": "A cyberpunk synthwave track with pulsating bass, arpeggiated synthesizers, and nostalgic 80s atmosphere. Features driving rhythm, neon-lit cityscape vibes, and emotional melodic hooks.",
      "style": "synthwave, cyberpunk, 80s, retro-futuristic",
      "tags": ["electronic", "synth", "nostalgic", "driving", "atmospheric", "cyberpunk"],
      "bpm": 120,
      "duration": "2:30",
      "instrumental": true,
      "difficulty": "beginner",
      "popularity": 95,
      "author": "System",
      "created_at": "2024-01-01",
      "updated_at": "2024-01-10",
      "example_audio_url": "https://example.com/audio/synthwave-example.mp3",
      "example_image_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=300&fit=crop",
      "metadata": {
        "model": "V4",
        "temperature": 0.8,
        "top_p": 0.95,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1
      }
    },
    // ... 20 more templates
  ]
}
```

### File: `app/static/templates/categories.json`
```json
{
  "categories": [
    {
      "id": "electronic",
      "name": "Electronic",
      "description": "Electronic music styles including synthwave, house, techno, and more",
      "icon": "graphic_eq",
      "color": "purple",
      "template_count": 6
    },
    {
      "id": "ambient",
      "name": "Ambient",
      "description": "Atmospheric and relaxing music for meditation, focus, or sleep",
      "icon": "waves",
      "color": "blue",
      "template_count": 4
    },
    {
      "id": "cinematic",
      "name": "Cinematic",
      "description": "Orchestral and film score music for trailers, games, and media",
      "icon": "movie",
      "color": "amber",
      "template_count": 4
    },
    {
      "id": "hiphop",
      "name": "Hip Hop & Lo-fi",
      "description": "Beat-based music including lo-fi, boom bap, and jazz hop",
      "icon": "headphones",
      "color": "green",
      "template_count": 3
    },
    {
      "id": "rock",
      "name": "Rock & Metal",
      "description": "Guitar-driven music from alternative rock to progressive metal",
      "icon": "music_note",
      "color": "red",
      "template_count": 2
    },
    {
      "id": "world",
      "name": "World & Ethnic",
      "description": "Cultural and traditional music from around the world",
      "icon": "public",
      "color": "teal",
      "template_count": 2
    }
  ]
}
```

## 3. Backend Service Implementation

### File: `app/services/template_service.py`
```python
"""
Template service for loading and managing music generation templates.
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for managing template data."""
    
    def __init__(self, templates_path: str = None, categories_path: str = None):
        """Initialize template service with file paths."""
        self.templates_path = templates_path or os.path.join(
            os.path.dirname(__file__), '..', 'static', 'templates', 'templates.json'
        )
        self.categories_path = categories_path or os.path.join(
            os.path.dirname(__file__), '..', 'static', 'templates', 'categories.json'
        )
        self._templates = None
        self._categories = None
        self._last_loaded = None
        
    def load_templates(self) -> Dict[str, Any]:
        """Load templates from JSON file."""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._templates = data
            self._last_loaded = datetime.now()
            logger.info(f"Loaded {data.get('template_count', 0)} templates")
            return data
        except FileNotFoundError:
            logger.error(f"Templates file not found: {self.templates_path}")
            return {"version": "1.0.0", "template_count": 0, "templates": []}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing templates JSON: {e}")
            return {"version": "1.0.0", "template_count": 0, "templates": []}
    
    def load_categories(self) -> Dict[str, Any]:
        """Load categories from JSON file."""
        try:
            with open(self.categories_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._categories = data
            return data
        except FileNotFoundError:
            logger.error(f"Categories file not found: {self.categories_path}")
            return {"categories": []}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing categories JSON: {e}")
            return {"categories": []}
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates."""
        if self._templates is None:
            self.load_templates()
        return self._templates.get('templates', []) if self._templates else []
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        templates = self.get_all_templates()
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None
    
    def get_templates_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Get templates filtered by category."""
        templates = self.get_all_templates()
        return [t for t in templates if t.get('category') == category_id]
    
    def search_templates(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search templates by name, description, or tags."""
        templates = self.get_all_templates()
        query_lower = query.lower()
        
        results = []
        for template in templates:
            # Skip if category doesn't match
            if category and template.get('category') != category:
                continue
            
            # Search in name, description, and tags
            if (query_lower in template.get('name', '').lower() or
                query_lower in template.get('description', '').lower() or
                any(query_lower in tag.lower() for tag in template.get('tags', []))):
                results.append(template)
        
        return results
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        if self._categories is None:
            self.load_categories()
        return self._categories.get('categories', []) if self._categories else []
    
    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific category by ID."""
        categories = self.get_all_categories()
        for category in categories:
            if category.get('id') == category_id:
                return category
        return None
    
    def get_popular_templates(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get most popular templates."""
        templates = self.get_all_templates()
        # Sort by popularity (descending) and limit results
        sorted_templates = sorted(templates, key=lambda x: x.get('popularity', 0), reverse=True)
        return sorted_templates[:limit]
    
    def get_recent_templates(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get recently added/updated templates."""
        templates = self.get_all_templates()
        # Sort by updated_at (descending) and limit results
        sorted_templates = sorted(
            templates, 
            key=lambda x: x.get('updated_at', x.get('created_at', '2000-01-01')),
            reverse=True
        )
        return sorted_templates[:limit]
    
    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """Validate a template object against schema."""
        errors = []
        
        # Required fields
        required_fields = ['id', 'name', 'category', 'prompt', 'tags']
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # ID format
        if 'id' in template and not template['id'].startswith('template_'):
            errors.append("Template ID must start with 'template_'")
        
        # Prompt length
        if 'prompt' in template:
            prompt = template['prompt']
            if len(prompt) < 20:
                errors.append("Prompt must be at least 20 characters")
            if len(prompt) > 500:
                errors.append("Prompt must not exceed 500 characters")
        
        # Tags validation
        if 'tags' in template:
            tags = template['tags']
            if not isinstance(tags, list):
                errors.append("Tags must be a list")
            elif len(tags) == 0:
                errors.append("At least one tag is required")
            elif len(tags) > 10:
                errors.append("Maximum 10 tags allowed")
        
        return errors

# Singleton instance for easy import
template_service = TemplateService()
```
## 4. API Endpoint Implementation

### File: `app/routes/template_routes.py`
```python
"""
Template API routes for the music generation application.
"""
from flask import Blueprint, jsonify, request
from app.services.template_service import template_service
import logging

logger = logging.getLogger(__name__)

template_bp = Blueprint('template', __name__, url_prefix='/api/templates')

@template_bp.route('/', methods=['GET'])
def get_templates():
    """Get all templates with optional filtering."""
    try:
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        limit = request.args.get('limit', type=int)
        sort_by = request.args.get('sort_by', 'popularity')  # popularity, recent, name
        
        # Get templates based on filters
        if search:
            templates = template_service.search_templates(search, category)
        elif category:
            templates = template_service.get_templates_by_category(category)
        else:
            templates = template_service.get_all_templates()
        
        # Apply sorting
        if sort_by == 'popularity':
            templates.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        elif sort_by == 'recent':
            templates.sort(key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True)
        elif sort_by == 'name':
            templates.sort(key=lambda x: x.get('name', '').lower())
        
        # Apply limit if specified
        if limit and limit > 0:
            templates = templates[:limit]
        
        # Get categories for the response
        categories = template_service.get_all_categories()
        
        return jsonify({
            'success': True,
            'templates': templates,
            'categories': categories,
            'count': len(templates),
            'total': template_service.get_all_templates().__len__()
        })
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load templates',
            'message': str(e)
        }), 500

@template_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific template by ID."""
    try:
        template = template_service.get_template_by_id(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load template',
            'message': str(e)
        }), 500

@template_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all template categories."""
    try:
        categories = template_service.get_all_categories()
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories)
        })
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load categories',
            'message': str(e)
        }), 500

@template_bp.route('/popular', methods=['GET'])
def get_popular_templates():
    """Get popular templates."""
    try:
        limit = request.args.get('limit', 6, type=int)
        templates = template_service.get_popular_templates(limit)
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting popular templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load popular templates',
            'message': str(e)
        }), 500

@template_bp.route('/recent', methods=['GET'])
def get_recent_templates():
    """Get recently added templates."""
    try:
        limit = request.args.get('limit', 6, type=int)
        templates = template_service.get_recent_templates(limit)
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load recent templates',
            'message': str(e)
        }), 500

@template_bp.route('/apply', methods=['POST'])
def apply_template():
    """Apply a template to the current session."""
    try:
        data = request.get_json()
        template_id = data.get('template_id')
        
        if not template_id:
            return jsonify({
                'success': False,
                'error': 'Template ID is required'
            }), 400
        
        template = template_service.get_template_by_id(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        # Return the template data for frontend to apply
        return jsonify({
            'success': True,
            'template': template,
            'prompt': template.get('prompt'),
            'style': template.get('style', ''),
            'instrumental': template.get('instrumental', True),
            'metadata': template.get('metadata', {})
        })
        
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply template',
            'message': str(e)
        }), 500
```

### File: `app/__init__.py` (add template blueprint)
```python
# Add to existing imports
from app.routes.template_routes import template_bp

# Add to create_app function after other blueprint registrations
app.register_blueprint(template_bp)
```

## 5. Implementation Steps

### Step 1: Create Directory Structure
```bash
mkdir -p app/static/templates
mkdir -p app/services
```

### Step 2: Create Template JSON Files
1. Create `app/static/templates/templates.json` with 21 template objects
2. Create `app/static/templates/categories.json` with 6 category objects

### Step 3: Implement Template Service
1. Create `app/services/template_service.py` with the TemplateService class
2. Add proper error handling and logging

### Step 4: Implement API Routes
1. Create `app/routes/template_routes.py` with all endpoint handlers
2. Register the blueprint in `app/__init__.py`

### Step 5: Test the API
1. Test `/api/templates` endpoint with various filters
2. Test `/api/templates/template_001` for specific template
3. Test `/api/templates/categories` for category list
4. Test `/api/templates/apply` with POST request

### Step 6: Validation and Error Handling
1. Add input validation for all endpoints
2. Implement proper error responses
3. Add request logging for debugging

## 6. Testing Strategy

### Unit Tests
```python
# test_template_service.py
def test_load_templates():
    service = TemplateService()
    templates = service.get_all_templates()
    assert len(templates) == 21
    
def test_get_template_by_id():
    service = TemplateService()
    template = service.get_template_by_id('template_001')
    assert template['name'] == 'Cyberpunk Synthwave'
    
def test_search_templates():
    service = TemplateService()
    results = service.search_templates('synthwave')
    assert len(results) > 0
```

### Integration Tests
```python
# test_template_routes.py
def test_get_templates_endpoint(client):
    response = client.get('/api/templates')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'templates' in data
    
def test_apply_template_endpoint(client):
    response = client.post('/api/templates/apply',
                          json={'template_id': 'template_001'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'prompt' in data
```

## 7. Performance Considerations

### Caching Strategy
- Cache template data in memory with 5-minute TTL
- Use Flask-Caching for API responses
- Implement ETag headers for client-side caching

### Optimization Tips
- Lazy load template data on first request
- Compress JSON responses with gzip
- Implement pagination for large template collections
- Use database indexing if migrating to SQL storage

## 8. Security Considerations

### Input Validation
- Validate all template IDs against expected format
- Sanitize search queries to prevent injection
- Limit request size for template application

### Rate Limiting
- Implement rate limiting on template API endpoints
- Use Flask-Limiter for easy configuration
- Set appropriate limits based on endpoint sensitivity

### Data Protection
- Ensure template JSON files are not writable by web server
- Validate template data on load to prevent malformed data
- Implement backup strategy for template files

## 9. Monitoring and Maintenance

### Logging
- Log template loading events
- Track template application usage
- Monitor API response times

### Health Checks
- Add health check endpoint for template service
- Monitor template file modification dates
- Alert on template loading failures

### Update Strategy
- Version template JSON files
- Implement template migration scripts
- Provide backward compatibility for template IDs

## 10. Success Metrics
- Template API response time < 200ms
- Template loading success rate > 99.9%
- Template application success rate > 95%
- User engagement with template features
- Reduction in failed generations due to poor prompts
        
