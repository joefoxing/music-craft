"""
Validation module for the Music Cover Generator application.
Contains parameter validation and constraint checking.
"""
from typing import Tuple, Optional, Dict, Any
from app.config import Config
from app.core.optional_params import validate_optional_params


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class ParameterValidator:
    """Validator for API parameters."""
    
    @staticmethod
    def validate_parameters(
        custom_mode: bool,
        instrumental: bool,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        model: str = "V5"
    ) -> Tuple[bool, str]:
        """
        Validate parameters according to API constraints.
        
        Args:
            custom_mode: Whether custom mode is enabled
            instrumental: Whether audio should be instrumental
            prompt: Description of desired audio content
            style: Music style/genre (required if custom_mode=True)
            title: Title of generated track (required if custom_mode=True)
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get model-specific character limits
        limits = Config.get_model_limits(model)
        
        # Check custom mode requirements
        if custom_mode:
            if not style:
                return False, "Style is required in custom mode"
            if not title:
                return False, "Title is required in custom mode"
            if not instrumental and not prompt:
                return False, "Prompt is required in custom mode when instrumental is false"
            
            # Check character limits
            if len(style) > limits["style"]:
                return False, f"Style exceeds {limits['style']} character limit for model {model}"
            if len(title) > limits["title"]:
                return False, f"Title exceeds {limits['title']} character limit for model {model}"
            if prompt and len(prompt) > limits["prompt"]:
                return False, f"Prompt exceeds {limits['prompt']} character limit for model {model}"
        else:
            # Non-custom mode: only prompt required, max 500 chars
            if not prompt:
                return False, "Prompt is required in non-custom mode"
            if len(prompt) > 500:
                return False, "Prompt exceeds 500 character limit in non-custom mode"
        
        return True, ""
    
    @staticmethod
    def validate_parameters_v1(
        custom_mode: bool,
        instrumental: bool,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        model: str = "V5",
        call_back_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate parameters for the v1 generate endpoint.
        
        Args:
            custom_mode: Whether custom mode is enabled
            instrumental: Whether audio should be instrumental
            prompt: Description of desired audio content or exact lyrics
            style: Music style/genre (required if custom_mode=True)
            title: Title of generated track (required if custom_mode=True)
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            call_back_url: Callback URL for status updates (required)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate required parameters for v1 endpoint
        if not call_back_url:
            return False, "callBackUrl is required"
        
        if not model:
            return False, "model is required"
        
        if not prompt:
            return False, "prompt is required"
        
        # Get model-specific character limits
        limits = Config.get_model_limits(model)
        
        # Check custom mode requirements
        if custom_mode:
            if not style:
                return False, "Style is required in custom mode"
            if not title:
                return False, "Title is required in custom mode"
            
            # Check character limits
            if len(style) > limits["style"]:
                return False, f"Style exceeds {limits['style']} character limit for model {model}"
            if len(title) > limits["title"]:
                return False, f"Title exceeds {limits['title']} character limit for model {model}"
            if prompt and len(prompt) > limits["prompt"]:
                return False, f"Prompt exceeds {limits['prompt']} character limit for model {model}"
        else:
            # Non-custom mode: only prompt required, max 500 chars
            if len(prompt) > 500:
                return False, "Prompt exceeds 500 character limit in non-custom mode"
        
        return True, ""
    
    @staticmethod
    def validate_optional_parameters(
        params_dict: Dict[str, Any],
        custom_mode: bool = False
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Validate and normalize optional generation parameters.
        
        Args:
            params_dict: Dictionary containing optional parameters
            custom_mode: Whether custom mode is enabled
            
        Returns:
            Tuple of (cleaned_params_dict, error_message)
            cleaned_params_dict contains only valid, normalized parameters
            error_message is None if validation passes, otherwise contains error
        """
        return validate_optional_params(params_dict, custom_mode)
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate audio filename.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename is required"
        
        if not Config.is_extension_allowed(filename):
            allowed = ", ".join(Config.get_allowed_extensions())
            return False, f"File type not allowed. Allowed types: {allowed}"
        
        return True, ""
    
    @staticmethod
    def validate_url(url: str, allowed_domains: Optional[list] = None) -> Tuple[bool, str]:
        """
        Validate URL format and domain.
        
        Args:
            url: URL to validate
            allowed_domains: List of allowed domains (optional)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"
        
        # Check URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            return False, "Invalid URL format. URL must start with http:// or https://"
        
        # Check allowed domains if specified
        if allowed_domains:
            import urllib.parse
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            
            if not any(allowed_domain in domain for allowed_domain in allowed_domains):
                return False, f"URL domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
        
        return True, ""
    
    @staticmethod
    def validate_audio_url_for_kie(url: str) -> Tuple[bool, str]:
        """
        Validate URL for Kie API compatibility.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        allowed_domains = [
            'musicfile.kie.ai',
            'kie.ai',
            'cdn1.suno.ai',
            'cdn2.suno.ai'
        ]
        
        return ParameterValidator.validate_url(url, allowed_domains)


class ModelValidator:
    """Validator for model-specific constraints."""
    
    @staticmethod
    def get_model_info(model: str) -> dict:
        """
        Get information about a specific model.
        
        Args:
            model: Model version
            
        Returns:
            Dictionary with model information
        """
        models = {
            'V5': {
                'name': 'V5',
                'description': 'Superior musical expression, faster generation',
                'limits': Config.get_model_limits('V5')
            },
            'V4_5PLUS': {
                'name': 'V4_5PLUS',
                'description': 'V4.5+ delivers richer sound, new ways to create, max 8 min',
                'limits': Config.get_model_limits('V4_5PLUS')
            },
            'V4_5': {
                'name': 'V4_5',
                'description': 'V4.5 enables smarter prompts, faster generations, max 8 min',
                'limits': Config.get_model_limits('V4_5')
            },
            'V4_5ALL': {
                'name': 'V4_5ALL',
                'description': 'V4.5ALL enables smarter prompts, faster generations, max 8 min',
                'limits': Config.get_model_limits('V4_5ALL')
            },
            'V4': {
                'name': 'V4',
                'description': 'V4 improves vocal quality, max 4 min',
                'limits': Config.get_model_limits('V4')
            }
        }
        
        return models.get(model, models['V5'])
    
    @staticmethod
    def get_all_models() -> dict:
        """
        Get information about all available models.
        
        Returns:
            Dictionary with all model information
        """
        models = {}
        for model in ['V5', 'V4_5PLUS', 'V4_5', 'V4_5ALL', 'V4']:
            models[model] = ModelValidator.get_model_info(model)
        return models