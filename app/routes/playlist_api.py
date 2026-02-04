from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Playlist, PlaylistGenerationJob, AudioLibrary, PlaylistAudioLibrary
from app.core.utils import ResponseUtils
from app.services.template_service import TemplateService
import uuid

playlist_api_bp = Blueprint('playlist_api', __name__, url_prefix='/api/playlists')

@playlist_api_bp.route('', methods=['GET'])
@login_required
def get_playlists():
    """Get all playlists for the current user."""
    try:
        playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.updated_at.desc()).all()
        return jsonify(ResponseUtils.create_success_response({
            'playlists': [p.to_dict(include_audio_items=False) for p in playlists]
        }))
    except Exception as e:
        current_app.logger.error(f"Error fetching playlists: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500

@playlist_api_bp.route('', methods=['POST'])
@login_required
def create_playlist():
    """Create a new playlist. Supports standard and smart generation."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400

        name = data.get('name')
        if not name:
            return jsonify(ResponseUtils.create_error_response('Name is required')), 400

        # Extract smart playlist parameters
        generation_type = data.get('generation_type', 'manual') # manual, prompt, template, infinite
        generation_prompt = data.get('generation_prompt')
        template_id = data.get('template_id')
        
        # Validate smart playlist params
        if generation_type in ['prompt', 'template']:
            if generation_type == 'prompt' and not generation_prompt:
                 return jsonify(ResponseUtils.create_error_response('generation_prompt is required for prompt-based playlists')), 400
            if generation_type == 'template' and not template_id:
                 return jsonify(ResponseUtils.create_error_response('template_id is required for template-based playlists')), 400

        playlist = Playlist(
            user_id=current_user.id,
            name=name,
            description=data.get('description'),
            cover_image_url=data.get('cover_image_url'),
            is_public=data.get('is_public', False)
        )
        
        # Set smart playlist metadata
        if generation_type != 'manual':
            playlist.is_generated = True
            playlist.generation_type = generation_type
            playlist.generation_prompt = generation_prompt
            playlist.template_id = template_id

        db.session.add(playlist)
        db.session.flush() # Get ID

        # Trigger generation job if needed
        job_data = None
        if playlist.is_generated:
            job = PlaylistGenerationJob(
                user_id=current_user.id,
                playlist_id=playlist.id,
                status='pending',
                prompt=generation_prompt,
                template_id=template_id
            )
            db.session.add(job)
            db.session.flush()
            job_data = job.to_dict()
            
            # Here we would trigger the async worker
            # For Phase 1, we just create the record
            
            # If template based, we might want to validate the template immediately using Service
            if generation_type == 'template':
                try:
                    template_service = TemplateService()
                    # In a real app, we'd fetch the template JSON from a DB or file based on ID
                    # mocked_template = template_service.get_template(template_id)
                    # template_service.parse_template(mocked_template)
                    pass
                except Exception as e:
                    return jsonify(ResponseUtils.create_error_response(f"Invalid template: {str(e)}")), 400

        db.session.commit()

        response_data = {
            'playlist': playlist.to_dict(),
        }
        if job_data:
            response_data['generation_job'] = job_data

        return jsonify(ResponseUtils.create_success_response(response_data, "Playlist created successfully"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500

@playlist_api_bp.route('/<playlist_id>', methods=['GET'])
@login_required
def get_playlist(playlist_id):
    """Get a specific playlist by ID."""
    try:
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify(ResponseUtils.create_error_response('Playlist not found')), 404
        
        # Check access (owner or public)
        if playlist.user_id != current_user.id and not playlist.is_public:
            return jsonify(ResponseUtils.create_error_response('Access denied', 403)), 403
            
        return jsonify(ResponseUtils.create_success_response({
            'playlist': playlist.to_dict(include_audio_items=True)
        }))
    except Exception as e:
        current_app.logger.error(f"Error fetching playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500

@playlist_api_bp.route('/<playlist_id>', methods=['PUT'])
@login_required
def update_playlist(playlist_id):
    """Update a playlist."""
    try:
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify(ResponseUtils.create_error_response('Playlist not found')), 404
            
        if playlist.user_id != current_user.id:
            return jsonify(ResponseUtils.create_error_response('Access denied', 403)), 403
            
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
            
        if 'name' in data:
            playlist.name = data['name']
        if 'description' in data:
            playlist.description = data['description']
        if 'is_public' in data:
            playlist.is_public = data['is_public']
        if 'cover_image_url' in data:
            playlist.cover_image_url = data['cover_image_url']
            
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'playlist': playlist.to_dict()
        }, "Playlist updated successfully"))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500

@playlist_api_bp.route('/<playlist_id>', methods=['DELETE'])
@login_required
def delete_playlist(playlist_id):
    """Delete a playlist."""
    try:
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify(ResponseUtils.create_error_response('Playlist not found')), 404
            
        if playlist.user_id != current_user.id:
            return jsonify(ResponseUtils.create_error_response('Access denied', 403)), 403
            
        db.session.delete(playlist)
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response(None, "Playlist deleted successfully"))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting playlist: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500
