# Template Extension for AI Music Generation

## Overview
This document describes how to extend the existing template system to support AI music generation capabilities. The extension maintains backward compatibility while adding new AI-specific parameters and functionality.

## Current Template Structure

### Existing Template Schema (from templates_complete.json)
```json
{
  "id": "template_001",
  "name": "Cyberpunk Synthwave",
  "description": "A cyberpunk synthwave track...",
  "category": "electronic",
  "subcategory": "synthwave",
  "prompt": "A cyberpunk synthwave track with...",
  "style": "synthwave, cyberpunk, 80s, retro-futuristic...",
  "tags": ["electronic", "synth", "cyberpunk", "80s", "nostalgic"],
  "bpm": 120,
  "duration": "3:15",
  "instrumental": true,
  "difficulty": "beginner",
  "popularity": 95,
  "author": "System",
  "created_at": "2024-01-12",
  "updated_at": "2024-01-12",
  "example_image_url": "https://...",
  "metadata": {
    "model": "V4",
    "temperature": 0.8,
    "top_p": 0.95,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1
  }
}
```

## Extended Template Schema for AI Music Generation

### New Template Type Field
```json
{
  "template_type": "ai_generation",  // New field: "ai_generation", "cover_generation", or "hybrid"
  // ... existing fields ...
}
```

### Complete Extended Schema
```json
{
  // Core Identification
  "id": "ai_template_001",
  "name": "AI Synthwave Generator",
  "description": "Generates original synthwave tracks with AI",
  "template_type": "ai_generation",
  
  // Categorization (existing)
  "category": "electronic",
  "subcategory": "synthwave",
  "tags": ["ai_generated", "electronic", "synthwave", "royalty_free"],
  
  // AI Generation Parameters (new)
  "ai_parameters": {
    "model": "kie_v4",
    "temperature": 0.7,
    "creativity": 0.8,
    "coherence": 0.9,
    "genre_adherence": 0.95,
    "structure_preservation": 0.85,
    "lyric_quality": 0.8,
    "vocal_realism": 0.75
  },
  
  // Musical Constraints (extended)
  "musical_constraints": {
    "bpm_range": [110, 130],
    "key_options": ["C_major", "A_minor", "E_minor", "G_major"],
    "duration_range": [120, 300],  // seconds
    "instrumentation": {
      "required": ["synth_bass", "drum_machine"],
      "recommended": ["arpeggiator", "pad", "lead_synth"],
      "optional": ["guitar", "vocals", "fx"]
    },
    "structure": {
      "type": "verse_chorus",
      "has_intro": true,
      "has_outro": true,
      "min_sections": 3,
      "max_sections": 6
    },
    "harmonic_complexity": "medium",
    "texture_density": "medium",
    "dynamic_range": "medium"
  },
  
  // Lyric Generation Settings (new)
  "lyric_settings": {
    "enabled": true,
    "default_theme": "cyberpunk_future",
    "theme_options": ["cyberpunk", "nostalgia", "digital_love", "urban_night"],
    "language": "en",
    "style": "poetic_tech",
    "vocal_characteristics": {
      "gender": "neutral",
      "age": "ageless",
      "tone": "digital",
      "style": "synth_pop"
    }
  },
  
  // Quality Settings (new)
  "quality_settings": {
    "audio_quality": "high",
    "sample_rate": 44100,
    "bit_depth": 24,
    "mastering_preset": "radio_ready",
    "output_formats": ["wav", "mp3", "midi"],
    "include_stems": false,
    "include_metadata": true
  },
  
  // Generation Prompts (extended)
  "prompts": {
    "main": "Generate an original synthwave track with pulsating basslines and nostalgic 80s atmosphere",
    "style_guidance": "Cyberpunk aesthetic, neon-lit cityscape, emotional melodic hooks",
    "instrumentation_guidance": "Use analog-style synthesizers, sequenced arpeggios, gated reverb drums",
    "structure_guidance": "Build from atmospheric intro to driving chorus, include breakdown section",
    "lyric_guidance": "Themes of human connection in digital world, melancholic futurism"
  },
  
  // Examples & References (extended)
  "examples": {
    "audio_references": [
      "https://example.com/synthwave_ref1.mp3",
      "https://example.com/synthwave_ref2.mp3"
    ],
    "mood_board": [
      "https://images.unsplash.com/neon-city.jpg",
      "https://images.unsplash.com/retro-tech.jpg"
    ],
    "similar_artists": ["The Midnight", "FM-84", "Timecop1983", "Gunship"]
  },
  
  // Metadata & Management (existing + extended)
  "author": "AI_System",
  "created_at": "2024-01-12",
  "updated_at": "2024-01-12",
  "version": "1.0",
  "compatibility": ["kie_v4", "suno_v3"],
  "popularity": 92,
  "difficulty": "beginner",
  "instrumental": false,
  
  // Usage Statistics (new)
  "usage_stats": {
    "generation_count": 150,
    "average_rating": 4.7,
    "success_rate": 0.95,
    "common_customizations": {
      "tempo": [115, 125],
      "key": ["C_minor", "D_minor"],
      "duration": [180, 240]
    }
  }
}
```

## Template Service Extension

### New TemplateService Methods

```python
class AITemplateService(TemplateService):
    """Extended template service for AI music generation."""
    
    def get_ai_templates(self) -> List[Dict[str, Any]]:
        """Get all AI generation templates."""
        templates = self.load_templates()
        return [t for t in templates if t.get('template_type') == 'ai_generation']
    
    def get_templates_by_ai_model(self, model: str) -> List[Dict[str, Any]]:
        """Get templates compatible with specific AI model."""
        templates = self.load_templates()
        return [
            t for t in templates 
            if t.get('template_type') == 'ai_generation' 
            and model in t.get('compatibility', [])
        ]
    
    def generate_from_template(self, template_id: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate music using a template with customizations."""
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Merge template defaults with customizations
        generation_params = self._merge_template_with_customizations(template, customizations)
        
        # Validate parameters
        self._validate_generation_parameters(generation_params)
        
        # Generate music using AI service
        return self._call_ai_generation_service(generation_params)
    
    def create_ai_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new AI generation template."""
        # Validate template structure
        self._validate_ai_template_structure(template_data)
        
        # Generate unique ID
        template_id = f"ai_template_{len(self.get_ai_templates()) + 1:03d}"
        template_data['id'] = template_id
        
        # Add to templates
        templates = self.load_templates()
        templates.append(template_data)
        self._save_templates(templates)
        
        return template_id
    
    def _merge_template_with_customizations(self, template: Dict[str, Any], 
                                          customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Merge template defaults with user customizations."""
        result = template.copy()
        
        # Apply customizations to appropriate sections
        if 'ai_parameters' in customizations:
            result['ai_parameters'].update(customizations['ai_parameters'])
        
        if 'musical_constraints' in customizations:
            result['musical_constraints'].update(customizations['musical_constraints'])
        
        if 'lyric_settings' in customizations:
            result['lyric_settings'].update(customizations['lyric_settings'])
        
        # Handle direct parameter overrides
        for key in ['tempo', 'key', 'duration', 'instrumental']:
            if key in customizations:
                result[key] = customizations[key]
        
        return result
```

## Template Categories for AI Generation

### 1. Genre-Specific Templates
```json
{
  "category": "genre_templates",
  "subcategories": [
    "electronic_templates",
    "rock_templates", 
    "jazz_templates",
    "classical_templates",
    "world_templates"
  ]
}
```

### 2. Mood/Emotion Templates
```json
{
  "category": "mood_templates",
  "subcategories": [
    "happy_upbeat",
    "sad_melancholic",
    "energetic_driving",
    "calm_relaxing",
    "mysterious_suspenseful"
  ]
}
```

### 3. Use Case Templates
```json
{
  "category": "use_case_templates",
  "subcategories": [
    "background_music",
    "film_scoring",
    "video_game_music",
    "meditation_ambient",
    "podcast_intro",
    "commercial_jingle"
  ]
}
```

### 4. Style/Period Templates
```json
{
  "category": "style_templates",
  "subcategories": [
    "retro_80s",
    "futuristic_cyberpunk",
    "vintage_jazz",
    "modern_pop",
    "experimental_avantgarde"
  ]
}
```

## Template Validation Rules

### 1. Required Fields for AI Templates
```python
REQUIRED_AI_TEMPLATE_FIELDS = [
    'id', 'name', 'template_type', 'category',
    'ai_parameters', 'musical_constraints'
]

REQUIRED_AI_PARAMETERS = [
    'model', 'temperature', 'creativity', 'coherence'
]

REQUIRED_MUSICAL_CONSTRAINTS = [
    'bpm_range', 'key_options', 'duration_range'
]
```

### 2. Value Validation
```python
def validate_ai_template(template: Dict[str, Any]) -> List[str]:
    """Validate AI template structure and values."""
    errors = []
    
    # Check required fields
    for field in REQUIRED_AI_TEMPLATE_FIELDS:
        if field not in template:
            errors.append(f"Missing required field: {field}")
    
    # Validate AI parameters
    if 'ai_parameters' in template:
        ai_params = template['ai_parameters']
        for param in REQUIRED_AI_PARAMETERS:
            if param not in ai_params:
                errors.append(f"Missing AI parameter: {param}")
        
        # Validate ranges
        if 'temperature' in ai_params:
            temp = ai_params['temperature']
            if not 0.0 <= temp <= 1.0:
                errors.append(f"Temperature must be between 0.0 and 1.0, got {temp}")
    
    # Validate musical constraints
    if 'musical_constraints' in template:
        constraints = template['musical_constraints']
        
        # BPM range validation
        if 'bpm_range' in constraints:
            bpm_min, bpm_max = constraints['bpm_range']
            if not (40 <= bpm_min <= bpm_max <= 240):
                errors.append(f"Invalid BPM range: {bpm_min}-{bpm_max}")
        
        # Duration range validation
        if 'duration_range' in constraints:
            dur_min, dur_max = constraints['duration_range']
            if not (30 <= dur_min <= dur_max <= 600):
                errors.append(f"Invalid duration range: {dur_min}-{dur_max}s")
    
    return errors
```

## Template Generation Examples

### Example 1: Basic AI Template Creation
```python
basic_ai_template = {
    "id": "ai_basic_001",
    "name": "Basic Electronic Generator",
    "template_type": "ai_generation",
    "category": "electronic",
    "subcategory": "general",
    "ai_parameters": {
        "model": "kie_v4",
        "temperature": 0.7,
        "creativity": 0.8,
        "coherence": 0.9
    },
    "musical_constraints": {
        "bpm_range": [100, 140],
        "key_options": ["C_major", "G_major", "D_minor", "A_minor"],
        "duration_range": [120, 240],
        "instrumentation": {
            "required": ["drum_machine", "bass"],
            "recommended": ["synth", "pad"]
        }
    }
}
```

### Example 2: Advanced Lyric Template
```python
lyric_template = {
    "id": "ai_lyric_001",
    "name": "Pop Song with AI Lyrics",
    "template_type": "ai_generation",
    "category": "pop",
    "subcategory": "contemporary",
    
    "ai_parameters": {
        "model": "suno_v3",
        "temperature": 0.6,
        "creativity": 0.7,
        "coherence": 0.95,
        "lyric_quality": 0.85,
        "vocal_realism": 0.8
    },
    
    "musical_constraints": {
        "bpm_range": [110, 130],
        "key_options": ["C_major", "F_major", "G_major", "A_minor"],
        "duration_range": [180, 240],
        "structure": {
            "type": "verse_chorus",
            "has_intro": true,
            "has_bridge": true,
            "has_outro": true
        }
    },
    
    "lyric_settings": {
        "enabled": true,
        "default_theme": "modern_love",
        "theme_options": ["love", "relationships", "self_empowerment", "city_life"],
        "language": "en",
        "style": "contemporary_pop",
        "vocal_characteristics": {
            "gender": "female",
            "age": "young_adult",
            "tone": "bright",
            "style": "pop"
        }
    },
    
    "prompts": {
        "main": "Generate a contemporary pop song with catchy hooks and relatable lyrics",
        "lyric_guidance": "Focus on modern relationships, emotional authenticity, and memorable choruses"
    }
}
```

## Migration Strategy

### 1. Backward Compatibility
```python
def migrate_existing_template(existing_template: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate existing template to AI-compatible format."""
    migrated = existing_template.copy()
    
    # Add template_type if missing
    if 'template_type' not in migrated:
        migrated['template_type'] = 'cover_generation'
    
    # Convert existing metadata to ai_parameters
    if 'metadata' in migrated:
        metadata = migrated.pop('metadata')
        migrated['ai_parameters'] = {
            'model': metadata.get('model', 'V4'),
            'temperature': metadata.get('temperature', 0.8),
            'creativity': 0.7,  # Default
            'coherence': 0.8    # Default
        }
    
    # Add musical_constraints from existing fields
    migrated['musical_constraints'] = {
        'bpm_range': [migrated.get('bpm', 120) - 10, migrated.get('bpm', 120) + 10],
        'key_options': ['C_major', 'G_major', 'A_minor'],  # Defaults
        'duration_range': [120, 300]  # Default range
    }
    
    return migrated
```

### 2. Dual-Mode Support
```python
class HybridTemplateService:
    """Supports both cover generation and AI generation templates."""
    
    def get_template(self, template_id: str, generation_type: str = None) -> Dict[str, Any]:
        """Get template with optional type filtering."""
        template = self.template_service.get_template_by_id(template_id)
        
        if generation_type:
            template_type = template.get('template_type', 'cover_generation')
            if template_type != generation_type:
                raise ValueError(f"Template {template_id} is type {template_type}, not {generation_type}")
        
        return template
    
    def generate_music(self, template_id: str, **kwargs) -> Dict[str, Any]:
        """Generate music using appropriate method based on template type."""
        template = self.get_template(template_id)
        template_type = template.get('template_type', 'cover_generation')
        
        if template_type == 'ai_generation':
            return self._generate_ai_music(template, **kwargs)
        else:
            return self._generate_cover_music(template, **kwargs)
```

## Template Management Interface

### 1. Template Creation UI
```json
{
  "ui_sections": [
    {
      "name": "Basic Information",
