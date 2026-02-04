"""
Callback service for the Music Cover Generator application.
Processes and extracts meaningful information from callback data.
"""
import datetime
from typing import Dict, Any, List


class CallbackService:
    """Service for processing callback data."""
    
    def process_callback_data(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and extract meaningful information from callback data.
        
        Args:
            callback_data: Raw callback data from Kie API
            
        Returns:
            Dictionary with processed callback information
        """
        if not callback_data:
            return {}
        
        processed = {
            'raw_data': callback_data,
            'code': callback_data.get('code'),
            'message': callback_data.get('msg'),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        # Extract data section
        data_section = callback_data.get('data', {})
        if isinstance(data_section, dict):
            # Check if this is a video callback (has video_url field)
            if 'video_url' in data_section:
                # This is a video callback
                processed.update({
                    'callback_type': 'video_complete',
                    'task_id': data_section.get('task_id'),
                    'video_url': data_section.get('video_url'),
                    'is_video_callback': True
                })
            else:
                # This is an audio callback
                processed.update({
                    'callback_type': data_section.get('callbackType'),
                    'task_id': data_section.get('task_id'),
                    'tracks': [],
                    'is_video_callback': False
                })
                
                # Process tracks if available
                tracks_data = data_section.get('data', [])
                if isinstance(tracks_data, list):
                    for i, track in enumerate(tracks_data):
                        if isinstance(track, dict):
                            processed_track = {
                                'track_number': i + 1,
                                'id': track.get('id'),
                                'title': track.get('title'),
                                'model_name': track.get('model_name'),
                                'tags': track.get('tags'),
                                'duration': track.get('duration'),
                                'create_time': track.get('createTime'),
                                'prompt': track.get('prompt'),
                                'audio_urls': {
                                    'generated': track.get('audio_url'),
                                    'source': track.get('source_audio_url'),
                                    'stream': track.get('stream_audio_url'),
                                    'source_stream': track.get('source_stream_audio_url')
                                },
                                'image_urls': {
                                    'generated': track.get('image_url'),
                                    'source': track.get('source_image_url')
                                }
                            }
                            processed['tracks'].append(processed_track)
        
        # Add status interpretation based on code
        status_codes = {
            0: 'success',  # Video generation success code
            200: 'success',
            400: 'validation_error',
            408: 'rate_limited',
            413: 'content_conflict',
            500: 'server_error',
            501: 'generation_failed',
            531: 'server_error_refunded'
        }
        
        processed['status'] = status_codes.get(processed['code'], 'unknown')
        
        return processed
    
    def extract_track_info(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract standardized track information from raw track data.
        
        Args:
            track_data: Raw track data from callback
            
        Returns:
            Standardized track information
        """
        return {
            'id': track_data.get('id'),
            'title': track_data.get('title'),
            'model_name': track_data.get('model_name'),
            'tags': track_data.get('tags'),
            'duration': track_data.get('duration'),
            'create_time': track_data.get('createTime'),
            'prompt': track_data.get('prompt'),
            'audio_urls': {
                'generated': track_data.get('audio_url'),
                'source': track_data.get('source_audio_url'),
                'stream': track_data.get('stream_audio_url'),
                'source_stream': track_data.get('source_stream_audio_url')
            },
            'image_urls': {
                'generated': track_data.get('image_url'),
                'source': track_data.get('source_image_url')
            }
        }
    
    def create_manual_video_entry(
        self,
        task_id: str,
        video_url: str,
        author: str = '',
        domain_name: str = ''
    ) -> Dict[str, Any]:
        """
        Create a manual video entry for videos that were successfully created on Kie
        but didn't trigger callbacks to the app.
        
        Args:
            task_id: Task ID of the video generation
            video_url: URL of the generated video
            author: Artist or creator name
            domain_name: Website or brand name
            
        Returns:
            History entry for manual video
        """
        import uuid
        import datetime
        
        return {
            'id': str(uuid.uuid4()),
            'task_id': task_id,
            'callback_type': 'video_complete',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'status_code': 0,  # Video generation success code
            'status_message': 'Video generation completed successfully',
            'status': 'success',
            'is_video_callback': True,
            'video_url': video_url,
            'author': author,
            'domain_name': domain_name,
            'tracks_count': 0,
            'has_audio_urls': False,
            'has_image_urls': False,
            'is_manual_entry': True,  # Flag to identify manual entries
            'manual_entry_time': datetime.datetime.utcnow().isoformat()
        }
    
    def validate_callback_data(self, callback_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate callback data structure.
        
        Args:
            callback_data: Callback data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not callback_data:
            return False, "Empty callback data"
        
        # Check for required fields based on callback type
        if 'code' not in callback_data:
            return False, "Missing 'code' field in callback data"
        
        # Check data section
        data_section = callback_data.get('data', {})
        if not isinstance(data_section, dict):
            return False, "Invalid 'data' section in callback data"
        
        return True, ""


class AICallbackProcessor:
    """Process Kie API callbacks for AI music generation."""
    
    def __init__(self):
        self.callback_service = CallbackService()
    
    def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Kie callback and update generation status."""
        
        callback_type = callback_data.get('data', {}).get('callbackType')
        task_id = callback_data.get('data', {}).get('task_id')
        
        # Find generation by task_id (in a real implementation, this would query a database)
        # For now, we'll create a mock generation object
        generation = self._create_mock_generation(task_id)
        
        if callback_type == 'text':
            generation['status'] = 'text_generated'
            generation['progress'] = 33
            
        elif callback_type == 'first':
            generation['status'] = 'first_track_generated'
            generation['progress'] = 66
            
        elif callback_type == 'complete':
            generation['status'] = 'completed'
            generation['progress'] = 100
            
            # Extract track data
            tracks = callback_data.get('data', {}).get('data', [])
            for track in tracks:
                self._process_generated_track(generation, track)
            
            # Calculate quality metrics
            generation['quality_metrics'] = self._calculate_quality_metrics(tracks)
        
        # Save updates (in a real implementation, this would save to a database)
        self._save_generation(generation)
        
        return generation
    
    def _create_mock_generation(self, task_id: str) -> Dict[str, Any]:
        """Create a mock generation object for testing."""
        import datetime
        import uuid
        
        return {
            'id': str(uuid.uuid4()),
            'task_id': task_id,
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'parameters': {},
            'tracks': [],
            'quality_metrics': {}
        }
    
    def _process_generated_track(self, generation: Dict[str, Any], track_data: Dict[str, Any]) -> None:
        """Process a generated track and add it to the generation."""
        processed_track = self.callback_service.extract_track_info(track_data)
        
        # Add AI-specific metadata
        processed_track['ai_metadata'] = {
            'generation_id': generation['id'],
            'model_version': track_data.get('model_name', 'unknown'),
            'quality_score': self._calculate_track_quality(track_data)
        }
        
        generation['tracks'].append(processed_track)
    
    def _calculate_track_quality(self, track_data: Dict[str, Any]) -> float:
        """Calculate quality score for a single track."""
        # Simple quality calculation based on available data
        # In a real implementation, this would be more sophisticated
        score = 0.7  # Base score
        
        # Adjust based on track duration (optimal 2-4 minutes)
        duration = track_data.get('duration', 0)
        if 120 <= duration <= 240:
            score += 0.2
        elif duration > 0:
            score += 0.1
        
        # Adjust based on model (higher models generally produce better quality)
        model = track_data.get('model_name', '')
        if 'V5' in model:
            score += 0.1
        elif 'V4_5' in model:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_quality_metrics(self, tracks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate quality metrics for generated tracks."""
        if not tracks:
            return {
                'audio_quality': 0.0,
                'musical_coherence': 0.0,
                'lyric_quality': 0.0,
                'style_adherence': 0.0,
                'overall_quality': 0.0
            }
        
        # Calculate individual track qualities
        track_qualities = [self._calculate_track_quality(track) for track in tracks]
        avg_track_quality = sum(track_qualities) / len(track_qualities) if track_qualities else 0.0
        
        # Check for lyrics
        has_lyrics = any(track.get('prompt') for track in tracks)
        
        metrics = {
            'audio_quality': self._assess_audio_quality(tracks),
            'musical_coherence': self._assess_musical_coherence(tracks),
            'lyric_quality': self._assess_lyric_quality(tracks) if has_lyrics else 1.0,
            'style_adherence': self._assess_style_adherence(tracks),
            'overall_quality': 0.0
        }
        
        # Calculate overall quality (weighted average)
        weights = {
            'audio_quality': 0.3,
            'musical_coherence': 0.4,
            'lyric_quality': 0.2,
            'style_adherence': 0.1
        }
        
        metrics['overall_quality'] = sum(
            metrics[key] * weights.get(key, 0)
            for key in metrics if key != 'overall_quality'
        )
        
        return metrics
    
    def _assess_audio_quality(self, tracks: List[Dict[str, Any]]) -> float:
        """Assess audio quality of generated tracks."""
        # Simple assessment based on model and duration
        if not tracks:
            return 0.0
        
        scores = []
        for track in tracks:
            score = 0.5  # Base score
            
            # Higher models generally produce better audio quality
            model = track.get('model_name', '')
            if 'V5' in model:
                score += 0.3
            elif 'V4_5' in model:
                score += 0.2
            elif 'V4' in model:
                score += 0.1
            
            # Longer tracks (within reason) may indicate better quality
            duration = track.get('duration', 0)
            if 60 <= duration <= 300:
                score += 0.1
            elif duration > 300:
                score += 0.05
            
            scores.append(min(score, 1.0))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _assess_musical_coherence(self, tracks: List[Dict[str, Any]]) -> float:
        """Assess musical coherence of generated tracks."""
        # This would normally involve audio analysis
        # For now, return a placeholder value
        return 0.8
    
    def _assess_lyric_quality(self, tracks: List[Dict[str, Any]]) -> float:
        """Assess lyric quality of generated tracks."""
        # Check if tracks have prompts (indicating lyrics)
        lyric_tracks = [t for t in tracks if t.get('prompt')]
        if not lyric_tracks:
            return 0.0
        
        # Simple assessment based on prompt length and model
        scores = []
        for track in lyric_tracks:
            score = 0.6  # Base score for having lyrics
            
            prompt = track.get('prompt', '')
            if len(prompt) > 20:  # Longer prompts may indicate more detailed lyrics
                score += 0.2
            
            # Higher models generally produce better lyrics
            model = track.get('model_name', '')
            if 'V5' in model:
                score += 0.2
            elif 'V4_5' in model:
                score += 0.1
            
            scores.append(min(score, 1.0))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _assess_style_adherence(self, tracks: List[Dict[str, Any]]) -> float:
        """Assess style adherence of generated tracks."""
        # This would compare generated tracks to requested style
        # For now, return a placeholder value
        return 0.7
    
    def _save_generation(self, generation: Dict[str, Any]) -> None:
        """Save generation updates (mock implementation)."""
        # In a real implementation, this would save to a database
        # For now, just log the update
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Updated generation {generation['id']} to status: {generation['status']}")