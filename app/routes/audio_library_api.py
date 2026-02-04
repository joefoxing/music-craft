"""
Audio Library API routes for the Music Cover Generator application.
Contains endpoints for managing user audio library operations.
"""
from flask import Blueprint, request, jsonify, current_app

from app.core.utils import ResponseUtils
from app.services.audio_library_service import AudioLibraryService


audio_library_bp = Blueprint('audio_library_api', __name__, url_prefix='/api/audio-library')


@audio_library_bp.route('', methods=['OPTIONS'])
def handle_audio_library_options():
    """Handle CORS preflight requests for audio library endpoints."""
    response = jsonify({'status': 'ok'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@audio_library_bp.route('', methods=['GET'])
def get_audio_library():
    """Get user's audio library with pagination and filtering."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        search = request.args.get('search')
        
        # Build filters
        filters = {}
        if request.args.get('genre'):
            filters['genre'] = request.args.get('genre')
        if request.args.get('year'):
            filters['year'] = int(request.args.get('year'))
        if request.args.get('source_type'):
            filters['source_type'] = request.args.get('source_type')
        if request.args.get('is_favorite'):
            filters['is_favorite'] = request.args.get('is_favorite').lower() == 'true'

        if request.args.get('playlist_id'):
            filters['playlist_id'] = request.args.get('playlist_id')
        
        # Get tags filter (multiple values)
        tags = request.args.getlist('tag')
        if tags:
            filters['tags'] = tags
        
        # Initialize service and get library
        service = AudioLibraryService()
        audio_items, total_count = service.get_user_audio_library(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters
        )
        
        # Convert to dictionaries
        audio_data = [item.to_dict() for item in audio_items]
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify(ResponseUtils.create_success_response({
            'audio_library': audio_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters_applied': filters,
            'search_query': search
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting audio library: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/<audio_id>', methods=['GET'])
def get_audio_item(audio_id):
    """Get a specific audio item from library."""
    try:
        service = AudioLibraryService()
        audio_item = service.get_audio_item(audio_id)
        
        if not audio_item:
            return jsonify(ResponseUtils.create_error_response('Audio item not found')), 404
        
        return jsonify(ResponseUtils.create_success_response({
            'audio_item': audio_item.to_dict(include_relationships=True)
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting audio item {audio_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('', methods=['POST'])
def add_to_library():
    """Add audio to user's library."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        service = AudioLibraryService()
        success, error_message, audio_item = service.add_to_library(data)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'audio_item': audio_item.to_dict(),
            'message': 'Audio added to library successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error adding audio to library: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/<audio_id>', methods=['PUT'])
def update_audio_item(audio_id):
    """Update an audio item in library."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        service = AudioLibraryService()
        success, error_message = service.update_audio_item(audio_id, data)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Audio item updated successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error updating audio item {audio_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/<audio_id>', methods=['DELETE'])
def delete_audio_item(audio_id):
    """Delete an audio item from library."""
    try:
        service = AudioLibraryService()
        success, error_message = service.delete_audio_item(audio_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Audio item deleted successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting audio item {audio_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/<audio_id>/play', methods=['POST'])
def increment_play_count(audio_id):
    """Increment play count for an audio item."""
    try:
        service = AudioLibraryService()
        success = service.increment_play_count(audio_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response('Audio item not found')), 404
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Play count incremented'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error incrementing play count for {audio_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/<audio_id>/favorite', methods=['POST'])
def toggle_favorite(audio_id):
    """Toggle favorite status for an audio item."""
    try:
        service = AudioLibraryService()
        success, error_message, is_favorite = service.toggle_favorite(audio_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'is_favorite': is_favorite,
            'message': f'{"Added to" if is_favorite else "Removed from"} favorites'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error toggling favorite for {audio_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/stats', methods=['GET'])
def get_library_stats():
    """Get statistics about user's audio library."""
    try:
        service = AudioLibraryService()
        stats = service.get_library_stats()
        
        return jsonify(ResponseUtils.create_success_response({
            'stats': stats
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting library stats: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/add-from-history', methods=['POST'])
def add_from_history():
    """Add audio from history entry to library."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        service = AudioLibraryService()
        success, error_message, audio_item = service.add_from_history(data)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'audio_item': audio_item.to_dict(),
            'message': 'Audio added from history successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error adding audio from history: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


# Playlist endpoints
@audio_library_bp.route('/playlists', methods=['GET'])
def get_playlists():
    """Get user's playlists."""
    try:
        service = AudioLibraryService()
        playlists = service.get_user_playlists()
        
        playlist_data = [playlist.to_dict() for playlist in playlists]
        
        return jsonify(ResponseUtils.create_success_response({
            'playlists': playlist_data
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting playlists: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/playlists', methods=['POST'])
def create_playlist():
    """Create a new playlist."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        name = data.get('name')
        if not name:
            return jsonify(ResponseUtils.create_error_response('Playlist name is required')), 400
        
        description = data.get('description')
        
        service = AudioLibraryService()
        success, error_message, playlist = service.create_playlist(name, description)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'playlist': playlist.to_dict(),
            'message': 'Playlist created successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error creating playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/playlists/<playlist_id>/add', methods=['POST'])
def add_to_playlist(playlist_id):
    """Add audio item to playlist."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        audio_id = data.get('audio_id')
        if not audio_id:
            return jsonify(ResponseUtils.create_error_response('Audio ID is required')), 400
        
        service = AudioLibraryService()
        success, error_message = service.add_to_playlist(playlist_id, audio_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Audio added to playlist successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error adding audio to playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/playlists/<playlist_id>/remove', methods=['POST'])
def remove_from_playlist(playlist_id):
    """Remove audio item from playlist."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        audio_id = data.get('audio_id')
        if not audio_id:
            return jsonify(ResponseUtils.create_error_response('Audio ID is required')), 400
        
        service = AudioLibraryService()
        success, error_message = service.remove_from_playlist(playlist_id, audio_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Audio removed from playlist successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error removing audio from playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@audio_library_bp.route('/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a playlist."""
    try:
        service = AudioLibraryService()
        success, error_message = service.delete_playlist(playlist_id)
        
        if not success:
            return jsonify(ResponseUtils.create_error_response(error_message)), 400
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Playlist deleted successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting playlist {playlist_id}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500