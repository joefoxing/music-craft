"""
API client module for the Music Cover Generator application.
Handles communication with Kie API for music generation.
"""
import requests
import json
import logging
import time
import hashlib
from typing import Dict, Any, Optional
from flask import current_app

from app.config import Config
from app.core.validation import ParameterValidator
from app.services.history_service import HistoryService


logger = logging.getLogger(__name__)


class KieAPIClient:
    """Client for interacting with Kie API for music cover generation."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize Kie API client.
        
        Args:
            api_key: Kie API key (optional, will use config if not provided)
            base_url: Kie API base URL (optional, will use config if not provided)
        """
        self.api_key = api_key or Config.KIE_API_KEY
        self.base_url = base_url or Config.KIE_API_BASE_URL
        self.use_mock = Config.USE_MOCK
        
        # If no API key is provided, force mock mode
        if not self.api_key:
            self.use_mock = True
            
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        if self.use_mock:
            logger.info("Using mock mode for Kie API")
            if not hasattr(KieAPIClient, '_mock_task_states'):
                KieAPIClient._mock_task_states = {}
            self._mock_task_states = KieAPIClient._mock_task_states
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value, handling both Flask context and standalone usage.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
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
            return self._mock_upload_and_cover_audio(upload_url, prompt, custom_mode, instrumental, model)
        
        endpoint = f"{self.base_url}/api/v1/generate/upload-cover"
        
        # Build request payload based on API documentation
        # Use public base URL
        base_url = Config.get_public_base_url()
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
        
        logger.info(f"Using callback URL: {call_back_url_to_use}")
        
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
        
        # Round numeric parameters to 2 decimal places
        from decimal import Decimal, ROUND_HALF_UP
        
        def round_to_two_decimals(value):
            """Round a value to 2 decimal places if it's numeric."""
            if value is None:
                return None
            try:
                return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return value
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                value = optional_params[field]
                # Round numeric fields
                if field in ["styleWeight", "weirdnessConstraint", "audioWeight"]:
                    value = round_to_two_decimals(value)
                payload[field] = value
        
        try:
            logger.info(f"Making request to Kie API: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
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
            logger.info("Using mock mode for upload_and_extend_audio")
            
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
        base_url = Config.get_public_base_url()
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
            
        logger.info(f"Using callback URL for extend: {call_back_url_to_use}")
        
        # Add optional parameters if provided
        optional_fields = [
            "negativeTags", "vocalGender", "styleWeight",
            "weirdnessConstraint", "audioWeight", "personaId"
        ]
        
        # Round numeric parameters to 2 decimal places
        from decimal import Decimal, ROUND_HALF_UP
        
        def round_to_two_decimals(value):
            """Round a value to 2 decimal places if it's numeric."""
            if value is None:
                return None
            try:
                return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return value
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                value = optional_params[field]
                # Round numeric fields
                if field in ["styleWeight", "weirdnessConstraint", "audioWeight"]:
                    value = round_to_two_decimals(value)
                payload[field] = value
                
        try:
            logger.info(f"Making request to Kie API: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API extend request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API extend request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
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
            result = self._mock_get_task_status(task_id)
            return self._transform_task_status_response(result)
        
        # Correct endpoint from documentation: /api/v1/generate/record-info?taskId={task_id}
        endpoint = f"{self.base_url}/api/v1/generate/record-info"
        
        try:
            logger.info(f"Checking task status for task_id: {task_id}")
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={"taskId": task_id},
                timeout=15
            )
            
            logger.info(f"Task status response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                transformed = self._transform_task_status_response(result, task_id)
                logger.info(f"Task status response: {json.dumps(transformed, indent=2)}")
                return transformed
            else:
                logger.error(f"Task status error: {response.status_code} - {response.text[:500]}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Task status request failed: {e}")
            
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
    
    def _transform_task_status_response(self, result, task_id=None):
        """
        Transform Kie API task status response to match frontend expectations.
        
        Args:
            result: Raw API response dict
            task_id: Optional task ID for history lookup
            
        Returns:
            Transformed response dict
        """
        if not isinstance(result, dict):
            return result
        
        # Add status field based on code and API status
        code = result.get('code')
        data = result.get('data')

        # Ensure data is a dict (replace None with empty dict)
        if data is None:
            result['data'] = {}
            data = result['data']

        # Extract original API status if available
        api_status = None
        if isinstance(data, dict):
            api_status = data.get('status')
            # Also copy error fields for frontend access (they are already in data)
            # No need to duplicate

        # Determine internal status based on API status mapping
        if api_status is not None:
            # Map API status to internal status
            if api_status == 'SUCCESS':
                internal_status = 'SUCCESS'
            elif api_status == 'PENDING':
                internal_status = 'PROCESSING'
            elif api_status in ['CREATE_TASK_FAILED', 'GENERATE_LYRICS_FAILED',
                                'CALLBACK_EXCEPTION', 'SENSITIVE_WORD_ERROR']:
                internal_status = 'FAILED'
            else:
                internal_status = 'PROCESSING'
        else:
            # Fallback to code-based logic
            if code == 200:
                # Determine if task is still processing (no data or empty data.data)
                if isinstance(data, dict):
                    lyrics_data = data.get('data')
                    if lyrics_data is None:
                        # Try to get lyrics data from response.data (lyrics endpoint)
                        response_data = data.get('response')
                        if isinstance(response_data, dict):
                            lyrics_data = response_data.get('data')
                    # If data is None or empty list, treat as processing (lyrics not ready)
                    if lyrics_data is None or (isinstance(lyrics_data, list) and len(lyrics_data) == 0):
                        internal_status = 'PROCESSING'
                    else:
                        internal_status = 'SUCCESS'
                else:
                    internal_status = 'SUCCESS'
            else:
                internal_status = 'FAILED'

        result['status'] = internal_status
        
        # Ensure data section exists and is dict
        if isinstance(data, dict):
            # Add status to data as well (for frontend)
            data['status'] = result['status']
            
            # Check if this is a lyrics response
            lyrics_data = data.get('data')
            if lyrics_data is None:
                # Try to get lyrics data from response.data (lyrics endpoint)
                response_data = data.get('response')
                if isinstance(response_data, dict):
                    lyrics_data = response_data.get('data')
            if lyrics_data is None:
                lyrics_data = []
            if isinstance(lyrics_data, list) and len(lyrics_data) > 0:
                # Check if first item has text field (lyrics) or lyrics field
                first_item = lyrics_data[0]
                text_field = first_item.get('text')
                lyrics_field = first_item.get('lyrics')
                if text_field is not None or lyrics_field is not None:
                    # Normalize lyrics data: ensure each item has 'text' field
                    normalized_lyrics = []
                    for item in lyrics_data:
                        normalized = dict(item)
                        if 'lyrics' in item and 'text' not in item:
                            normalized['text'] = item['lyrics']
                        normalized_lyrics.append(normalized)
                    # Create response.lyricsData structure (preserve existing response fields)
                    if 'response' not in data:
                        data['response'] = {}
                    data['response']['lyricsData'] = normalized_lyrics
                    logger.debug(f"Added lyrics response: {data['response']}")
        
        # If no lyrics data from API, check history for callbacks with lyrics data
        if task_id and not data.get('response') and isinstance(data, dict):
            try:
                history_service = HistoryService()
                history_entries = history_service.get_history_by_task_id(task_id)
                for entry in history_entries:
                    # Look for callback data with lyrics
                    callback_data = entry.get('data')
                    if isinstance(callback_data, dict) and callback_data.get('callbackType') == 'complete':
                        lyrics_items = callback_data.get('data')
                        if isinstance(lyrics_items, list) and len(lyrics_items) > 0:
                            # Check if first item has text field
                            if lyrics_items[0].get('text') is not None or lyrics_items[0].get('lyrics') is not None:
                                normalized_lyrics = []
                                for item in lyrics_items:
                                    normalized = dict(item)
                                    if 'lyrics' in item and 'text' not in item:
                                        normalized['text'] = item['lyrics']
                                    normalized_lyrics.append(normalized)
                                data['response'] = {
                                    'lyricsData': normalized_lyrics
                                }
                                # Update status to SUCCESS since we have lyrics
                                result['status'] = 'SUCCESS'
                                data['status'] = 'SUCCESS'
                                logger.debug(f"Added lyrics response from history for task {task_id}")
                                break
            except Exception as e:
                logger.debug(f"Error checking history for lyrics data: {e}")
        
        return result
    
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
            return self._mock_generate_music_video(task_id, audio_id)
        
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
            logger.info(f"Making request to Kie API for music video generation: {endpoint}")
            logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API music video request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API music video request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
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

    def generate_lyrics(
        self,
        prompt: str,
        call_back_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate lyrics from text prompt using Kie API.
        
        Args:
            prompt: Description of desired lyrics content (max 200 words)
            call_back_url: Callback URL for status updates
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            return self._mock_generate_lyrics(prompt)
        
        endpoint = f"{self.base_url}/api/v1/lyrics"
        
        # Build request payload based on API documentation
        # Use public base URL
        base_url = Config.get_public_base_url()
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        payload = {
            "prompt": prompt,
            "callBackUrl": call_back_url_to_use
        }
        
        logger.info(f"Using callback URL for lyrics generation: {call_back_url_to_use}")
        
        try:
            logger.info(f"Making request to Kie API for lyrics generation: {endpoint}")
            logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API lyrics request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API lyrics request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
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
                        f"Please check if this is the correct endpoint for lyrics generation."
                    )
            
            raise
    
    def get_lyrics_record_info(self, task_id: str) -> Dict[str, Any]:
        """
        Get status and results of a lyrics generation task.

        Args:
            task_id: Task ID returned from generate_lyrics

        Returns:
            API response dictionary with lyrics data
        """
        if self.use_mock:
            result = self._mock_get_task_status(task_id)
            return self._transform_task_status_response(result, task_id)

        endpoint = f"{self.base_url}/api/v1/lyrics/record-info"

        try:
            logger.info(f"Checking lyrics record info for task_id: {task_id}")
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={"taskId": task_id},
                timeout=15
            )

            logger.info(f"Lyrics record info response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                transformed = self._transform_task_status_response(result, task_id)
                logger.info(f"Lyrics record info response: {json.dumps(transformed, indent=2)}")
                return transformed
            else:
                logger.error(f"Lyrics record info error: {response.status_code} - {response.text[:500]}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"Lyrics record info request failed: {e}")

            if "404" in str(e):
                raise requests.exceptions.RequestException(
                    f"Lyrics record info endpoint not found (404). "
                    f"The endpoint '{endpoint}?taskId={task_id}' may not be correct. "
                    f"Please check the Kie API documentation."
                )
            elif "403" in str(e):
                raise requests.exceptions.RequestException(
                    f"Authentication failed (403). Please check your API key."
                )
            else:
                raise requests.exceptions.RequestException(
                    f"Failed to retrieve lyrics record info: {e}. "
                    f"Please rely on callbacks for status updates."
                )

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
            logger.info("Using mock mode for add_instrumental")
            
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
        # Use public base URL
        base_url = Config.get_public_base_url()
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        # Ensure numeric parameters are rounded to 2 decimal places
        # This is a defensive measure in case validation wasn't applied upstream
        from decimal import Decimal, ROUND_HALF_UP
        
        def round_to_two_decimals(value: float) -> float:
            """Round a float value to 2 decimal places."""
            try:
                return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return value
        
        style_weight = round_to_two_decimals(style_weight)
        weirdness_constraint = round_to_two_decimals(weirdness_constraint)
        audio_weight = round_to_two_decimals(audio_weight)
        
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
        
        logger.info(f"Using callback URL: {call_back_url_to_use}")
        
        try:
            logger.info(f"Making request to Kie API: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
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

    def add_vocals(
        self,
        upload_url: str,
        prompt: str,
        title: str,
        style: Optional[str] = None,
        tags: Optional[str] = None,
        negative_tags: Optional[str] = None,
        model: str = "V5",
        vocal_gender: str = "male",
        style_weight: float = 0.61,
        weirdness_constraint: float = 0.72,
        audio_weight: float = 0.65,
        call_back_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add vocals (layer AI-generated vocals on top of an existing instrumental).
        
        Args:
            upload_url: URL where the instrumental audio file is hosted
            prompt: Description of desired vocal content/lyrics
            title: Title of the vocal track
            style: Musical style/genre for the vocals
            tags: Comma-separated tags describing the vocal style
            negative_tags: Comma-separated tags to avoid in generation
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            vocal_gender: Vocal gender ('male', 'female', 'mixed', or empty for auto)
            style_weight: Style weight parameter (0-1)
            weirdness_constraint: Weirdness constraint parameter (0-1)
            audio_weight: Audio weight parameter (0-1)
            call_back_url: Callback URL for status updates
            
        Returns:
            API response dictionary with taskId
        """
        if self.use_mock:
            logger.info("Using mock mode for add_vocals")
            
            # Generate a mock task ID
            task_id = hashlib.md5(f"{upload_url}{prompt}{title}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/generate/add-vocals"
        
        # Build request payload based on API documentation
        # Use public base URL
        base_url = Config.get_public_base_url()
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        # Ensure numeric parameters are rounded to 2 decimal places
        from decimal import Decimal, ROUND_HALF_UP
        
        def round_to_two_decimals(value: float) -> float:
            """Round a float value to 2 decimal places."""
            try:
                return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return value
        
        style_weight = round_to_two_decimals(style_weight)
        weirdness_constraint = round_to_two_decimals(weirdness_constraint)
        audio_weight = round_to_two_decimals(audio_weight)
        
        # Build payload according to Kie API specification
        payload = {
            "uploadUrl": upload_url,
            "prompt": prompt,
            "title": title,
            "callBackUrl": call_back_url_to_use,
            "model": model,
            "styleWeight": style_weight,
            "weirdnessConstraint": weirdness_constraint,
            "audioWeight": audio_weight
        }
        
        # Add optional parameters if provided
        if style:
            payload["style"] = style
        if tags:
            payload["tags"] = tags
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if vocal_gender:
            # Convert to API format if needed
            if vocal_gender.lower() == "male":
                payload["vocalGender"] = "m"
            elif vocal_gender.lower() == "female":
                payload["vocalGender"] = "f"
            elif vocal_gender.lower() == "mixed":
                payload["vocalGender"] = "mixed"
            else:
                payload["vocalGender"] = vocal_gender
        
        logger.info(f"Using callback URL for add-vocals: {call_back_url_to_use}")
        
        try:
            logger.info(f"Making request to Kie API add-vocals endpoint: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API add-vocals request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API add-vocals request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for add-vocals."
                    )
                elif e.response.status_code == 402:
                    raise requests.exceptions.RequestException(
                        "Insufficient credits (402). Please add more credits to your account."
                    )
            
            raise

    def vocal_removal(
        self,
        task_id: str,
        audio_id: str,
        type: str,
        call_back_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Split tracks into stems using Suno's get-stem API.
        
        Args:
            task_id: ID of the original music-generation task
            audio_id: Which audio variation to process
            type: Separation mode ('separate_vocal' or 'split_stem')
            call_back_url: Callback URL for status updates
            
        Returns:
            API response dictionary
        """
        if self.use_mock:
            logger.info("Using mock mode for vocal_removal")
            
            # Generate a mock task ID
            mock_task_id = hashlib.md5(f"{task_id}{audio_id}{type}{time.time()}".encode()).hexdigest()[:24]
            
            # Simulate API delay
            time.sleep(0.5)
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": mock_task_id
                }
            }
        
        endpoint = f"{self.base_url}/api/v1/vocal-removal/generate"
        
        # Build request payload based on API documentation
        # Use public base URL
        base_url = Config.get_public_base_url()
        if not base_url and not call_back_url:
            # Try to construct from request context if available
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except:
                pass
        
        call_back_url_to_use = call_back_url or f"{base_url}/callback"
        
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
            "callBackUrl": call_back_url_to_use,
            "type": type
        }
        
        logger.info(f"Using callback URL for vocal removal: {call_back_url_to_use}")
        
        try:
            logger.info(f"Making request to Kie API vocal removal endpoint: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API vocal removal request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API vocal removal request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
                if e.response.status_code == 401:
                    raise requests.exceptions.RequestException(
                        "Authentication failed (401). Please check your API key."
                    )
                elif e.response.status_code == 404:
                    raise requests.exceptions.RequestException(
                        f"Endpoint not found (404): {endpoint}. "
                        f"Please check if this is the correct endpoint for vocal removal."
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
        return ParameterValidator.validate_parameters(
            custom_mode, instrumental, prompt, style, title, model
        )
    
    def validate_parameters_v1(
        self,
        custom_mode: bool,
        instrumental: bool,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        model: str = "V5",
        call_back_url: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Validate parameters for the v1 generate endpoint.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return ParameterValidator.validate_parameters_v1(
            custom_mode, instrumental, prompt, style, title, model, call_back_url
        )
    
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
            return self._mock_generate_music_direct(custom_mode, instrumental, call_back_url, model, prompt)
        
        endpoint = f"{self.base_url}/api/v1/generate"
        
        # Build request payload based on API documentation
        payload = {
            "customMode": custom_mode,
            "instrumental": instrumental,
            "callBackUrl": call_back_url,
            "model": model,
            "prompt": prompt
        }
        
        logger.info(f"Using callback URL for direct music generation: {call_back_url}")
        
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
        
        # Round numeric parameters to 2 decimal places
        from decimal import Decimal, ROUND_HALF_UP
        
        def round_to_two_decimals(value):
            """Round a value to 2 decimal places if it's numeric."""
            if value is None:
                return None
            try:
                return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return value
        
        for field in optional_fields:
            if field in optional_params and optional_params[field] is not None:
                value = optional_params[field]
                # Round numeric fields
                if field in ["styleWeight", "weirdnessConstraint", "audioWeight"]:
                    value = round_to_two_decimals(value)
                payload[field] = value
        
        try:
            logger.info(f"Making request to Kie API v1 generate endpoint: {endpoint}")
            logger.info(f"Request payload keys: {list(payload.keys())}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kie API v1 generate request successful: {result.get('code', 'No code')}")
            logger.info(f"Kie API response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kie API v1 generate request failed: {e}")
            
            # Try to get more details from response if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
                
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
                        f"Please check if this is the correct endpoint for direct music generation."
                    )
                elif e.response.status_code == 422:
                    raise requests.exceptions.RequestException(
                        f"Validation error (422): {e.response.text[:200]}"
                    )
            
            raise
    
    # Mock methods for testing
    def _mock_upload_and_cover_audio(
        self,
        upload_url: str,
        prompt: str,
        custom_mode: bool,
        instrumental: bool,
        model: str
    ) -> Dict[str, Any]:
        """Mock implementation for upload_and_cover_audio."""
        logger.info("Using mock mode for upload_and_cover_audio")
        
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
    
    def _mock_get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Mock implementation for get_task_status."""
        logger.info(f"Using mock mode for get_task_status for task_id: {task_id}")
        
        # Create a deterministic progression based on task_id
        # This ensures the same task always follows the same progression
        task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
        
        # Track mock task states
        if task_id not in self._mock_task_states:
            # First time seeing this task, initialize its state
            self._mock_task_states[task_id] = {
                'created_at': time.time(),
                'poll_count': 0,
                'stage': 'text'  # Start with text generation
            }
        
        task_state = self._mock_task_states[task_id]
        # Ensure required keys exist (for tasks created by _mock_generate_lyrics)
        if 'poll_count' not in task_state:
            task_state['poll_count'] = 0
        if 'stage' not in task_state:
            task_state['stage'] = 'text'
        if 'created_at' not in task_state:
            task_state['created_at'] = time.time()
        
        task_state['poll_count'] += 1
        logger.debug(f"Mock task {task_id} poll count: {task_state['poll_count']}")
        print(f"[MOCK] task {task_id} poll count: {task_state['poll_count']}")
        
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
        # Check if this is a lyrics task
        is_lyrics = task_state.get('is_lyrics', False)
        logger.info(f"Mock returning stage={stage}, poll_count={task_state['poll_count']}, is_lyrics={is_lyrics}")
        
        if stage == 'text':
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "callbackType": "text",
                    "task_id": task_id,
                    "data": [],
                    "poll_count": task_state['poll_count'],
                    "stage": stage
                }
            }
        elif stage == 'first':
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "callbackType": "first",
                    "task_id": task_id,
                    "data": [],
                    "poll_count": task_state['poll_count'],
                    "stage": stage
                }
            }
        else:  # complete
            if is_lyrics:
                # Generate mock lyrics data
                return {
                    "code": 200,
                    "msg": "All generated successfully.",
                    "data": {
                        "callbackType": "complete",
                        "task_id": task_id,
                        "poll_count": task_state['poll_count'],
                        "stage": stage,
                        "data": [
                            {
                                "error_message": "",
                                "status": "complete",
                                "text": "[Verse]\nThis is a mock lyrics generated for testing.\nIt has verses and a chorus.\n\n[Chorus]\nSing along with the music.\nThis is just a placeholder.\n\n[Verse 2]\nMore lines to fill the space.\nHope you enjoy the song.",
                                "title": "Mock Lyrics"
                            }
                        ]
                    }
                }
            else:
                # Generate mock audio data
                return {
                    "code": 200,
                    "msg": "All generated successfully.",
                    "data": {
                        "callbackType": "complete",
                        "task_id": task_id,
                        "poll_count": task_state['poll_count'],
                        "stage": stage,
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
    
    def _mock_generate_music_video(self, task_id: str, audio_id: str) -> Dict[str, Any]:
        """Mock implementation for generate_music_video."""
        logger.info("Using mock mode for generate_music_video")
        
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

    def _mock_generate_lyrics(self, prompt: str) -> Dict[str, Any]:
        """Mock implementation for generate_lyrics."""
        logger.info("Using mock mode for generate_lyrics")
        
        # Generate a mock task ID
        task_id = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:24]
        
        # Mark this task as a lyrics task for mock status tracking
        if task_id not in self._mock_task_states:
            self._mock_task_states[task_id] = {}
        self._mock_task_states[task_id]['is_lyrics'] = True
        self._mock_task_states[task_id]['prompt'] = prompt
        
        # Simulate API delay
        time.sleep(0.5)
        
        # Return mock response matching the API documentation format
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "taskId": task_id
            }
        }
    
    def _mock_generate_music_direct(
        self,
        custom_mode: bool,
        instrumental: bool,
        call_back_url: str,
        model: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Mock implementation for generate_music_direct."""
        logger.info("Using mock mode for generate_music_direct")
        
        # Generate a mock task ID
        task_id = hashlib.md5(f"{custom_mode}{instrumental}{prompt}{time.time()}".encode()).hexdigest()[:24]
        
        # Simulate API delay
        time.sleep(0.5)
        
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "taskId": task_id
            }
        }