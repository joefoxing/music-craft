import requests
import json
import logging
import uuid
from flask import current_app
from typing import Dict, Any, Optional, List

class KieAPIClient:
    """Client for interacting with Kie API for music cover generation."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or self._get_config('KIE_API_KEY')
        self.base_url = base_url or self._get_config('KIE_API_BASE_URL', 'https://api.kie.ai')
        
        # Get USE_MOCK config - it might be a boolean or string
        use_mock_config = self._get_config('USE_MOCK', 'false')
        if isinstance(use_mock_config, bool):
            self.use_mock = use_mock_config
        else:
            self.use_mock = str(use_mock_config).lower() == 'true'
        
        # If no API key is provided, force mock mode
        if not self.api_key:
            self.use_mock = True
            
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.logger = logging.getLogger(__name__)
        if self.use_mock:
            self.logger.info("Using mock mode for Kie API")
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value, handling both Flask context and standalone usage."""
        try:
            # Try to get from Flask current_app
            if current_app and hasattr(current_app, 'config'):
                return current_app.config.get(key, default)
        except RuntimeError:
            # Outside of Flask context
            pass
        return default
    
    def upload_and_cover_audio(
        self,
        upload_url: str,
        prompt: str,
        custom_mode: bool = False,
        instrumental: bool = False,
        model: str = "V5",
        call_back_url: Optional[str] = None,
        style: Optional[str] = None,
        title: Optional[str] = None,
        **optional_params
    ) -> Dict[str, Any]:
        """
        Upload and cover audio using Kie API.
        
        Args:
            upload_url: URL where the audio file is hosted
            prompt: Description of desired audio content
            custom_mode: Whether to use custom mode
            instrumental: Whether the audio should be instrumental
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            call_back_url: Callback URL for status updates
            style: Music style/genre (required if custom_mode=True)
            title: Title of generated track (required if custom_mode=True)
            **optional_params: Additional optional parameters
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            self.logger.info("Using mock mode for upload_and_cover_audio")
            import time
            import hashlib
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{upload_url}{prompt}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/generate/upload-cover"
        
        # Build request payload based on API documentation
        # Use BASE_URL
        base_url = self._get_config('BASE_URL', '')
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        payload = {
            "uploadUrl": upload_url,
            "prompt": prompt,
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": call_back_url_to_use
        }
        
        self.logger.info(f"Using callback URL: {call_back_url_to_use}")
        
        # Add required fields based on mode
        if custom_mode:
            if style:
                payload["style"] = style
            if title:
                payload["title"] = title
        
        # Add optional parameters if provided
        optional_fields = [
            "negativeTags", "vocalGender", "styleWeight",
            "weirdnessConstraint", "audioWeight", "personaId"
        ]
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                payload[field] = optional_params[field]
        
        try:
            self.logger.info(f"Making request to Kie API: {endpoint}")
            self.logger.info(f"Request payload keys: {list(payload.keys())}")
            self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API request successful: {result.get('code', 'No code')}")
            self.logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for upload-and-cover."
                    )
                elif e.response.status_code == 402:
                    raise requests.exceptions.RequestException(
                        "Insufficient credits (402). Please add more credits to your account."
                    )
            
            raise
    
    def upload_and_extend_audio(
        self,
        upload_url: str,
        continue_at: int,
        prompt: str,
        instrumental: bool = False,
        model: str = "V5",
        call_back_url: Optional[str] = None,
        style: Optional[str] = None,
        title: Optional[str] = None,
        default_param_flag: bool = True,
        **optional_params
    ) -> Dict[str, Any]:
        """
        Upload and extend audio using Kie API.
        
        Args:
            upload_url: URL where the audio file is hosted
            continue_at: Timestamp (in seconds) to start extension
            prompt: Description of desired extension content
            instrumental: Whether the extension should be instrumental
            model: Model version (V5, etc.)
            call_back_url: Callback URL for status updates
            style: Music style/genre
            title: Title of generated track
            default_param_flag: Whether to use default parameters (True by default)
            **optional_params: Additional optional parameters including:
                - negativeTags (str)
                - vocalGender (str)
                - styleWeight (float)
                - weirdnessConstraint (float)
                - audioWeight (float)
                - personaId (str)
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            self.logger.info("Using mock mode for upload_and_extend_audio")
            import time
            import hashlib
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{upload_url}{continue_at}{prompt}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/generate/upload-extend"
        
        # Build request payload
        base_url = self._get_config('BASE_URL', '')
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        # Based on user sample code
        payload = {
            "uploadUrl": upload_url,
            "defaultParamFlag": default_param_flag,
            "instrumental": instrumental,
            "continueAt": continue_at,
            "model": model,
            "callBackUrl": call_back_url_to_use,
            "prompt": prompt
        }
        
        if style:
            payload["style"] = style
        if title:
            payload["title"] = title
            
        self.logger.info(f"Using callback URL for extend: {call_back_url_to_use}")
        
        # Add optional parameters if provided
        optional_fields = [
            "negativeTags", "vocalGender", "styleWeight",
            "weirdnessConstraint", "audioWeight", "personaId"
        ]
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                payload[field] = optional_params[field]
                
        try:
            self.logger.info(f"Making request to Kie API: {endpoint}")
            self.logger.info(f"Request payload keys: {list(payload.keys())}")
            self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API extend request successful: {result.get('code', 'No code')}")
            self.logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API extend request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a music generation task.
        
        Args:
            task_id: Task ID returned from upload-and-cover-audio
            
        Returns:
            Task status dictionary or error information
        """
        if self.use_mock:
            self.logger.info(f"Using mock mode for get_task_status for task_id: {task_id}")
            import time
            import hashlib
            
            # Create a deterministic progression based on task_id
            # This ensures the same task always follows the same progression
            task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
            
            # Simulate time-based progression
            # Use the last 3 digits of the hash to determine progression speed
            progression_speed = (task_hash % 1000) / 1000.0  # 0.0 to 1.0
            
            # Track mock task states in a simple in-memory cache
            # In a real implementation, this would be stored in a database
            if not hasattr(self, '_mock_task_states'):
                self._mock_task_states = {}
            
            if task_id not in self._mock_task_states:
                # First time seeing this task, initialize its state
                self._mock_task_states[task_id] = {
                    'created_at': time.time(),
                    'poll_count': 0,
                    'stage': 'text'  # Start with text generation
                }
            
            task_state = self._mock_task_states[task_id]
            task_state['poll_count'] += 1
            
            # Determine current stage based on poll count
            # Progress through stages: text -> first -> complete
            if task_state['poll_count'] <= 2:
                stage = 'text'
            elif task_state['poll_count'] <= 4:
                stage = 'first'
            else:
                stage = 'complete'
            
            # Update stage
            task_state['stage'] = stage
            
            if stage == 'text':
                return {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "callbackType": "text",
                        "task_id": task_id,
                        "data": []
                    }
                }
            elif stage == 'first':
                return {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "callbackType": "first",
                        "task_id": task_id,
                        "data": []
                    }
                }
            else:  # complete
                # Generate mock audio data
                return {
                    "code": 200,
                    "msg": "All generated successfully.",
                    "data": {
                        "callbackType": "complete",
                        "task_id": task_id,
                        "data": [
                            {
                                "id": f"mock_{task_id}_1",
                                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                                "source_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                                "stream_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                                "source_stream_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                                "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
                                "source_image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
                                "prompt": "Mock generated audio for testing purposes",
                                "model_name": "chirp-v3-5",
                                "title": "Mock Music Cover",
                                "tags": "test, mock, demo",
                                "createTime": "2025-01-01 00:00:00",
                                "duration": 120.5
                            }
                        ]
                    }
                }
        
        # Correct endpoint from documentation: /api/v1/generate/record-info?taskId={task_id}
        endpoint = f"{self.base_url}/api/v1/generate/record-info"
        
        try:
            self.logger.info(f"Checking task status for task_id: {task_id}")
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={"taskId": task_id},
                timeout=15
            )
            
            self.logger.info(f"Task status response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Task status response: {json.dumps(result, indent=2)}")
                return result
            else:
                self.logger.error(f"Task status error: {response.status_code} - {response.text[:500]}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Task status request failed: {e}")
            
            # Provide more helpful error message
            if "404" in str(e):
                raise requests.exceptions.RequestException(
                    f"Task status endpoint not found (404). "
                    f"The endpoint '{endpoint}?taskId={task_id}' may not be correct for upload-and-cover tasks. "
                    f"Please check the Kie API documentation for the correct task status endpoint."
                )
            elif "403" in str(e):
                raise requests.exceptions.RequestException(
                    f"Authentication failed (403). Please check your API key."
                )
            else:
                raise requests.exceptions.RequestException(
                    f"Failed to retrieve task status: {e}. "
                    f"Please rely on callbacks for status updates."
                )
    
    def generate_music_video(
        self,
        task_id: str,
        audio_id: str,
        call_back_url: str,
        author: Optional[str] = None,
        domain_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate music video using Kie API.
        
        Args:
            task_id: Unique identifier of the music generation task
            audio_id: Unique identifier of the specific audio track to visualize
            call_back_url: URL to receive music video generation task completion updates
            author: Artist or creator name to display as a signature (max 50 chars)
            domain_name: Website or brand to display as a watermark (max 50 chars)
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            self.logger.info("Using mock mode for generate_music_video")
            import time
            import hashlib
            
            # Generate a mock video task ID
            video_task_id = hashlib.md5(f"{task_id}{audio_id}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 0,
                "msg": "",
                "data": {
                    "taskId": video_task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/mp4/generate"
        
        # Build request payload based on API documentation
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
            "callBackUrl": call_back_url
        }
        
        # Add optional parameters if provided
        if author:
            payload["author"] = author[:50]  # Enforce max length
        if domain_name:
            payload["domainName"] = domain_name[:50]  # Enforce max length
        
        try:
            self.logger.info(f"Making request to Kie API for music video generation: {endpoint}")
            self.logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API music video request successful: {result.get('code', 'No code')}")
            self.logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API music video request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 402:
                    raise requests.exceptions.RequestException(
                        "Insufficient credits (402). Please add more credits to your account."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for music video generation."
                    )
            
            raise
    
    def generate_music_direct(
        self,
        custom_mode: bool,
        instrumental: bool,
        call_back_url: str,
        model: str,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        **optional_params
    ) -> Dict[str, Any]:
        """
        Generate music directly using the /api/v1/generate endpoint.
        
        Args:
            custom_mode: Whether to use custom mode
            instrumental: Whether the audio should be instrumental
            call_back_url: Callback URL for status updates (required)
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            prompt: Description of desired audio content or exact lyrics
            style: Music style/genre (required if custom_mode=True)
            title: Title of generated track (required if custom_mode=True)
            **optional_params: Additional optional parameters
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            self.logger.info("Using mock mode for generate_music_direct")
            import time
            import hashlib
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{prompt}{model}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/generate"
        
        # Build request payload
        payload = {
            "customMode": custom_mode,
            "instrumental": instrumental,
            "callBackUrl": call_back_url,
            "model": model,
            "prompt": prompt
        }
        
        # Add optional fields based on mode
        if custom_mode:
            if style:
                payload["style"] = style
            if title:
                payload["title"] = title
        
        # Add optional parameters if provided
        optional_fields = [
            "negativeTags", "vocalGender", "styleWeight",
            "weirdnessConstraint", "audioWeight", "personaId"
        ]
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                payload[field] = optional_params[field]
        
        try:
            self.logger.info(f"Making request to Kie API: {endpoint}")
            self.logger.info(f"Request payload keys: {list(payload.keys())}")
            self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API generate request successful: {result.get('code', 'No code')}")
            self.logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API generate request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
            raise
    
    def add_instrumental(
        self,
        upload_url: str,
        title: str,
        negative_tags: Optional[str] = None,
        tags: Optional[str] = None,
        call_back_url: Optional[str] = None,
        model: str = "V4_5PLUS",
        vocal_gender: str = "m",
        style_weight: float = 0.61,
        weirdness_constraint: float = 0.72,
        audio_weight: float = 0.65
    ) -> Dict[str, Any]:
        """
        Add instrumental using Kie API.
        
        Args:
            upload_url: URL where the audio file is hosted
            title: Title of the instrumental track
            negative_tags: Tags to avoid in generation
            tags: Tags describing the instrumental
            call_back_url: Callback URL for status updates
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            vocal_gender: Vocal gender ('m' for male, 'f' for female)
            style_weight: Style weight parameter (0-1)
            weirdness_constraint: Weirdness constraint parameter (0-1)
            audio_weight: Audio weight parameter (0-1)
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            self.logger.info("Using mock mode for add_instrumental")
            import time
            import hashlib
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{upload_url}{title}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/generate/add-instrumental"
        
        # Build request payload based on API documentation
        # Use BASE_URL
        base_url = self._get_config('BASE_URL', '')
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        payload = {
            "uploadUrl": upload_url,
            "title": title,
            "callBackUrl": call_back_url_to_use,
            "model": model,
            "vocalGender": vocal_gender,
            "styleWeight": style_weight,
            "weirdnessConstraint": weirdness_constraint,
            "audioWeight": audio_weight
        }
        
        # Add optional parameters if provided
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if tags:
            payload["tags"] = tags
        
        self.logger.info(f"Using callback URL: {call_back_url_to_use}")
        
        try:
            self.logger.info(f"Making request to Kie API: {endpoint}")
            self.logger.info(f"Request payload keys: {list(payload.keys())}")
            self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API request successful: {result.get('code', 'No code')}")
            self.logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for add-instrumental."
                    )
                elif e.response.status_code == 402:
                    raise requests.exceptions.RequestException(
                        "Insufficient credits (402). Please add more credits to your account."
                    )
            
            raise
    
    def validate_parameters(
        self,
        custom_mode: bool,
        instrumental: bool,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        model: str = "V5"
    ) -> tuple[bool, str]:
        """
        Validate parameters according to API constraints.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Model-specific character limits
        model_limits = {
            "V5": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5PLUS": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5ALL": {"prompt": 5000, "style": 1000, "title": 80},
            "V4": {"prompt": 3000, "style": 200, "title": 80}
        }
        
        limits = model_limits.get(model, model_limits["V5"])
        
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


class EnhancedKieAPIClient(KieAPIClient):
    """Extended client for AI music generation."""
    
    def generate_ai_music(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI music using Kie API with our parameter format.
        
        Args:
            parameters: Our standardized parameter format
            
        Returns:
            Generation response with task_id
        """
        # Convert our parameters to Kie API format
        kie_params = self._convert_to_kie_format(parameters)
        
        # Call Kie API
        response = self._call_kie_generate_endpoint(kie_params)
        
        return {
            'task_id': response['data']['taskId'],
            'generation_id': f"ai_gen_{uuid.uuid4().hex[:8]}",
            'status': 'queued',
            'estimated_completion': self._estimate_completion_time(parameters)
        }
    
    def _convert_to_kie_format(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert our parameter format to Kie API format."""
        # Map genre/mood to style
        style = self._generate_style_description(
            parameters.get('genre'),
            parameters.get('subgenre'),
            parameters.get('mood')
        )
        
        # Determine if custom mode is needed
        custom_mode = parameters.get('complexity', 'simple') != 'simple'
        
        # Build Kie parameters
        kie_params = {
            'customMode': custom_mode,
            'instrumental': not parameters.get('lyrics', {}).get('enabled', False),
            'model': self._select_model(parameters),
            'callBackUrl': self._get_callback_url(),
            'prompt': parameters.get('prompt', ''),
            'style': style,
            'title': parameters.get('title', 'AI Generated Track')
        }
        
        # Add optional parameters if in custom mode
        if custom_mode:
            if parameters.get('lyrics', {}).get('enabled'):
                kie_params['prompt'] = self._generate_lyrics_prompt(parameters)
            
            # Add advanced parameters
            kie_params.update({
                'vocalGender': parameters.get('lyrics', {}).get('vocal_characteristics', {}).get('gender', 'f'),
                'styleWeight': parameters.get('ai_parameters', {}).get('genre_adherence', 0.9),
                'weirdnessConstraint': 1.0 - parameters.get('ai_parameters', {}).get('creativity', 0.7),
                'audioWeight': parameters.get('ai_parameters', {}).get('coherence', 0.8)
            })
        
        return kie_params
    
    def _generate_style_description(self, genre: Optional[str], subgenre: Optional[str], mood: Optional[str]) -> str:
        """Generate a style description from genre, subgenre, and mood."""
        parts = []
        if genre:
            parts.append(genre)
        if subgenre:
            parts.append(subgenre)
        if mood:
            parts.append(mood)
        
        if not parts:
            return "electronic, ambient, atmospheric"
        
        return ", ".join(parts)
    
    def _select_model(self, parameters: Dict[str, Any]) -> str:
        """Select appropriate Kie model based on parameters."""
        duration = parameters.get('duration', 180)
        has_lyrics = parameters.get('lyrics', {}).get('enabled', False)
        quality = parameters.get('audio_quality', 'medium')
        
        if quality == 'high':
            return 'V5'
        elif quality == 'medium':
            if has_lyrics and duration > 240:
                return 'V4_5PLUS'
            else:
                return 'V4_5'
        else:  # low quality or default
            return 'V4'
    
    def _get_callback_url(self) -> str:
        """Get callback URL for AI generation."""
        base_url = self._get_config('BASE_URL', '')
        if not base_url:
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                base_url = 'http://localhost:5000'
        
        return f"{base_url}/callback/ai"
    
    def _generate_lyrics_prompt(self, parameters: Dict[str, Any]) -> str:
        """Generate lyrics prompt from parameters."""
        lyrics_config = parameters.get('lyrics', {})
        theme = lyrics_config.get('theme', 'love')
        style = lyrics_config.get('style', 'poetic')
        language = lyrics_config.get('language', 'en')
        
        prompt = f"{style} lyrics about {theme}"
        if language != 'en':
            prompt += f" in {language}"
        
        return prompt
    
    def _call_kie_generate_endpoint(self, kie_params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Kie API generate endpoint with the given parameters."""
        if self.use_mock:
            self.logger.info("Using mock mode for AI music generation")
            import time
            import hashlib
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{kie_params.get('prompt', '')}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        # For AI generation, we need to use a different endpoint
        # Since the implementation plan doesn't specify the exact endpoint,
        # we'll use the existing upload-and-cover endpoint for now
        # In a real implementation, this would be a dedicated AI generation endpoint
        endpoint = f"{self.base_url}/api/v1/generate/upload-cover"
        
        # Build payload - note: we need an upload_url for the existing endpoint
        # For pure AI generation without an upload, we might need a different approach
        # For now, we'll use a placeholder URL
        payload = {
            "uploadUrl": "https://example.com/placeholder.mp3",  # Placeholder for AI generation
            "prompt": kie_params.get('prompt', ''),
            "customMode": kie_params.get('customMode', False),
            "instrumental": kie_params.get('instrumental', False),
            "model": kie_params.get('model', 'V5'),
            "callBackUrl": kie_params.get('callBackUrl', ''),
            "style": kie_params.get('style', ''),
            "title": kie_params.get('title', 'AI Generated Track')
        }
        
        # Add optional parameters
        optional_fields = ['vocalGender', 'styleWeight', 'weirdnessConstraint', 'audioWeight']
        for field in optional_fields:
            if field in kie_params:
                payload[field] = kie_params[field]
        
        try:
            self.logger.info(f"Making AI generation request to Kie API: {endpoint}")
            self.logger.info(f"Request payload keys: {list(payload.keys())}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            self.logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Kie API AI generation request successful: {result.get('code', 'No code')}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Kie API AI generation request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for AI generation."
                    )
                elif e.response.status_code == 402:
                    raise requests.exceptions.RequestException(
                        "Insufficient credits (402). Please add more credits to your account."
                    )
            
            raise
    
    def _estimate_completion_time(self, parameters: Dict[str, Any]) -> int:
        """Estimate completion time in seconds based on parameters."""
        duration = parameters.get('duration', 180)
        quality = parameters.get('audio_quality', 'medium')
        
        # Base time per second of audio
        base_time_per_second = 2  # seconds of processing per second of audio
        
        # Adjust for quality
        quality_multiplier = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }.get(quality, 1.5)
        
        # Adjust for complexity
        complexity = parameters.get('complexity', 'simple')
        complexity_multiplier = 2.0 if complexity == 'complex' else 1.0
        
        estimated_seconds = duration * base_time_per_second * quality_multiplier * complexity_multiplier
        
        # Add fixed overhead
        estimated_seconds += 30
        
        return int(estimated_seconds)