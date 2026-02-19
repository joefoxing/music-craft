"""
API endpoints for manual lyrics search using LRCLIB and the lyricsdb pipeline.
"""
import logging
import tempfile
import os
import time
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask_login import login_required, current_user

from app.models import AudioLibrary
from app import db

logger = logging.getLogger(__name__)

# Create a session with retry strategy for LRCLIB
def create_lrclib_session():
    """Create a requests session with retry strategy for LRCLIB API calls."""
    session = requests.Session()
    
    # Retry strategy: retry on connection errors and timeouts
    retry_strategy = Retry(
        total=3,  # Total retries
        backoff_factor=1,  # Wait 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

lyrics_search_bp = Blueprint('lyrics_search', __name__, url_prefix='/api/lyrics-search')


@lyrics_search_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check to verify endpoint is accessible."""
    return jsonify({'status': 'ok', 'message': 'lyrics-search endpoint is working'})


@lyrics_search_bp.route('/extract-metadata', methods=['POST'])
def extract_metadata():
    """
    Extract artist and title metadata from an uploaded audio file.
    
    No authentication required for temporary metadata extraction.
    
    Returns:
        {
            "artist": "Artist Name" or null,
            "title": "Song Title" or null,
            "error": "error message" (if applicable)
        }
    """
    try:
        logger.info('=== extract-metadata endpoint called ===')
        logger.info(f'Request files: {list(request.files.keys())}')
        logger.info(f'Request form: {list(request.form.keys())}')
        
        if 'file' not in request.files:
            logger.warning('No file in request')
            return jsonify({'error': 'No file provided', 'artist': None, 'title': None}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning('Empty filename')
            return jsonify({'error': 'No file selected', 'artist': None, 'title': None}), 400
        
        logger.info(f'Processing file: {file.filename}')
        
        # Save to temporary file
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.audio', delete=False)
            logger.info(f'Temp file created at: {temp_file.name}')
            
            file.save(temp_file.name)
            temp_file.close()
            
            logger.info(f'File saved, size: {os.path.getsize(temp_file.name)} bytes')
            
            # Extract metadata
            artist, title = _extract_metadata_from_file(temp_file.name)
            
            logger.info(f'Extracted metadata - Artist: {artist}, Title: {title}')
            
            response = {
                'artist': artist,
                'title': title
            }
            logger.info(f'Returning: {response}')
            return jsonify(response)
        
        finally:
            if temp_file:
                import os
                try:
                    os.unlink(temp_file.name)
                    logger.debug(f'Deleted temp file: {temp_file.name}')
                except Exception as e:
                    logger.warning(f'Failed to delete temp file: {e}')
    
    except Exception as e:
        logger.error(f"ERROR in extract-metadata: {e}", exc_info=True)
        return jsonify({'error': str(e), 'artist': None, 'title': None}), 500


def _extract_metadata_from_file(file_path):
    """Extract artist and title from audio file metadata tags."""
    try:
        logger.debug(f'Attempting to extract metadata from: {file_path}')
        
        try:
            import mutagen
            mutagen_file_loader = mutagen.File
            logger.debug('Mutagen loaded successfully')
        except ImportError as e:
            logger.warning(f'Mutagen not available: {e}')
            return None, None
        except Exception as e:
            logger.warning(f'Error loading mutagen: {e}')
            return None, None

        try:
            audio_file = mutagen_file_loader(file_path)
            logger.debug(f'Audio file loaded: {type(audio_file)}')
        except Exception as e:
            logger.debug(f'Could not load audio file with mutagen: {e}')
            return None, None
            
        if not audio_file or not getattr(audio_file, 'tags', None):
            logger.debug('No tags found in audio file')
            return None, None

        tags = audio_file.tags
        logger.debug(f'Tags found: {type(tags)}')
        artist = None
        title = None

        # ID3 tags (MP3)
        for key in ['TPE1', 'TPE2']:
            if key in tags:
                artist = _normalize_tag_value(tags[key])
                logger.debug(f'Found artist via {key}: {artist}')
                if artist:
                    break
        if 'TIT2' in tags:
            title = _normalize_tag_value(tags['TIT2'])
            logger.debug(f'Found title via TIT2: {title}')

        # Vorbis comments (FLAC, OGG)
        if not artist:
            for key in ['artist', 'ARTIST', 'albumartist', 'ALBUMARTIST']:
                if key in tags:
                    val = tags[key]
                    artist = val[0] if isinstance(val, list) else str(val)
                    artist = artist.strip() if artist else None
                    logger.debug(f'Found artist via {key}: {artist}')
                    if artist:
                        break
        if not title:
            for key in ['title', 'TITLE']:
                if key in tags:
                    val = tags[key]
                    title = val[0] if isinstance(val, list) else str(val)
                    title = title.strip() if title else None
                    logger.debug(f'Found title via {key}: {title}')
                    if title:
                        break

        # MP4/M4A atoms
        if not artist and '\xa9ART' in tags:
            val = tags['\xa9ART']
            artist = val[0] if isinstance(val, list) else str(val)
            artist = artist.strip() if artist else None
            logger.debug(f'Found artist via MP4 atom: {artist}')
        if not title and '\xa9nam' in tags:
            val = tags['\xa9nam']
            title = val[0] if isinstance(val, list) else str(val)
            title = title.strip() if title else None
            logger.debug(f'Found title via MP4 atom: {title}')

        logger.info(f'Metadata extraction result - Artist: {artist}, Title: {title}')
        return artist, title

    except Exception as e:
        logger.error(f'Error extracting metadata: {e}', exc_info=True)
        return None, None


def _normalize_tag_value(value):
    """Normalize tag value to string."""
    if value is None:
        return None

    if isinstance(value, list):
        normalized = '\n'.join(str(v) for v in value if v is not None).strip()
        return normalized or None

    if hasattr(value, 'text'):
        text_value = getattr(value, 'text')
        if isinstance(text_value, list):
            normalized = '\n'.join(str(v) for v in text_value if v is not None).strip()
            return normalized or None
        normalized = str(text_value).strip()
        return normalized or None

    normalized = str(value).strip()
    return normalized or None


@lyrics_search_bp.route('/search', methods=['POST'])
@login_required
def search_lyrics():
    """
    Search for lyrics on LRCLIB by track name and artist.
    
    Request JSON:
        {
            "track_name": "Song Title",
            "artist_name": "Artist Name" (optional)
        }
    
    Returns:
        List of matching lyrics results from LRCLIB
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        track_name = data.get('track_name', '').strip()
        if not track_name:
            return jsonify({'error': 'track_name is required'}), 400
        
        artist_name = data.get('artist_name', '').strip()
        
        # Build LRCLIB API request
        lrclib_url = 'https://lrclib.net/api/search'
        params = {
            'track_name': track_name
        }
        if artist_name:
            params['artist_name'] = artist_name
        
        logger.info(f"Searching LRCLIB: track='{track_name}', artist='{artist_name}'")
        
        # Query LRCLIB API with robust error handling
        session = create_lrclib_session()
        timeout = 30
        response = None
        
        try:
            # First attempt with SSL verification enabled
            response = session.get(lrclib_url, params=params, timeout=timeout,
                                  headers={'Connection': 'close'})
            response.raise_for_status()
            logger.info(f"LRCLIB search successful on first attempt")
        except requests.exceptions.SSLError as e:
            # SSL error - try with verify=False as fallback
            logger.warning(f"LRCLIB SSL error: {e}. Retrying without SSL verification...")
            try:
                response = session.get(lrclib_url, params=params, timeout=timeout,
                                      headers={'Connection': 'close'}, verify=False)
                response.raise_for_status()
                logger.info(f"LRCLIB search successful with verify=False")
            except Exception as e2:
                logger.error(f"LRCLIB search failed even without SSL verification: {e2}")
                return jsonify({'error': 'Failed to search lyrics: SSL connection issue. Please try again.'}), 503
        except requests.exceptions.Timeout as e:
            logger.error(f"LRCLIB search timed out: {e}")
            return jsonify({'error': 'Lyrics search service is slow to respond. Please try again.'}), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"LRCLIB request failed: {e}")
            return jsonify({'error': f'Failed to search lyrics: {str(e)}'}), 503
        
        results = response.json()
        
        if not isinstance(results, list):
            logger.warning(f"LRCLIB returned non-list response: {type(results)}")
            results = []
        
        # Filter and format results
        formatted_results = []
        for item in results[:20]:  # Limit to 20 results
            if not isinstance(item, dict):
                continue
            
            plain_lyrics = item.get('plainLyrics')
            synced_lyrics = item.get('syncedLyrics')
            
            # Handle None values explicitly
            plain_lyrics = '' if plain_lyrics is None else str(plain_lyrics).strip()
            synced_lyrics = '' if synced_lyrics is None else str(synced_lyrics).strip()
            
            # Prefer synced lyrics if available, fallback to plain
            lyrics_text = synced_lyrics if synced_lyrics else plain_lyrics
            
            if not lyrics_text:
                continue
            
            formatted_results.append({
                'id': item.get('id'),
                'track_name': item.get('trackName', ''),
                'artist_name': item.get('artistName', ''),
                'album_name': item.get('albumName', ''),
                'duration': item.get('duration'),
                'lyrics': lyrics_text,
                'has_synced': bool(synced_lyrics),
                'instrumental': item.get('instrumental', False)
            })
        
        logger.info(f"Found {len(formatted_results)} lyrics results")
        
        return jsonify({
            'results': formatted_results,
            'count': len(formatted_results)
        })
    
    except requests.exceptions.RequestException as e:
        logger.error(f"LRCLIB API request failed: {e}")
        return jsonify({'error': f'Failed to search lyrics: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"Error searching lyrics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lyrics_search_bp.route('/apply', methods=['POST'])
@login_required
def apply_lyrics():
    """
    Apply selected lyrics from LRCLIB search to an AudioLibrary item.
    
    Request JSON:
        {
            "audio_id": "uuid",  (optional - if not provided, just return lyrics)
            "lyrics": "lyrics text",
            "track_name": "Song Title",
            "artist_name": "Artist Name",
            "album_name": "Album Name" (optional)
        }
    
    Returns:
        Updated audio item or just success confirmation
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        lyrics = data.get('lyrics', '').strip()
        if not lyrics:
            return jsonify({'error': 'lyrics is required'}), 400
        
        audio_id = data.get('audio_id')
        track_name = data.get('track_name', '').strip()
        artist_name = data.get('artist_name', '').strip()
        album_name = data.get('album_name', '').strip()
        
        # If audio_id provided, update the AudioLibrary record
        if audio_id:
            audio_item = AudioLibrary.query.filter_by(
                id=audio_id,
                user_id=current_user.id
            ).first()
            
            if not audio_item:
                return jsonify({'error': 'Audio item not found'}), 404
            
            audio_item.lyrics = lyrics
            audio_item.lyrics_source = 'lrclib'
            audio_item.lyrics_extraction_status = 'completed'
            audio_item.lyrics_extraction_error = None
            
            # Optionally update metadata if provided
            if track_name:
                audio_item.title = track_name
            if artist_name:
                audio_item.artist = artist_name
            
            db.session.commit()
            
            logger.info(f"Applied LRCLIB lyrics to audio item {audio_id}")
            
            return jsonify({
                'audio_item': audio_item.to_dict(),
                'message': 'Lyrics applied successfully'
            })
        
        # If no audio_id, just return the lyrics (for direct paste to prompt)
        return jsonify({
            'lyrics': lyrics,
            'message': 'Lyrics ready to use'
        })
    
    except Exception as e:
        logger.error(f"Error applying lyrics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@lyrics_search_bp.route('/pipeline-search', methods=['POST'])
@login_required
def pipeline_search():
    """
    Search for lyrics using the lyricsdb pipeline (Genius API + syncedlyrics).

    Requires GENIUS_ACCESS_TOKEN environment variable to be set.

    Request JSON:
        {
            "track_name": "Song Title",
            "artist_name": "Artist Name" (optional)
        }

    Returns:
        {
            "track_name": "...",
            "artist_name": "...",
            "lyrics": "plain or synced lyrics text",
            "has_synced": true/false,
            "genius_url": "..."
        }
    """
    try:
        genius_token = os.environ.get('GENIUS_ACCESS_TOKEN', '').strip()
        if not genius_token:
            return jsonify({
                'error': 'GENIUS_ACCESS_TOKEN is not configured. '
                         'Please set the environment variable to enable pipeline search.'
            }), 503

        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        track_name = data.get('track_name', '').strip()
        if not track_name:
            return jsonify({'error': 'track_name is required'}), 400

        artist_name = data.get('artist_name', '').strip()

        logger.info(f"Pipeline search: track='{track_name}', artist='{artist_name}'")

        # Step 1: Genius REST API for metadata ONLY (no page scraping = no Cloudflare block)
        genius_url = None
        resolved_title = track_name
        resolved_artist = artist_name
        try:
            genius_resp = requests.get(
                'https://api.genius.com/search',
                params={'q': f'{track_name} {artist_name}'.strip()},
                headers={'Authorization': f'Bearer {genius_token}'},
                timeout=10,
            )
            if genius_resp.ok:
                hits = genius_resp.json().get('response', {}).get('hits', [])
                if hits:
                    best = hits[0]['result']
                    resolved_title = best.get('title', track_name)
                    resolved_artist = (best.get('primary_artist') or {}).get('name', artist_name)
                    genius_url = best.get('url')
                    logger.info(f"Genius metadata: '{resolved_title}' by '{resolved_artist}'")
        except Exception as e:
            logger.warning(f"Genius metadata lookup failed (non-fatal): {e}")

        # Step 2: LRCLIB API call with multiple search strategies
        synced_lyrics = None
        plain_lyrics = None
        lrclib_metadata = None
        
        session = create_lrclib_session()
        lrclib_attempts = [
            # Strategy 1: Structured search with track_name and artist_name
            {
                'name': 'structured',
                'params': {
                    'track_name': resolved_title,
                    'artist_name': resolved_artist
                }
            },
            # Strategy 2: Generic keyword search (fallback)
            {
                'name': 'keyword',
                'params': {
                    'q': f"{resolved_title} {resolved_artist}".strip()
                }
            },
            # Strategy 3: Title-only search
            {
                'name': 'title_only',
                'params': {
                    'track_name': resolved_title
                }
            }
        ]
        
        for strategy in lrclib_attempts:
            try:
                logger.info(f"LRCLIB pipeline search attempt: {strategy['name']}")
                try:
                    # First attempt with SSL verification enabled
                    lrclib_resp = session.get(
                        'https://lrclib.net/api/search',
                        params=strategy['params'],
                        headers={'Connection': 'close'},
                        timeout=10,
                    )
                except requests.exceptions.SSLError as e:
                    # SSL error - retry with verify=False
                    logger.warning(f"LRCLIB SSL error (attempt {strategy['name']}): {e}. Retrying without SSL verification...")
                    lrclib_resp = session.get(
                        'https://lrclib.net/api/search',
                        params=strategy['params'],
                        headers={'Connection': 'close'},
                        timeout=10,
                        verify=False
                    )
                
                if lrclib_resp.ok:
                    tracks = lrclib_resp.json()
                    if tracks and isinstance(tracks, list) and len(tracks) > 0:
                        best_track = tracks[0]
                        synced_lyrics = (best_track.get('syncedLyrics') or '').strip() or None
                        plain_lyrics = (best_track.get('plainLyrics') or '').strip() or None
                        lrclib_metadata = best_track
                        logger.info(f"LRCLIB found lyrics via {strategy['name']}: synced={bool(synced_lyrics)}, plain={bool(plain_lyrics)}")
                        break  # Success, stop trying other strategies
                    else:
                        logger.debug(f"LRCLIB {strategy['name']} returned empty results")
                else:
                    logger.debug(f"LRCLIB {strategy['name']} returned status {lrclib_resp.status_code}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"LRCLIB {strategy['name']} timed out: {e}")
                continue
            except Exception as e:
                logger.warning(f"LRCLIB {strategy['name']} failed: {e}")
                continue

        lyrics_text = synced_lyrics or plain_lyrics or ''
        has_synced = bool(synced_lyrics)

        # If LRCLIB found lyrics, return them
        if lyrics_text:
            logger.info(f"Pipeline search found lyrics via LRCLIB for '{resolved_title}' by '{resolved_artist}'")
            return jsonify({
                'track_name': resolved_title,
                'artist_name': resolved_artist,
                'lyrics': lyrics_text,
                'has_synced': has_synced,
                'genius_url': genius_url,
            })
        
        # If LRCLIB had no results, try fallback strategies
        # For now, we can't do AssemblyAI transcription without an audio file,
        # but we can try to provide a helpful error message
        logger.info(f"Pipeline search: no lyrics found via LRCLIB, no audio file for transcription fallback")
        return jsonify({
            'error': 'No lyrics found. Try searching by a different name, or upload the audio file for AI transcription.',
            'suggestions': {
                'track_name': resolved_title,
                'artist_name': resolved_artist,
                'genius_url': genius_url
            }
        }), 404

    except Exception as e:
        logger.error(f"Pipeline search error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
