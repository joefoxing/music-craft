"""
AI Template service for the Music Cover Generator application.
Manages AI music generation templates and their integration with Kie API.
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app

from app.core.utils import JSONUtils, FileUtils
from app.core.parameter_mapping import ParameterMapper
from app.services.template_service import TemplateService


class AITemplateService:
    """Service for managing AI music generation templates."""
    
    def __init__(self):
        """Initialize AI template service."""
        self.template_service = TemplateService()
        self.ai_templates_file = self._get_ai_templates_file_path()
        FileUtils.ensure_directory_exists(os.path.dirname(self.ai_templates_file))
        self._ai_templates_cache = None
    
    def _get_ai_templates_file_path(self) -> str:
        """Get the path to the AI templates JSON file."""
        templates_dir = os.path.join(current_app.root_path, 'static', 'templates')
        
        # Try to load the AI templates file
        ai_path = os.path.join(templates_dir, 'ai_templates.json')
        if os.path.exists(ai_path):
            return ai_path
        
        # If no AI templates file exists, we'll create one from existing templates
        return ai_path
    
    def load_ai_templates(self) -> List[Dict[str, Any]]:
        """
        Load AI templates data from JSON file.
        
        Returns:
            List of AI template entries
        """
        if self._ai_templates_cache is not None:
            return self._ai_templates_cache
        
        # Try to load AI templates file
        if os.path.exists(self.ai_templates_file):
            data = JSONUtils.load_json_file(self.ai_templates_file, {"ai_templates": []})
            templates = data.get("ai_templates", [])
        else:
            # Generate AI templates from existing templates
            templates = self._generate_ai_templates_from_existing()
        
        self._ai_templates_cache = templates
        return templates
    
    def _generate_ai_templates_from_existing(self) -> List[Dict[str, Any]]:
        """Generate AI templates from existing templates."""
        existing_templates = self.template_service.get_all_templates()
        ai_templates = []
        
        for template in existing_templates:
            # Convert existing template to AI template format
            ai_template = self.convert_to_ai_template(template)
            if ai_template:
                ai_templates.append(ai_template)
        
        return ai_templates
    
    def convert_to_ai_template(self, template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a regular template to an AI template.
        
        Args:
            template: Regular template dictionary
            
        Returns:
            AI template dictionary or None if conversion not possible
        """
        # Extract key parameters
        template_id = template.get('id')
        name = template.get('name')
        genre = template.get('genre') or template.get('style', '').split(',')[0] if template.get('style') else 'electronic'
        
        if not template_id or not name:
            return None
        
        # Create AI template structure
        ai_template = ParameterMapper.create_ai_template_structure(
            template_id=f"ai_{template_id}",
            name=f"AI {name}",
            genre=genre,
            subgenre=template.get('subgenre'),
            mood=template.get('mood'),
            has_lyrics=template.get('has_lyrics', False),
            description=template.get('description', f'AI-generated {genre} music'),
            duration=template.get('duration', 180),
            quality=template.get('quality', 'medium'),
            complexity=template.get('complexity', 'simple'),
            popularity=template.get('popularity', 50),
            difficulty=template.get('difficulty', 'intermediate'),
            tags=template.get('tags', [genre]),
            bpm_range=template.get('bpm_range', [80, 160]),
            duration_range=template.get('duration_range', [60, 300]),
            lyric_themes=template.get('lyric_themes', []),
            lyric_theme=template.get('lyric_theme', 'love'),
            lyric_style=template.get('lyric_style', 'poetic'),
            language=template.get('language', 'en'),
            vocal_gender=template.get('vocal_gender', 'f')
        )
        
        # Preserve original template ID reference
        ai_template['original_template_id'] = template_id
        
        return ai_template
    
    def get_all_ai_templates(self) -> List[Dict[str, Any]]:
        """
        Get all AI templates.
        
        Returns:
            List of all AI templates
        """
        return self.load_ai_templates()
    
    def get_ai_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific AI template by ID.
        
        Args:
            template_id: AI template ID to find
            
        Returns:
            AI template or None if not found
        """
        templates = self.load_ai_templates()
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None
    
    def get_ai_templates_by_type(self, template_type: str) -> List[Dict[str, Any]]:
        """
        Get AI templates filtered by template type.
        
        Args:
            template_type: Template type to filter by (e.g., 'kie_generation')
            
        Returns:
            List of AI templates of the specified type
        """
        templates = self.load_ai_templates()
        return [t for t in templates if t.get('template_type') == template_type]
    
    def detect_ai_template(self, template: Dict[str, Any]) -> bool:
        """
        Detect if a template is an AI template.
        
        Args:
            template: Template dictionary
            
        Returns:
            True if template is an AI template, False otherwise
        """
        # Check for AI-specific fields
        if template.get('template_type') == 'kie_generation':
            return True
        
        if 'kie_mapping' in template:
            return True
        
        # Check for AI generation capabilities
        if template.get('generation_method') == 'ai':
            return True
        
        return False
    
    def validate_ai_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate AI generation parameters.
        
        Args:
            parameters: AI generation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['genre', 'duration']
        for field in required_fields:
            if field not in parameters:
                return False, f"Missing required field: {field}"
        
        # Validate duration
        duration = parameters.get('duration', 0)
        if not isinstance(duration, (int, float)) or duration <= 0:
            return False, "Duration must be a positive number"
        
        if duration > 600:  # 10 minutes max
            return False, "Duration cannot exceed 600 seconds (10 minutes)"
        
        # Validate quality
        quality = parameters.get('audio_quality', 'medium')
        if quality not in ['low', 'medium', 'high']:
            return False, "Audio quality must be 'low', 'medium', or 'high'"
        
        # Validate complexity
        complexity = parameters.get('complexity', 'simple')
        if complexity not in ['simple', 'complex']:
            return False, "Complexity must be 'simple' or 'complex'"
        
        # Validate lyrics if present
        if parameters.get('lyrics', {}).get('enabled', False):
            lyrics = parameters['lyrics']
            if 'theme' not in lyrics:
                return False, "Lyric theme is required when lyrics are enabled"
            
            language = lyrics.get('language', 'en')
            if len(language) != 2:
                return False, "Language must be a 2-letter code"
        
        # Validate AI parameters
        ai_params = parameters.get('ai_parameters', {})
        for param in ['genre_adherence', 'creativity', 'coherence']:
            if param in ai_params:
                value = ai_params[param]
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    return False, f"{param} must be a number between 0 and 1"
        
        return True, ""
    
    def generate_kie_parameters(self, template_id: str, user_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate Kie API parameters from AI template and user parameters.
        
        Args:
            template_id: AI template ID
            user_parameters: Optional user parameter overrides
            
        Returns:
            Kie API parameters
        """
        # Get AI template
        template = self.get_ai_template_by_id(template_id)
        if not template:
            raise ValueError(f"AI template not found: {template_id}")
        
        # Merge template defaults with user parameters
        parameters = self._merge_parameters(template, user_parameters or {})
        
        # Validate parameters
        is_valid, error_message = self.validate_ai_parameters(parameters)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {error_message}")
        
        # Convert to Kie API format
        kie_parameters = ParameterMapper.map_template_to_kie(parameters)
        
        return kie_parameters
    
    def _merge_parameters(self, template: Dict[str, Any], user_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Merge template defaults with user parameters."""
        # Start with template defaults
        merged = {
            'genre': template.get('genre'),
            'subgenre': template.get('subgenre'),
            'mood': template.get('mood'),
            'duration': template.get('duration', 180),
            'title': template.get('name', 'AI Generated Track'),
            'prompt': template.get('description', ''),
            'primary_instruments': template.get('instruments', []),
            'audio_quality': template.get('quality', 'medium'),
            'complexity': template.get('complexity', 'simple')
        }
        
        # Add AI parameters from template
        if 'kie_mapping' in template and 'parameter_defaults' in template['kie_mapping']:
            defaults = template['kie_mapping']['parameter_defaults']
            merged['ai_parameters'] = {
                'genre_adherence': defaults.get('style_weight', 0.9),
                'creativity': 1.0 - defaults.get('weirdness_constraint', 0.3),
                'coherence': defaults.get('audio_weight', 0.8)
            }
        
        # Add lyrics configuration if present in template
        if template.get('has_lyrics', False) and 'lyrics_config' in template:
            lyrics_config = template['lyrics_config']
            merged['lyrics'] = {
                'enabled': True,
                'theme': lyrics_config.get('theme', 'love'),
                'style': lyrics_config.get('style', 'poetic'),
                'language': lyrics_config.get('language', 'en'),
                'vocal_characteristics': {
                    'gender': lyrics_config.get('vocal_gender', 'f')
                }
            }
        
        # Override with user parameters
        for key, value in user_parameters.items():
            if value is not None:
                if key == 'ai_parameters' and 'ai_parameters' in merged:
                    # Merge AI parameters
                    merged['ai_parameters'].update(value)
                elif key == 'lyrics' and 'lyrics' in merged:
                    # Merge lyrics parameters
                    merged['lyrics'].update(value)
                else:
                    merged[key] = value
        
        return merged
    
    def process_generation_result(self, kie_response: Dict[str, Any], template_id: str) -> Dict[str, Any]:
        """
        Process Kie API generation result.
        
        Args:
            kie_response: Kie API response
            template_id: AI template ID used for generation
            
        Returns:
            Processed generation result
        """
        template = self.get_ai_template_by_id(template_id)
        if not template:
            raise ValueError(f"AI template not found: {template_id}")
        
        # Extract task ID
        task_id = kie_response.get('data', {}).get('taskId')
        if not task_id:
            raise ValueError("No task ID in Kie API response")
        
        # Create result structure
        result = {
            'generation_id': f"gen_{task_id}",
            'task_id': task_id,
            'template_id': template_id,
            'template_name': template.get('name'),
            'status': 'queued',
            'created_at': self._get_current_timestamp(),
            'estimated_completion': self._estimate_completion_time(template),
            'kie_response': kie_response
        }
        
        return result
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        import datetime
        return datetime.datetime.utcnow().isoformat()
    
    def _estimate_completion_time(self, template: Dict[str, Any]) -> int:
        """Estimate completion time in seconds based on template."""
        duration = template.get('duration', 180)
        quality = template.get('quality', 'medium')
        complexity = template.get('complexity', 'simple')
        
        # Base time per second of audio
        base_time_per_second = 2
        
        # Adjust for quality
        quality_multiplier = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }.get(quality, 1.5)
        
        # Adjust for complexity
        complexity_multiplier = 2.0 if complexity == 'complex' else 1.0
        
        estimated_seconds = duration * base_time_per_second * quality_multiplier * complexity_multiplier
        
        # Add fixed overhead
        estimated_seconds += 30
        
        return int(estimated_seconds)
    
    def save_ai_templates(self, templates: List[Dict[str, Any]]) -> bool:
        """
        Save AI templates to file.
        
        Args:
            templates: List of AI templates to save
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            'ai_templates': templates,
            'metadata': {
                'version': '1.0',
                'generated_at': self._get_current_timestamp(),
                'count': len(templates)
            }
        }
        
        try:
            JSONUtils.save_json_file(self.ai_templates_file, data)
            self._ai_templates_cache = templates
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save AI templates: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear the AI templates cache."""
        self._ai_templates_cache = None
        self.template_service.clear_cache()