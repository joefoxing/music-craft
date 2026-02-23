from flask import Blueprint, request, jsonify, render_template, current_app, url_for
import os
import uuid
import datetime
import json
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app.kie_client import KieAPIClient
from app.config import Config

main_bp = Blueprint('main', __name__)

def get_public_base_url():
    """Get public base URL."""
    return Config.get_public_base_url(request)

def is_safe_url(url):
    """
    Check if the URL is safe to access (SSRF protection).
    Allowed domains: kie.ai, suno.ai and their subdomains.
    """
    if not url:
        return False
        
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # List of allowed base domains
        allowed_domains = {
            'kie.ai', 
            'musicfile.kie.ai',
            'api.kie.ai',
            'suno.ai', 
            'cdn1.suno.ai', 
            'cdn2.suno.ai',
            'images.unsplash.com', # Used for covers
            'www.soundhelix.com'   # Used in mocks
        }
        
        # Check if domain matches or is a subdomain of allowed domains
        for allowed in allowed_domains:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
                
        return False
    except Exception:
        return False

@main_bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@main_bp.route('/cover-generator')
def cover_generator():
    """Render the cover generator page."""
    return render_template('cover-generator.html')

@main_bp.route('/lyrics-extraction')
def lyrics_extraction():
    """Render the lyrics extraction page."""
    return render_template('lyrics-extraction.html')

@main_bp.route('/history')
def history():
    """Render the callback history page."""
    return render_template('history.html')

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle audio file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not Config.is_extension_allowed(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(Config.get_allowed_extensions())}'}), 400
    
    # Check file size
    max_upload_size = current_app.config.get('MAX_UPLOAD_SIZE')
    if max_upload_size:
        # Get file size by seeking to end
        file.seek(0, 2)  # seek to end of file
        file_size = file.tell()
        file.seek(0)     # rewind to beginning
        if file_size > max_upload_size:
            return jsonify({'error': f'File size exceeds limit of {max_upload_size // (1024*1024)} MB'}), 413
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    file_extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    
    # Save file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Create URL for the uploaded file
    # Use our dedicated audio serving endpoint for better control
    # Use public base URL for external API access
    public_base_url = get_public_base_url()
    file_url = f"{public_base_url}/serve-audio/{unique_filename}"
    
    return jsonify({
        'success': True,
        'filename': unique_filename,
        'original_filename': original_filename,
        'file_url': file_url,
        'file_path': file_path
    })

@main_bp.route('/api/generate-music', methods=['POST'])
def generate_music():
    """Generate music without login required - unauthenticated generation."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        # Optional parameters with defaults
        model = data.get('model', 'V5')
        instrumental = data.get('instrumental', False)
        custom_mode = data.get('custom_mode', False)
        style = data.get('style')
        title = data.get('title')
        
        # Validate prompt length
        if len(prompt) > 5000:
            return jsonify({'error': 'Prompt is too long (max 5000 characters)'}), 400
        
        # Get callback URL
        public_base_url = get_public_base_url()
        call_back_url = f"{public_base_url}/callback"
        
        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters
        is_valid, error_msg = client.validate_parameters(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model
        )
        
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Call Kie API directly for music generation
        response = client.generate_music_direct(
            custom_mode=custom_mode,
            instrumental=instrumental,
            call_back_url=call_back_url,
            model=model,
            prompt=prompt,
            style=style,
            title=title
        )

        # Record a pending history entry as soon as the job is submitted so it
        # appears in the history page immediately (before the callback arrives).
        task_id = (response.get('data') or {}).get('taskId')
        if task_id:
            try:
                pending_entry = {
                    'id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'callback_type': 'pending',
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'status_code': None,
                    'status_message': 'Generation in progress',
                    'status': 'pending',
                    'is_video_callback': False,
                    'tracks_count': 0,
                    'has_audio_urls': False,
                    'has_image_urls': False,
                    'generation_params': {
                        'type': 'music',
                        'prompt': prompt,
                        'model': model,
                        'instrumental': instrumental,
                        'custom_mode': custom_mode,
                        'style': style,
                        'title': title,
                    }
                }
                add_to_history(pending_entry)
                current_app.logger.info(f"Pending history entry created for music task: {task_id}")
            except Exception as he:
                current_app.logger.warning(f"Failed to create pending history entry: {he}")

        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/generate-cover', methods=['POST'])
def generate_cover():
    """Generate music cover using Kie API."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        upload_url = data.get('upload_url')
        prompt = data.get('prompt')
        custom_mode = data.get('custom_mode', False)
        instrumental = data.get('instrumental', False)
        model = data.get('model', 'V5')
        
        if not upload_url:
            return jsonify({'error': 'upload_url is required'}), 400
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        # Optional parameters
        style = data.get('style')
        title = data.get('title')
        call_back_url = data.get('call_back_url')
        
        # Optional advanced parameters
        optional_params = {
            'negativeTags': data.get('negative_tags'),
            'vocalGender': data.get('vocal_gender'),
            'styleWeight': data.get('style_weight'),
            'weirdnessConstraint': data.get('weirdness_constraint'),
            'audioWeight': data.get('audio_weight'),
            'personaId': data.get('persona_id')
        }
        
        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters
        is_valid, error_msg = client.validate_parameters(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model
        )
        
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Call Kie API
        response = client.upload_and_cover_audio(
            upload_url=upload_url,
            prompt=prompt,
            custom_mode=custom_mode,
            instrumental=instrumental,
            model=model,
            call_back_url=call_back_url,
            style=style,
            title=title,
            **optional_params
        )

        # Record a pending history entry immediately upon job submission.
        task_id = (response.get('data') or {}).get('taskId')
        if task_id:
            try:
                pending_entry = {
                    'id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'callback_type': 'pending',
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'status_code': None,
                    'status_message': 'Cover generation in progress',
                    'status': 'pending',
                    'is_video_callback': False,
                    'tracks_count': 0,
                    'has_audio_urls': False,
                    'has_image_urls': False,
                    'generation_params': {
                        'type': 'cover',
                        'prompt': prompt,
                        'model': model,
                        'instrumental': instrumental,
                        'custom_mode': custom_mode,
                        'style': style,
                        'title': title,
                        'upload_url': upload_url,
                    }
                }
                add_to_history(pending_entry)
                current_app.logger.info(f"Pending history entry created for cover task: {task_id}")
            except Exception as he:
                current_app.logger.warning(f"Failed to create pending history entry: {he}")

        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating cover: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/generate-music-video', methods=['POST'])
def generate_music_video():
    """Generate music video using Kie API."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        task_id = data.get('task_id')
        audio_id = data.get('audio_id')
        
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400
        if not audio_id:
            return jsonify({'error': 'audio_id is required'}), 400
        
        # Optional parameters
        author = data.get('author')
        domain_name = data.get('domain_name')
        
        # Get callback URL
        public_base_url = get_public_base_url()
        call_back_url = f"{public_base_url}/callback"
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API to generate music video
        response = client.generate_music_video(
            task_id=task_id,
            audio_id=audio_id,
            call_back_url=call_back_url,
            author=author,
            domain_name=domain_name
        )
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music video: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a generation task."""
    try:
        current_app.logger.info(f"Getting task status for task_id: {task_id}")
        client = KieAPIClient()
        status = client.get_task_status(task_id)
        current_app.logger.info(f"Task status response received for {task_id}")
        return jsonify(status)
    except Exception as e:
        current_app.logger.error(f"Error getting task status: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/video-status/<video_task_id>', methods=['GET'])
def get_video_status(video_task_id):
    """Get status of a video generation task from history."""
    try:
        current_app.logger.info(f"Getting video status for video_task_id: {video_task_id}")
        
        # Load history to find video callbacks
        history = load_history()
        
        # Find video callbacks for this task
        video_callbacks = []
        for entry in history:
            if entry.get('task_id') == video_task_id and entry.get('is_video_callback', False):
                video_callbacks.append(entry)
        
        if video_callbacks:
            # Sort by timestamp (newest first)
            video_callbacks.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            latest_callback = video_callbacks[0]
            
            # Extract video URL if available
            video_url = latest_callback.get('video_url')
            status_code = latest_callback.get('status_code')
            status_message = latest_callback.get('status_message')
            
            return jsonify({
                'success': True,
                'video_task_id': video_task_id,
                'status': 'complete' if status_code in [0, 200] else 'processing',
                'status_code': status_code,
                'status_message': status_message,
                'video_url': video_url,
                'has_video': video_url is not None,
                'last_callback_time': latest_callback.get('timestamp'),
                'callbacks_count': len(video_callbacks)
            })
        else:
            # Check if there's a video task in progress (no callbacks yet)
            # We could also check with Kie API if we had a video status endpoint
            return jsonify({
                'success': True,
                'video_task_id': video_task_id,
                'status': 'processing',
                'status_code': None,
                'status_message': 'Video generation in progress',
                'video_url': None,
                'has_video': False,
                'last_callback_time': None,
                'callbacks_count': 0
            })
            
    except Exception as e:
        current_app.logger.error(f"Error getting video status: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/models', methods=['GET'])
def get_models():
    """Get available model versions and their constraints."""
    models = {
        'V5': {
            'name': 'V5',
            'description': 'Superior musical expression, faster generation',
            'limits': {
                'prompt': 5000,
                'style': 1000,
                'title': 100
            }
        },
        'V4_5PLUS': {
            'name': 'V4_5PLUS',
            'description': 'V4.5+ delivers richer sound, new ways to create, max 8 min',
            'limits': {
                'prompt': 5000,
                'style': 1000,
                'title': 100
            }
        },
        'V4_5': {
            'name': 'V4_5',
            'description': 'V4.5 enables smarter prompts, faster generations, max 8 min',
            'limits': {
                'prompt': 5000,
                'style': 1000,
                'title': 100
            }
        },
        'V4_5ALL': {
            'name': 'V4_5ALL',
            'description': 'V4.5ALL enables smarter prompts, faster generations, max 8 min',
            'limits': {
                'prompt': 5000,
                'style': 1000,
                'title': 80
            }
        },
        'V4': {
            'name': 'V4',
            'description': 'V4 improves vocal quality, max 4 min',
            'limits': {
                'prompt': 3000,
                'style': 200,
                'title': 80
            }
        }
    }
    
    return jsonify(models)

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
            return jsonify({'error': 'Invalid filename'}), 400
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
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
        from flask import send_file
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
        return jsonify({'error': str(e)}), 500

# Callback processing functions
def process_callback_data(callback_data):
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

# History management functions
def get_history_file_path():
    """Get the path to the history JSON file."""
    history_dir = os.path.join(current_app.root_path, 'static', 'history')
    os.makedirs(history_dir, exist_ok=True)
    return os.path.join(history_dir, 'history.json')

def load_history():
    """Load history data from JSON file."""
    history_file = get_history_file_path()
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.error(f"Error loading history file: {e}")
            return []
    return []

def save_history(history_data):
    """Save history data to JSON file."""
    history_file = get_history_file_path()
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, default=str)
        return True
    except IOError as e:
        current_app.logger.error(f"Error saving history file: {e}")
        return False

def add_to_history(entry):
    """Add a new entry to history."""
    history = load_history()
    
    # Ensure entry has required fields
    if 'id' not in entry:
        entry['id'] = str(uuid.uuid4())
    if 'timestamp' not in entry:
        entry['timestamp'] = datetime.datetime.utcnow().isoformat()
    
    # Add to beginning of list (most recent first)
    history.insert(0, entry)
    
    # Keep only last 100 entries to prevent file from growing too large
    if len(history) > 100:
        history = history[:100]
    
    # Save the history
    if save_history(history):
        # Run cleanup of old entries (older than 15 days) periodically
        # We'll run cleanup every 10th entry to avoid performance issues
        if len(history) % 10 == 0:
            try:
                cleanup_old_history(days_threshold=15)
            except Exception as e:
                current_app.logger.warning(f"Failed to run history cleanup: {e}")
        return True
    return False

def update_history_entry(task_id, updates):
    """Update an existing history entry by task_id."""
    history = load_history()
    updated = False
    
    for entry in history:
        if entry.get('task_id') == task_id:
            entry.update(updates)
            entry['last_updated'] = datetime.datetime.utcnow().isoformat()
            updated = True
            break
    
    if updated:
        return save_history(history)
    return False

def upsert_history_entry(entry):
    """
    Update an existing history entry for the same task_id (if in a transient state)
    or insert a new one.

    A 'pending' or 'processing' entry created at submission time will be replaced
    in-place by the first callback so the history list stays clean (one row per job).
    If no existing transient entry is found a new row is prepended.
    """
    history = load_history()

    # Ensure required fields are present
    if 'id' not in entry:
        entry['id'] = str(uuid.uuid4())
    if 'timestamp' not in entry:
        entry['timestamp'] = datetime.datetime.utcnow().isoformat()

    task_id = entry.get('task_id')
    if task_id:
        for i, existing in enumerate(history):
            if existing.get('task_id') == task_id and existing.get('status') in ('pending', 'processing'):
                # Preserve original submission timestamp and id
                entry.setdefault('original_timestamp', existing.get('timestamp'))
                entry['id'] = existing['id']
                entry['last_updated'] = datetime.datetime.utcnow().isoformat()
                history[i] = entry
                return save_history(history)

    # No transient entry found – prepend as a new record
    history.insert(0, entry)
    if len(history) > 100:
        history = history[:100]
    if save_history(history):
        if len(history) % 10 == 0:
            try:
                cleanup_old_history(days_threshold=15)
            except Exception as e:
                current_app.logger.warning(f"Failed to run history cleanup: {e}")
        return True
    return False

def cleanup_old_history(days_threshold=15):
    """
    Remove history entries older than the specified number of days.
    
    Args:
        days_threshold (int): Number of days after which entries should be removed.
    
    Returns:
        tuple: (removed_count, total_count_after_cleanup)
    """
    history = load_history()
    if not history:
        return 0, 0
    
    # Calculate cutoff time
    cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=days_threshold)
    
    # Filter entries newer than cutoff
    filtered_history = []
    removed_count = 0
    
    for entry in history:
        timestamp_str = entry.get('timestamp')
        if not timestamp_str:
            # If no timestamp, keep the entry (shouldn't happen)
            filtered_history.append(entry)
            continue
        
        try:
            # Parse timestamp string to datetime
            if 'T' in timestamp_str:
                # ISO format with T separator
                entry_time = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Try parsing as simple string
                entry_time = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Check if entry is older than cutoff
            if entry_time >= cutoff_time:
                filtered_history.append(entry)
            else:
                removed_count += 1
                current_app.logger.info(f"Removing old history entry: {entry.get('id')} from {timestamp_str}")
        except (ValueError, TypeError) as e:
            # If parsing fails, keep the entry
            current_app.logger.warning(f"Could not parse timestamp '{timestamp_str}' for entry {entry.get('id')}: {e}")
            filtered_history.append(entry)
    
    # Save filtered history
    if save_history(filtered_history):
        current_app.logger.info(f"History cleanup removed {removed_count} entries older than {days_threshold} days. {len(filtered_history)} entries remain.")
        return removed_count, len(filtered_history)
    else:
        current_app.logger.error("Failed to save history after cleanup")
        return 0, len(history)

# Download URL API - Keep for backward compatibility but improve it
@main_bp.route('/api/download-url', methods=['POST'])
def get_download_url():
    """Get a downloadable URL for kie.ai generated files."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Check if URL is from kie.ai services
        if not ('musicfile.kie.ai' in url or 'kie.ai' in url or 'cdn1.suno.ai' in url or 'cdn2.suno.ai' in url):
            return jsonify({
                'error': 'Only kie.ai/suno.ai generated file URLs are supported',
                'code': 422
            }), 422
        
        # Initialize API client
        client = KieAPIClient()
        
        # Make request to kie.ai download URL API
        endpoint = f"{client.base_url}/api/v1/common/download-url"
        
        # Use the same headers as other API calls
        response = requests.post(
            endpoint,
            headers=client.headers,
            json={'url': url},
            timeout=15
        )
        
        current_app.logger.info(f"Download URL API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            current_app.logger.info(f"Download URL API response: {json.dumps(result, indent=2)}")
            return jsonify(result)
        else:
            # If kie.ai API fails, try to get the file directly
            current_app.logger.warning(f"Kie.ai download API failed with {response.status_code}, trying direct download")
            
            # Check if it's a suno.ai CDN URL (these might work directly)
            if 'cdn1.suno.ai' in url or 'cdn2.suno.ai' in url:
                return jsonify({
                    'code': 200,
                    'msg': 'success',
                    'data': url  # Return the original URL for direct download
                })
            
            # Return the error from kie.ai API
            try:
                error_data = response.json()
                return jsonify(error_data), response.status_code
            except:
                return jsonify({
                    'error': f'Failed to get download URL: {response.status_code}',
                    'code': response.status_code
                }), response.status_code
            
    except Exception as e:
        current_app.logger.error(f"Error getting download URL: {e}")
        return jsonify({'error': str(e)}), 500

# Direct audio download endpoint - handles downloads behind the scenes
@main_bp.route('/api/download-audio', methods=['POST'])
def download_audio():
    """Download audio file from kie.ai/suno.ai and stream it to user."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        url = data.get('url')
        filename = data.get('filename', 'audio.mp3')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'Invalid URL format'}), 400
            
        # SSRF Protection: Check if URL is safe
        if not is_safe_url(url):
            current_app.logger.warning(f"Blocked potential SSRF attempt to URL: {url}")
            return jsonify({'error': 'URL not allowed'}), 403
        
        # Clean filename for safety
        filename = secure_filename(filename)
        if not filename.lower().endswith('.mp3'):
            filename += '.mp3'
        
        current_app.logger.info(f"Downloading audio from {url} as {filename}")
        
        # Set up headers for the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Add API key for kie.ai URLs if available
        if 'kie.ai' in url:
            client = KieAPIClient()
            if client.api_key and not client.use_mock:
                headers['Authorization'] = f'Bearer {client.api_key}'
        
        # Stream the download
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        if response.status_code != 200:
            current_app.logger.error(f"Failed to download audio: {response.status_code}")
            return jsonify({
                'error': f'Failed to download audio: HTTP {response.status_code}',
                'code': response.status_code
            }), response.status_code
        
        # Create a streaming response
        from flask import Response
        
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        # Determine content type
        content_type = response.headers.get('Content-Type', 'audio/mpeg')
        
        return Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': response.headers.get('Content-Length', ''),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except requests.exceptions.Timeout:
        current_app.logger.error("Download request timed out")
        return jsonify({'error': 'Download request timed out'}), 504
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Download request failed: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Error downloading audio: {e}")
        return jsonify({'error': str(e)}), 500

# Promoted Songs API
@main_bp.route('/api/songs/promoted', methods=['GET'])
def get_promoted_songs():
    """Get promoted creator songs from history."""
    try:
        # Load history
        history = load_history()
        
        # Filter for successful song generations that have tracks
        songs = []
        for entry in history:
            # Check if it's a completed generation
            # We want successful entries that are NOT video callbacks
            if entry.get('status') == 'success' and not entry.get('is_video_callback'):
                # Get tracks from processed_data
                processed_data = entry.get('processed_data', {})
                tracks = processed_data.get('tracks', [])
                
                # If we still don't have tracks, skip
                if not tracks:
                    continue

                for track in tracks:
                    # Construct song object compatible with PromotedSongs/CardFactory
                    # We need to ensure we have at least a title and audio URL
                    title = track.get('title')
                    audio_url = track.get('audio_urls', {}).get('generated')
                    
                    if not title or not audio_url:
                        continue
                        
                    song = {
                        'id': track.get('id'),
                        'title': title,
                        'artist': 'Creator', # Default to Creator as we don't track user names yet
                        'duration': track.get('duration'),
                        'cover_url': track.get('image_urls', {}).get('generated'),
                        'audio_url': audio_url,
                        'tags': track.get('tags'),
                        'model_name': track.get('model_name'),
                        'created_at': track.get('create_time')
                    }
                    songs.append(song)
        
        # Limit to 6 songs for the section
        songs = songs[:6]
        
        return jsonify({
            'success': True,
            'data': {
                'songs': songs
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting promoted songs: {e}")
        return jsonify({'success': False, 'msg': str(e)}), 500

# History API routes
@main_bp.route('/api/history', methods=['GET'])
def get_history():
    """Get all history entries."""
    try:
        history = load_history()
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/history/<entry_id>', methods=['GET'])
def get_history_entry(entry_id):
    """Get a specific history entry by ID."""
    try:
        history = load_history()
        for entry in history:
            if entry.get('id') == entry_id or entry.get('task_id') == entry_id:
                return jsonify({
                    'success': True,
                    'entry': entry
                })
        
        return jsonify({'error': 'History entry not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting history entry: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear all history entries."""
    try:
        empty_history = []
        if save_history(empty_history):
            return jsonify({
                'success': True,
                'message': 'History cleared successfully'
            })
        else:
            return jsonify({'error': 'Failed to clear history'}), 500
    except Exception as e:
        current_app.logger.error(f"Error clearing history: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/history/cleanup', methods=['POST'])
def cleanup_history():
    """
    Manually trigger cleanup of history entries older than specified days.
    
    Query parameters:
    - days: Number of days threshold (default: 15)
    - auto: If 'true', run cleanup automatically without confirmation (default: false)
    """
    try:
        # Get parameters
        days_threshold = request.args.get('days', default=15, type=int)
        auto_mode = request.args.get('auto', default='false').lower() == 'true'
        
        # Validate days threshold
        if days_threshold < 1:
            return jsonify({'error': 'Days threshold must be at least 1'}), 400
        
        # Run cleanup
        removed_count, remaining_count = cleanup_old_history(days_threshold=days_threshold)
        
        return jsonify({
            'success': True,
            'message': f'History cleanup completed successfully',
            'removed_count': removed_count,
            'remaining_count': remaining_count,
            'days_threshold': days_threshold,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error cleaning up history: {e}")
        return jsonify({'error': str(e)}), 500

# Manual video entry API for missing callbacks
@main_bp.route('/api/history/manual-video', methods=['POST'])
def add_manual_video():
    """
    Add a manual video entry for videos that were successfully created on Kie
    but didn't trigger callbacks to the app.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        task_id = data.get('task_id')
        video_url = data.get('video_url')
        
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400
        if not video_url:
            return jsonify({'error': 'video_url is required'}), 400
        
        # Optional parameters
        author = data.get('author', '')
        domain_name = data.get('domain_name', '')
        
        # Create a video callback entry
        history_entry = {
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
        
        # Add to history
        if add_to_history(history_entry):
            current_app.logger.info(f"Manual video entry added for task: {task_id}")
            return jsonify({
                'success': True,
                'message': 'Manual video entry added successfully',
                'entry_id': history_entry['id'],
                'task_id': task_id,
                'video_url': video_url
            })
        else:
            return jsonify({'error': 'Failed to add manual video entry to history'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error adding manual video entry: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced callback handler that stores history
@main_bp.route('/callback-with-history', methods=['POST'])
def callback_handler_with_history():
    """
    Handle Kie API callbacks and store them in history.
    """
    try:
        callback_data = request.json
        if not callback_data:
            current_app.logger.warning("Received empty callback data")
            return jsonify({'status': 'error', 'message': 'Empty callback data'}), 400
        
        current_app.logger.info(f"Received callback: {json.dumps(callback_data, indent=2)}")
        
        # Extract task information
        task_id = callback_data.get('task_id') or callback_data.get('data', {}).get('task_id')
        callback_type = callback_data.get('callbackType')
        
        if not task_id:
            current_app.logger.warning("Callback missing task_id")
            return jsonify({'status': 'error', 'message': 'Missing task_id'}), 400
        
        current_app.logger.info(f"Callback for task_id: {task_id}, type: {callback_type}")
        
        # Create history entry
        history_entry = {
            'id': str(uuid.uuid4()),
            'task_id': task_id,
            'callback_type': callback_type,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'data': callback_data,
            'status': 'received'
        }
        
        # Add to history
        if add_to_history(history_entry):
            current_app.logger.info(f"Callback stored in history for task: {task_id}")
        else:
            current_app.logger.warning(f"Failed to store callback in history for task: {task_id}")
        
        # Always respond quickly (within 15 seconds as required)
        return jsonify({
            'status': 'success',
            'message': 'Callback received and stored',
            'task_id': task_id,
            'callback_type': callback_type,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing callback: {e}")
        current_app.logger.exception(e)
        
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500

# Update the existing callback handler to also store history
@main_bp.route('/callback', methods=['POST'])
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
            return jsonify({'status': 'error', 'message': 'Empty callback data'}), 400
        
        current_app.logger.info(f"Received callback: {json.dumps(callback_data, indent=2)}")
        
        # Process callback data
        processed_data = process_callback_data(callback_data)
        
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
                    'timestamp': datetime.datetime.utcnow().isoformat(),
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
                    'timestamp': datetime.datetime.utcnow().isoformat(),
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
            
            # Upsert into history: update the existing pending/processing entry for
            # this task if one exists, otherwise insert a new row.
            try:
                upsert_history_entry(history_entry)
                current_app.logger.info(f"Callback upserted in history for task: {task_id}")
            except Exception as history_error:
                current_app.logger.error(f"Failed to store callback in history: {history_error}")
        else:
            current_app.logger.warning("Callback missing task_id")
        
        # Always respond quickly (within 15 seconds as required)
        response_data = {
            'status': 'success',
            'message': 'Callback received and processed',
            'task_id': task_id,
            'callback_type': callback_type,
            'status_code': status_code,
            'is_video_callback': processed_data.get('is_video_callback', False),
            'tracks_count': len(processed_data.get('tracks', [])),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing callback: {e}")
        current_app.logger.exception(e)  # Log full traceback
        
        # Return error but don't crash - Kie will retry up to 3 times
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500