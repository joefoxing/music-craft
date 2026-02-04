"""
History API routes for the Music Cover Generator application.
Contains endpoints for managing and retrieving callback history.
"""
from flask import Blueprint, request, jsonify, current_app

from app.config import Config
from app.core.utils import ResponseUtils, DateTimeUtils
from app.services.history_service import HistoryService
from app.services.callback_service import CallbackService


history_api_bp = Blueprint('history_api', __name__, url_prefix='/api/history')


@history_api_bp.route('', methods=['GET'])
def get_history():
    """Get all history entries."""
    try:
        history_service = HistoryService()
        history = history_service.load_history()
        
        return jsonify(ResponseUtils.create_success_response({
            'history': history,
            'count': len(history)
        }))
    except Exception as e:
        current_app.logger.error(f"Error getting history: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/<entry_id>', methods=['GET'])
def get_history_entry(entry_id):
    """Get a specific history entry by ID."""
    try:
        history_service = HistoryService()
        entry = history_service.get_history_entry(entry_id)
        
        if entry:
            return jsonify(ResponseUtils.create_success_response({
                'entry': entry
            }))
        else:
            return jsonify(ResponseUtils.create_error_response('History entry not found')), 404
    except Exception as e:
        current_app.logger.error(f"Error getting history entry: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/clear', methods=['POST'])
def clear_history():
    """Clear all history entries."""
    try:
        history_service = HistoryService()
        if history_service.clear_history():
            return jsonify(ResponseUtils.create_success_response(
                message='History cleared successfully'
            ))
        else:
            return jsonify(ResponseUtils.create_error_response('Failed to clear history')), 500
    except Exception as e:
        current_app.logger.error(f"Error clearing history: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/delete', methods=['POST'])
def delete_history_entries():
    """Delete selected history entries by entry IDs."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400

        entry_ids = data.get('ids')
        if not isinstance(entry_ids, list) or not entry_ids:
            return jsonify(ResponseUtils.create_error_response('ids must be a non-empty list')), 400

        history_service = HistoryService()
        removed_count, remaining_count = history_service.delete_history_entries(entry_ids)

        return jsonify(ResponseUtils.create_success_response({
            'removed_count': removed_count,
            'remaining_count': remaining_count
        }, message='History entries deleted successfully'))
    except Exception as e:
        current_app.logger.error(f"Error deleting history entries: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/cleanup', methods=['POST'])
def cleanup_history():
    """
    Manually trigger cleanup of history entries older than specified days.
    
    Query parameters:
    - days: Number of days threshold (default: 15)
    - auto: If 'true', run cleanup automatically without confirmation (default: false)
    """
    try:
        # Get parameters
        days_threshold = request.args.get('days', default=Config.HISTORY_CLEANUP_DAYS, type=int)
        auto_mode = request.args.get('auto', default='false').lower() == 'true'
        
        # Validate days threshold
        if days_threshold < 1:
            return jsonify(ResponseUtils.create_error_response('Days threshold must be at least 1')), 400
        
        # Run cleanup
        history_service = HistoryService()
        removed_count, remaining_count = history_service.cleanup_old_history(
            days_threshold=days_threshold
        )
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'History cleanup completed successfully',
            'removed_count': removed_count,
            'remaining_count': remaining_count,
            'days_threshold': days_threshold,
            'timestamp': DateTimeUtils.get_current_iso_timestamp()
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error cleaning up history: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/manual-video', methods=['POST'])
def add_manual_video():
    """
    Add a manual video entry for videos that were successfully created on Kie
    but didn't trigger callbacks to the app.
    """
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        task_id = data.get('task_id')
        video_url = data.get('video_url')
        
        if not task_id:
            return jsonify(ResponseUtils.create_error_response('task_id is required')), 400
        if not video_url:
            return jsonify(ResponseUtils.create_error_response('video_url is required')), 400
        
        # Optional parameters
        author = data.get('author', '')
        domain_name = data.get('domain_name', '')
        
        # Create a video callback entry
        callback_service = CallbackService()
        history_entry = callback_service.create_manual_video_entry(
            task_id=task_id,
            video_url=video_url,
            author=author,
            domain_name=domain_name
        )
        
        # Add to history
        history_service = HistoryService()
        if history_service.add_to_history(history_entry):
            current_app.logger.info(f"Manual video entry added for task: {task_id}")
            return jsonify(ResponseUtils.create_success_response({
                'message': 'Manual video entry added successfully',
                'entry_id': history_entry['id'],
                'task_id': task_id,
                'video_url': video_url
            }))
        else:
            return jsonify(ResponseUtils.create_error_response(
                'Failed to add manual video entry to history'
            )), 500
            
    except Exception as e:
        current_app.logger.error(f"Error adding manual video entry: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@history_api_bp.route('/stats', methods=['GET'])
def get_history_stats():
    """Get statistics about history entries."""
    try:
        history_service = HistoryService()
        stats = history_service.get_history_stats()
        
        return jsonify(ResponseUtils.create_success_response({
            'stats': stats
        }))
    except Exception as e:
        current_app.logger.error(f"Error getting history stats: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500