"""
Main routes for the Music Cover Generator application.
Contains basic page routes and file upload handling.
"""
from flask import Blueprint, request, jsonify, render_template, current_app, url_for, send_file, abort, redirect
from flask_login import login_required, current_user
import os
import re

from app.config import Config
from app.core.utils import FileUtils, ResponseUtils, DateTimeUtils
from app.core.validation import ParameterValidator
from app.services.audio_library_service import AudioLibraryService


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Render the main landing page."""
    return render_template('index.html')


@main_bp.route('/login')
def login_redirect():
    """Redirect /login to /auth/login."""
    return redirect(url_for('auth.login'))


@main_bp.route('/register')
def register_redirect():
    """Redirect /register to /auth/register."""
    return redirect(url_for('auth.register'))


@main_bp.route('/cover-generator')
@login_required
def cover_generator():
    """Render the cover generator page."""
    return render_template('cover-generator.html', active_nav='cover-generator')


@main_bp.route('/mashup')
@login_required
def mashup_page():
    """Render the mashup generator page."""
    return render_template('mashup.html', active_nav='mashup')


@main_bp.route('/lyrics-extraction')
def lyrics_extraction():
    """Render the lyrics extraction page."""
    return render_template('lyrics-extraction.html', active_nav='lyrics-extraction')


@main_bp.route('/music-generator')
@login_required
def music_generator():
    """Render the music generator page."""
    return render_template('music_generator.html', active_nav='music-generator')


@main_bp.route('/history')
@login_required
def history():
    """Render the callback history page."""
    return render_template('history.html', active_nav='history')


@main_bp.route('/library')
@login_required
def library():
    """Render the music library page."""
    return render_template('library.html', active_nav='library')


@main_bp.route('/playlist/<playlist_id>')
@login_required
def view_playlist(playlist_id):
    """Render the library page filtered by playlist."""
    return render_template('library.html', active_nav='library', playlist_id=playlist_id)


@main_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.has_permission('view_admin'):
        abort(403)
    from app.models import User
    active_pro_count  = User.query.filter_by(subscription_status='active',  subscription_tier='pro').count()
    past_due_count    = User.query.filter_by(subscription_status='past_due').count()
    free_user_count   = User.query.filter_by(subscription_tier='free').count()
    users_with_tokens = User.query.filter(User.token_balance > 0).count()
    return render_template(
        'admin.html',
        active_nav='admin',
        active_pro_count=active_pro_count,
        past_due_count=past_due_count,
        free_user_count=free_user_count,
        users_with_tokens=users_with_tokens,
    )


@main_bp.route('/admin/dashboard')
@login_required
def admin_billing_dashboard():
    if not current_user.has_permission('view_admin'):
        abort(403)
    from app.models import User
    active_pro_count  = User.query.filter_by(subscription_status='active',  subscription_tier='pro').count()
    past_due_count    = User.query.filter_by(subscription_status='past_due').count()
    free_user_count   = User.query.filter_by(subscription_tier='free').count()
    users_with_tokens = User.query.filter(User.token_balance > 0).count()
    return render_template(
        'admin/dashboard.html',
        active_nav='admin',
        active_pro_count=active_pro_count,
        past_due_count=past_due_count,
        free_user_count=free_user_count,
        users_with_tokens=users_with_tokens,
    )


@main_bp.route('/add-instrumental')
@login_required
def add_instrumental():
    """Render the add instrumental page."""
    public_base_url = Config.get_public_base_url(request)
    return render_template('add-instrumental.html', active_nav='add-instrumental', public_base_url=public_base_url)


@main_bp.route('/add-vocal')
@login_required
def add_vocal():
    """Render the add vocal page."""
    public_base_url = Config.get_public_base_url(request)
    return render_template('add-vocal.html', active_nav='add-vocal', public_base_url=public_base_url)


@main_bp.route('/vocal-removal')
@login_required
def vocal_removal():
    """Render the vocal removal page."""
    public_base_url = Config.get_public_base_url(request)
    return render_template('vocal-removal.html', active_nav='vocal-removal', public_base_url=public_base_url)


@main_bp.route('/replace-section')
@login_required
def replace_section_page():
    """Render the Replace Music Section page."""
    public_base_url = Config.get_public_base_url(request)
    prefill_task_id  = request.args.get('taskId', '')
    prefill_audio_id = request.args.get('audioId', '')
    return render_template(
        'replace-section.html',
        active_nav='replace-section',
        public_base_url=public_base_url,
        prefill_task_id=prefill_task_id,
        prefill_audio_id=prefill_audio_id,
    )


@main_bp.route('/voice')
@login_required
def voice_conversion():
    """Render the voice conversion page."""
    return render_template('voice-conversion.html', active_nav='voice-conversion')


@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle audio file upload."""
    if 'file' not in request.files:
        return jsonify(ResponseUtils.create_error_response('No file part')), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify(ResponseUtils.create_error_response('No selected file')), 400
    
    # Validate file
    is_valid, error_msg = ParameterValidator.validate_filename(file.filename)
    if not is_valid:
        return jsonify(ResponseUtils.create_error_response(error_msg)), 400
    
    requested_lyrics_language = (request.form.get('lyrics_language') or '').strip().lower()
    if requested_lyrics_language and not re.fullmatch(r'[a-z]{2,3}(?:-[a-z]{2,4})?', requested_lyrics_language):
        return jsonify(ResponseUtils.create_error_response('Invalid lyrics language code')), 400

    # Generate unique filename
    unique_filename = FileUtils.generate_unique_filename(file.filename)
    
    # Save file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Create URL for the uploaded file
    # Use our dedicated audio serving endpoint for better control
    # Use public base URL for external API access
    public_base_url = Config.get_public_base_url(request)
    file_url = f"{public_base_url}/serve-audio/{unique_filename}"

    # Immediately add uploaded file to user's audio library so lyrics extraction starts right away.
    # Allow opt-out for specific flows by setting form field auto_add_to_library=false.
    auto_add_to_library = request.form.get('auto_add_to_library', 'true').lower() == 'true'
    audio_item_payload = None
    if auto_add_to_library:
        try:
            service = AudioLibraryService()
            base_title = os.path.splitext(file.filename)[0] if file.filename else 'Uploaded Audio'
            file_ext = os.path.splitext(file.filename or '')[1].lower().lstrip('.')
            library_data = {
                'title': base_title,
                'artist': current_user.display_name if getattr(current_user, 'display_name', None) else 'Unknown Artist',
                'file_size': os.path.getsize(file_path),
                'file_format': file_ext,
                'audio_url': file_url,
                'original_filename': file.filename,
                'source_type': 'upload',
                'processing_status': 'ready',
                'extract_lyrics': True,
                'lyrics_language': requested_lyrics_language or None
            }

            success, error_message, audio_item = service.add_to_library(library_data)
            if success and audio_item:
                audio_item_payload = audio_item.to_dict()
            else:
                current_app.logger.warning(f"Upload succeeded but add_to_library failed: {error_message}")
        except Exception as exc:
            current_app.logger.warning(f"Upload succeeded but failed to enqueue lyrics extraction: {exc}")
    
    return jsonify(ResponseUtils.create_success_response({
        'filename': unique_filename,
        'original_filename': file.filename,
        'file_url': file_url,
        'file_path': file_path,
        'audio_item': audio_item_payload
    }, 'File uploaded successfully'))


@main_bp.route('/serve-audio/<filename>', methods=['GET', 'OPTIONS'])
def serve_audio(filename):
    """
    Serve uploaded audio files with proper headers.
    This endpoint provides better control over file serving than static files.
    """
    if request.method == 'OPTIONS':
        # Handle CORS preflight requests
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        # Security check: ensure filename is safe
        if '..' in filename or filename.startswith('/'):
            return jsonify(ResponseUtils.create_error_response('Invalid filename')), 400
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify(ResponseUtils.create_error_response('File not found')), 404
        
        # Determine MIME type based on file extension
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac'
        }
        
        ext = os.path.splitext(filename)[1].lower()
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # Serve file with proper headers
        response = send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False,  # Don't force download
            download_name=filename
        )
        
        # Add CORS headers to allow cross-origin requests (for Kie API)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        # Cache control headers
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving audio file {filename}: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@main_bp.route('/profile')
@login_required
def profile_redirect():
    """Redirect to auth profile page."""
    from flask import redirect, url_for
    return redirect(url_for('auth.profile'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard page."""
    from datetime import datetime
    hour = datetime.now().hour
    return render_template('dashboard.html', active_nav='dashboard', greeting_hour=hour)