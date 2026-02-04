# AI Music Generation Usage Guide

## Overview
The new AI music generation feature integrates Kie API's AI capabilities into the Lyric Cover system. This guide explains how to use the feature programmatically and through the application.

## Quick Start

### 1. Using EnhancedKieAPIClient Directly

```python
from app.kie_client import EnhancedKieAPIClient

# Initialize client (will use mock mode if no API key is configured)
client = EnhancedKieAPIClient()

# Define generation parameters
parameters = {
    'genre': 'electronic',
    'subgenre': 'synthwave',
    'mood': 'nostalgic',
    'duration': 180,  # seconds
    'title': 'My AI Track',
    'prompt': 'A nostalgic synthwave track with atmospheric pads',
    'audio_quality': 'medium',  # low, medium, high
    'complexity': 'simple',  # simple or complex
    'lyrics': {
        'enabled': False
    },
    'ai_parameters': {
        'genre_adherence': 0.9,  # 0.0 to 1.0
        'creativity': 0.7,       # 0.0 to 1.0
        'coherence': 0.8         # 0.0 to 1.0
    }
}

# Generate AI music
response = client.generate_ai_music(parameters)
print(f"Generation ID: {response['generation_id']}")
print(f"Task ID: {response['task_id']}")
print(f"Status: {response['status']}")
print(f"Estimated completion: {response['estimated_completion']} seconds")
```

### 2. Using AITemplateService (Within Flask App Context)

```python
from app.services.ai_template_service import AITemplateService

# Initialize service (requires Flask app context)
service = AITemplateService()

# Get all AI templates
templates = service.get_all_ai_templates()

# Generate using a specific template
template_id = 'ai_synthwave_001'
user_parameters = {
    'duration': 150,
    'title': 'Custom Track Name'
}

# Generate Kie parameters
kie_params = service.generate_kie_parameters(template_id, user_parameters)

# Use with EnhancedKieAPIClient
from app.kie_client import EnhancedKieAPIClient
client = EnhancedKieAPIClient()

# Note: The actual API call would need to be adapted since generate_kie_parameters
# returns parameters for the Kie API, not a direct generation call
```

## API Endpoints

### New AI Generation Endpoint (to be implemented in routes)
```python
# Example route that would need to be added to app/routes/api.py
@app.route('/api/generate/ai', methods=['POST'])
def generate_ai_music():
    """Generate AI music from parameters."""
    data = request.get_json()
    
    # Validate parameters
    from app.services.ai_template_service import AITemplateService
    service = AITemplateService()
    is_valid, error = service.validate_ai_parameters(data)
    
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Generate music
    from app.kie_client import EnhancedKieAPIClient
    client = EnhancedKieAPIClient()
    
    try:
        response = client.generate_ai_music(data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Parameter Reference

### Required Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `genre` | string | Primary music genre | `'electronic'`, `'rock'`, `'pop'` |
| `duration` | integer | Track duration in seconds | `180` (3 minutes) |

### Optional Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `subgenre` | string | Music subgenre | `None` |
| `mood` | string | Emotional mood | `None` |
| `title` | string | Track title | `'AI Generated Track'` |
| `prompt` | string | Generation prompt | `''` |
| `audio_quality` | string | Quality level: `low`, `medium`, `high` | `'medium'` |
| `complexity` | string | Complexity: `simple`, `complex` | `'simple'` |
| `primary_instruments` | list | List of instruments | `[]` |

### Lyrics Parameters (if `lyrics.enabled = True`)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `lyrics.enabled` | boolean | Enable lyrics generation | `False` |
| `lyrics.theme` | string | Lyric theme | `'love'` |
| `lyrics.style` | string | Lyric style | `'poetic'` |
| `lyrics.language` | string | 2-letter language code | `'en'` |
| `lyrics.vocal_characteristics.gender` | string | Vocal gender: `'male'`, `'female'` | `'f'` |

### AI Parameters
| Parameter | Type | Range | Description | Default |
|-----------|------|-------|-------------|---------|
| `ai_parameters.genre_adherence` | float | 0.0-1.0 | How closely to follow genre | `0.9` |
| `ai_parameters.creativity` | float | 0.0-1.0 | Creativity level | `0.7` |
| `ai_parameters.coherence` | float | 0.0-1.0 | Musical coherence | `0.8` |

## Configuration

### Environment Variables
Add to your `.env` file:
```bash
# Kie API Configuration
KIE_API_KEY=your_kie_api_key_here
KIE_API_BASE_URL=https://api.kie.ai
USE_MOCK=false  # Set to true for testing without API key

# Callback Configuration (for production)
BASE_URL=http://your-domain.com
NGROK_URL=http://your-ngrok-url.ngrok.io  # For local development with callbacks
```

### Mock Mode
When `USE_MOCK=true` or no `KIE_API_KEY` is provided:
- All API calls return mock responses
- No actual API calls are made
- Useful for testing and development
- Generation times are simulated

## Testing the Feature

### 1. Run the Integration Test
```bash
python test_kie_integration.py
```

### 2. Manual Testing in Python Console
```python
# Test parameter mapping
from app.core.parameter_mapping import ParameterMapper

params = {
    'genre': 'rock',
    'subgenre': 'alternative',
    'mood': 'energetic',
    'duration': 150
}

kie_params = ParameterMapper.convert_to_kie_parameters(params)
print(kie_params)

# Test AI generation with mock mode
from app.kie_client import EnhancedKieAPIClient
client = EnhancedKieAPIClient()  # Will use mock mode
response = client.generate_ai_music(params)
print(response)
```

## Integration with Existing System

### Backward Compatibility
- Existing audio upload and cover generation continues to work unchanged
- AI generation is an additional feature, not a replacement
- Templates can be converted to AI templates automatically

### Template Conversion
Existing templates can be converted to AI templates:
```python
from app.services.ai_template_service import AITemplateService

service = AITemplateService()
regular_template = {
    'id': 'template_001',
    'name': 'Synthwave Template',
    'genre': 'electronic',
    'subgenre': 'synthwave',
    # ... other template fields
}

ai_template = service.convert_to_ai_template(regular_template)
```

## Callback Handling

### AI-Specific Callbacks
AI generations use a dedicated callback endpoint: `/callback/ai`

### Processing Callbacks
```python
from app.services.callback_service import AICallbackProcessor

processor = AICallbackProcessor()

# Process a callback (typically from webhook)
callback_data = request.get_json()  # From Flask request
generation = processor.process_callback(callback_data)

print(f"Generation status: {generation['status']}")
print(f"Progress: {generation['progress']}%")
if generation['status'] == 'completed':
    print(f"Quality score: {generation['quality_metrics']['overall_quality']}")
```

## Troubleshooting

### Common Issues

1. **"Working outside of application context"**
   - Solution: Use services within Flask app context
   - For testing: Create app context with `app.app_context()`

2. **API Key Errors**
   - Check `KIE_API_KEY` in environment variables
   - Enable mock mode for testing: `USE_MOCK=true`

3. **Parameter Validation Errors**
   - Use `AITemplateService.validate_ai_parameters()` to validate before generation
   - Check parameter ranges and required fields

4. **Callback Not Received**
   - Ensure `BASE_URL` or `NGROK_URL` is correctly configured
   - Check that the callback endpoint is accessible

## Next Steps for Full Integration

### 1. Add UI Components
- AI template selection interface
- Parameter customization controls
- Generation status dashboard

### 2. Implement API Routes
- `/api/generate/ai` - AI generation endpoint
- `/api/templates/ai` - AI template management
- `/api/generations` - Generation status tracking

### 3. Add Database Support
- Store generation results
- Track generation history
- Save user preferences

### 4. Production Deployment
- Configure proper callback URLs
- Set up API key rotation
- Implement rate limiting
- Add monitoring and logging

## Support
For issues with the AI music generation feature:
1. Check the [KIE_API_INTEGRATION_SUMMARY.md](KIE_API_INTEGRATION_SUMMARY.md)
2. Review test results in `test_kie_integration.py`
3. Consult the Kie API documentation for parameter details
4. Enable debug logging in the application

The AI music generation feature is now ready for integration into the application UI and can be tested with mock mode before connecting to the live Kie API.