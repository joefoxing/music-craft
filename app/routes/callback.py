"""
Callback routes for the Music Cover Generator application.
Handles Kie API callbacks and history management.
"""
from flask import Blueprint, request, jsonify, current_app
import datetime
import uuid
import json

from app.config import Config
from app.core.utils import ResponseUtils, DateTimeUtils, JSONUtils
from app.services.history_service import HistoryService
from app.services.callback_service import CallbackService


callback_bp = Blueprint('callback', __name__)


@callback_bp.route('/callback-with-history', methods=['POST'])
def callback_handler_with_history():
    """
    Handle Kie API callbacks and store them in history.
    """
    try:
        callback_data = request.json
        if not callback_data:
            current_app.logger.warning("Received empty callback data")
            return jsonify(ResponseUtils.create_error_response('Empty callback data')), 400
        
        current_app.logger.info(f"Received callback: {json.dumps(callback_data, indent=2)}")
        
        # Extract task information
        task_id = callback_data.get('task_id') or callback_data.get('data', {}).get('task_id')
        callback_type = callback_data.get('callbackType')
        
        if not task_id:
            current_app.logger.warning("Callback missing task_id")
            return jsonify(ResponseUtils.create_error_response('Missing task_id')), 400
        
        current_app.logger.info(f"Callback for task_id: {task_id}, type: {callback_type}")
        
        # Create history entry
        history_entry = {
            'id': str(uuid.uuid4()),
            'task_id': task_id,
            'callback_type': callback_type,
            'timestamp': DateTimeUtils.get_current_iso_timestamp(),
            'data': callback_data,
            'status': 'received'
        }
        
        # Add to history
        history_service = HistoryService()
        if history_service.add_to_history(history_entry):
            current_app.logger.info(f"Callback stored in history for task: {task_id}")
        else:
            current_app.logger.warning(f"Failed to store callback in history for task: {task_id}")
        
        # Always respond quickly (within 15 seconds as required)
        return jsonify(ResponseUtils.create_success_response({
            'task_id': task_id,
            'callback_type': callback_type,
            'timestamp': DateTimeUtils.get_current_iso_timestamp()
        }, 'Callback received and stored')), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing callback: {e}")
        current_app.logger.exception(e)
        
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@callback_bp.route('/callback', methods=['POST'])
def callback_handler():
    """
    Handle Kie API callbacks.
    
    Requirements from Kie documentation:
    - Must respond within 15 seconds
    - Should handle multiple callbacks for same task
    - Must handle errors appropriately (400, 413, etc.)
    - 3 consecutive failures will stop callbacks
    """
    try:
        callback_data = request.json
        if not callback_data:
            current_app.logger.warning("Received empty callback data")
            return jsonify(ResponseUtils.create_error_response('Empty callback data')), 400
        
        current_app.logger.info(f"Received callback: {json.dumps(callback_data, indent=2)}")
        
        # Process callback data
        callback_service = CallbackService()
        processed_data = callback_service.process_callback_data(callback_data)
        
        # Extract task information
        task_id = processed_data.get('task_id')
        callback_type = processed_data.get('callback_type')
        status_code = processed_data.get('code')
        status_message = processed_data.get('message')
        
        if task_id:
            current_app.logger.info(f"Callback for task_id: {task_id}, type: {callback_type}, code: {status_code}")
            
            # Check if this is a video callback
            is_video_callback = processed_data.get('is_video_callback', False)
            
            if is_video_callback:
                # Video callback handling
                video_url = processed_data.get('video_url')
                current_app.logger.info(f"Video callback received. Video URL: {video_url}")
                
                # Create enhanced history entry for video
                history_entry = {
                    'id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'callback_type': callback_type,
                    'timestamp': DateTimeUtils.get_current_iso_timestamp(),
                    'status_code': status_code,
                    'status_message': status_message,
                    'status': processed_data.get('status'),
                    'processed_data': processed_data,
                    'raw_data': callback_data,
                    'is_video_callback': True,
                    'video_url': video_url,
                    'tracks_count': 0,
                    'has_audio_urls': False,
                    'has_image_urls': False
                }
            else:
                # Audio callback handling
                tracks = processed_data.get('tracks', [])
                if tracks:
                    current_app.logger.info(f"Callback contains {len(tracks)} track(s)")
                    for i, track in enumerate(tracks):
                        current_app.logger.info(f"Track {i+1}: {track.get('title')} (ID: {track.get('id')})")
                
                # Create enhanced history entry for audio
                history_entry = {
                    'id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'callback_type': callback_type,
                    'timestamp': DateTimeUtils.get_current_iso_timestamp(),
                    'status_code': status_code,
                    'status_message': status_message,
                    'status': processed_data.get('status'),
                    'processed_data': processed_data,
                    'raw_data': callback_data,
                    'is_video_callback': False,
                    'tracks_count': len(tracks),
                    'has_audio_urls': any(
                        track.get('audio_urls', {}).get('generated')
                        for track in tracks
                    ),
                    'has_image_urls': any(
                        track.get('image_urls', {}).get('generated')
                        for track in tracks
                    )
                }
            
            # Add to history
            history_service = HistoryService()
            try:
                history_service.add_to_history(history_entry)
                current_app.logger.info(f"Callback stored in history for task: {task_id}")
                
                # Also update existing entry if this is a progress update
                if callback_type in ['text', 'first', 'complete', 'video_complete']:
                    history_service.update_history_entry(task_id, {
                        'last_callback_type': callback_type,
                        'last_callback_time': DateTimeUtils.get_current_iso_timestamp(),
                        'callback_progress': callback_type,
                        'processed_data': processed_data
                    })
                    
            except Exception as history_error:
                current_app.logger.error(f"Failed to store callback in history: {history_error}")
        else:
            current_app.logger.warning("Callback missing task_id")
        
        # Always respond quickly (within 15 seconds as required)
        response_data = ResponseUtils.create_success_response({
            'task_id': task_id,
            'callback_type': callback_type,
            'status_code': status_code,
            'is_video_callback': processed_data.get('is_video_callback', False),
            'tracks_count': len(processed_data.get('tracks', [])),
            'timestamp': DateTimeUtils.get_current_iso_timestamp()
        }, 'Callback received and processed')
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing callback: {e}")
        current_app.logger.exception(e)  # Log full traceback
        
        # Return error but don't crash - Kie will retry up to 3 times
        return jsonify(ResponseUtils.create_error_response(str(e))), 500