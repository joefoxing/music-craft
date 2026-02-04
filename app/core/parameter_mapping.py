"""
Parameter mapping module for the Music Cover Generator application.
Contains functions for converting between different parameter formats.
"""
from typing import Dict, Any, Optional, List
from app.config import Config


class ParameterMapper:
    """Mapper for converting between parameter formats."""
    
    @staticmethod
    def convert_to_kie_parameters(our_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert our parameter format to Kie API format.
        
        Args:
            our_params: Our standardized parameter format
            
        Returns:
            Kie API parameter dictionary
        """
        # Determine model based on requirements
        model = ParameterMapper.select_kie_model(
            duration=our_params.get('duration', 180),
            has_lyrics=our_params.get('lyrics', {}).get('enabled', False),
            quality=our_params.get('audio_quality', 'medium')
        )
        
        # Generate style description
        style = ParameterMapper.generate_kie_style(
            genre=our_params.get('genre'),
            subgenre=our_params.get('subgenre'),
            mood=our_params.get('mood'),
            instruments=our_params.get('primary_instruments', [])
        )
        
        # Build parameters
        kie_params = {
            'customMode': True,  # Always use custom mode for control
            'instrumental': not our_params.get('lyrics', {}).get('enabled', False),
            'model': model,
            'callBackUrl': ParameterMapper.get_callback_url(),
            'style': style,
            'title': our_params.get('title', 'Generated Track')
        }
        
        # Add lyrics if needed
        if not kie_params['instrumental']:
            kie_params['prompt'] = ParameterMapper.generate_lyrics(
                theme=our_params.get('lyrics', {}).get('theme'),
                style=our_params.get('lyrics', {}).get('style'),
                language=our_params.get('lyrics', {}).get('language', 'en')
            )
        else:
            kie_params['prompt'] = our_params.get('prompt', '')
        
        # Add advanced parameters
        kie_params.update({
            'styleWeight': our_params.get('ai_parameters', {}).get('genre_adherence', 0.9),
            'weirdnessConstraint': 1.0 - our_params.get('ai_parameters', {}).get('creativity', 0.7),
            'audioWeight': our_params.get('ai_parameters', {}).get('coherence', 0.8)
        })
        
        # Add vocal gender if specified
        if 'lyrics' in our_params and 'vocal_characteristics' in our_params['lyrics']:
            gender = our_params['lyrics']['vocal_characteristics'].get('gender', 'f')
            kie_params['vocalGender'] = 'm' if gender == 'male' else 'f'
        
        return kie_params
    
    @staticmethod
    def select_kie_model(
        duration: int = 180,
        has_lyrics: bool = False,
        quality: str = 'medium'
    ) -> str:
        """
        Select appropriate Kie model based on parameters.
        
        Args:
            duration: Track duration in seconds
            has_lyrics: Whether the track has lyrics
            quality: Audio quality (low, medium, high)
            
        Returns:
            Model name (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
        """
        if quality == 'high':
            return 'V5'
        elif quality == 'medium':
            if has_lyrics and duration > 240:
                return 'V4_5PLUS'
            else:
                return 'V4_5'
        else:  # low quality or default
            return 'V4'
    
    @staticmethod
    def generate_kie_style(
        genre: Optional[str] = None,
        subgenre: Optional[str] = None,
        mood: Optional[str] = None,
        instruments: Optional[List[str]] = None
    ) -> str:
        """
        Generate Kie style description from components.
        
        Args:
            genre: Primary genre (e.g., rock, pop, electronic)
            subgenre: Subgenre (e.g., synthwave, lo-fi, trap)
            mood: Emotional mood (e.g., happy, sad, energetic)
            instruments: List of primary instruments
            
        Returns:
            Style description string
        """
        parts = []
        
        # Add genre components
        if genre:
            parts.append(genre)
        if subgenre:
            parts.append(subgenre)
        
        # Add mood
        if mood:
            mood_descriptors = {
                'happy': 'upbeat, joyful, positive',
                'sad': 'melancholic, emotional, introspective',
                'energetic': 'energetic, dynamic, powerful',
                'calm': 'calm, peaceful, relaxing',
                'mysterious': 'mysterious, atmospheric, enigmatic',
                'romantic': 'romantic, passionate, emotional',
                'aggressive': 'aggressive, intense, powerful',
                'dreamy': 'dreamy, ethereal, atmospheric'
            }
            parts.append(mood_descriptors.get(mood, mood))
        
        # Add instruments if specified
        if instruments:
            instrument_text = ', '.join(instruments[:3])  # Limit to 3 instruments
            parts.append(f"featuring {instrument_text}")
        
        if not parts:
            return "electronic, ambient, atmospheric"
        
        return ", ".join(parts)
    
    @staticmethod
    def generate_lyrics(
        theme: Optional[str] = None,
        style: Optional[str] = None,
        language: str = 'en'
    ) -> str:
        """
        Generate lyrics prompt from parameters.
        
        Args:
            theme: Lyric theme (e.g., love, loss, hope)
            style: Lyric style (e.g., poetic, narrative, abstract)
            language: Language code
            
        Returns:
            Lyrics prompt string
        """
        theme = theme or 'love'
        style = style or 'poetic'
        
        prompt = f"{style} lyrics about {theme}"
        if language != 'en':
            prompt += f" in {language}"
        
        return prompt
    
    @staticmethod
    def get_callback_url() -> str:
        """
        Get callback URL for AI generation.
        
        Returns:
            Callback URL string
        """
        # Use the same logic as Config.get_public_base_url
        return Config.get_public_base_url(request=None) + "/callback/ai"
    
    @staticmethod
    def map_template_to_kie(template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map template parameters to Kie API format.
        
        Args:
            template: Template dictionary
            
        Returns:
            Kie API parameters
        """
        # Extract parameters from template
        params = {
            'genre': template.get('genre'),
            'subgenre': template.get('subgenre'),
            'mood': template.get('mood'),
            'duration': template.get('duration', 180),
            'title': template.get('name', 'Generated Track'),
            'prompt': template.get('description', ''),
            'primary_instruments': template.get('instruments', []),
            'audio_quality': template.get('quality', 'medium'),
            'complexity': template.get('complexity', 'simple')
        }
        
        # Handle lyrics if present in template
        if template.get('has_lyrics', False):
            params['lyrics'] = {
                'enabled': True,
                'theme': template.get('lyric_theme', 'love'),
                'style': template.get('lyric_style', 'poetic'),
                'language': template.get('language', 'en'),
                'vocal_characteristics': {
                    'gender': template.get('vocal_gender', 'f')
                }
            }
        
        # Handle AI parameters if present
        if 'ai_parameters' in template:
            params['ai_parameters'] = template['ai_parameters']
        else:
            # Default AI parameters
            params['ai_parameters'] = {
                'genre_adherence': template.get('genre_adherence', 0.9),
                'creativity': template.get('creativity', 0.7),
                'coherence': template.get('coherence', 0.8)
            }
        
        return ParameterMapper.convert_to_kie_parameters(params)
    
    @staticmethod
    def create_ai_template_structure(
        template_id: str,
        name: str,
        genre: str,
        subgenre: Optional[str] = None,
        mood: Optional[str] = None,
        has_lyrics: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create AI template structure compatible with Kie API.
        
        Args:
            template_id: Unique template ID
            name: Template name
            genre: Primary genre
            subgenre: Subgenre (optional)
            mood: Mood (optional)
            has_lyrics: Whether template includes lyrics
            **kwargs: Additional template parameters
            
        Returns:
            AI template structure
        """
        template = {
            'id': template_id,
            'name': name,
            'template_type': 'kie_generation',
            'genre': genre,
            'subgenre': subgenre,
            'mood': mood,
            'has_lyrics': has_lyrics,
            'description': kwargs.get('description', f'{genre} {subgenre or ""} {mood or ""}'.strip()),
            'duration': kwargs.get('duration', 180),
            'quality': kwargs.get('quality', 'medium'),
            'complexity': kwargs.get('complexity', 'simple'),
            'popularity': kwargs.get('popularity', 50),
            'difficulty': kwargs.get('difficulty', 'intermediate'),
            'tags': kwargs.get('tags', [genre])
        }
        
        # Add Kie-specific mapping
        template['kie_mapping'] = {
            'model': ParameterMapper.select_kie_model(
                duration=kwargs.get('duration', 180),
                has_lyrics=has_lyrics,
                quality=kwargs.get('quality', 'medium')
            ),
            'custom_mode': True,
            'base_style': ParameterMapper.generate_kie_style(genre, subgenre, mood),
            'style_variations': kwargs.get('style_variations', {}),
            'parameter_defaults': {
                'style_weight': kwargs.get('style_weight', 0.9),
                'weirdness_constraint': kwargs.get('weirdness_constraint', 0.3),
                'audio_weight': kwargs.get('audio_weight', 0.8)
            }
        }
        
        # Add parameter constraints
        template['parameter_constraints'] = {
            'bpm_range': kwargs.get('bpm_range', [80, 160]),
            'duration_range': kwargs.get('duration_range', [60, 300]),
            'lyric_themes': kwargs.get('lyric_themes', [])
        }
        
        # Add lyrics configuration if needed
        if has_lyrics:
            template['lyrics_config'] = {
                'theme': kwargs.get('lyric_theme', 'love'),
                'style': kwargs.get('lyric_style', 'poetic'),
                'language': kwargs.get('language', 'en'),
                'vocal_gender': kwargs.get('vocal_gender', 'f')
            }
        
        return template