"""
API endpoints for manual lyrics search using LRCLIB and the lyricsdb pipeline.
"""
import logging
import tempfile
import os
from flask import Blueprint, jsonify, request, current_app
import requests
from flask_login import login_required, current_user

from app.models import AudioLibrary
from app import db

logger = logging.getLogger(__name__)

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
        
        # Query LRCLIB API with retry logic
        max_retries = 2
        timeout = 30
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = requests.get(lrclib_url, params=params, timeout=timeout,
                                        headers={'Connection': 'close'})
                response.raise_for_status()
                break
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"LRCLIB timeout on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    logger.error(f"LRCLIB timed out after {max_retries} attempts")
                    return jsonify({'error': 'Lyrics search service is slow to respond. Please try again.'}), 504
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"LRCLIB request failed: {e}")
                raise
        
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

        # Step 2: LRCLIB direct API call (search result already includes lyrics inline —
        # avoids the SSL EOF bug in the /api/get/{id} path endpoint on this urllib3 version)
        synced_lyrics = None
        plain_lyrics = None
        search_term = f"{resolved_title} {resolved_artist}".strip()

        try:
            lrclib_resp = requests.get(
                'https://lrclib.net/api/search',
                params={'q': search_term},
                headers={'Connection': 'close'},
                timeout=10,
            )
            if lrclib_resp.ok:
                tracks = lrclib_resp.json()
                if tracks:
                    best_track = tracks[0]
                    synced_lyrics = (best_track.get('syncedLyrics') or '').strip() or None
                    plain_lyrics = (best_track.get('plainLyrics') or '').strip() or None
                    logger.info(f"LRCLIB: synced={bool(synced_lyrics)}, plain={bool(plain_lyrics)}")
        except Exception as e:
            logger.warning(f"LRCLIB lookup failed (non-fatal): {e}")

        lyrics_text = synced_lyrics or plain_lyrics or ''
        has_synced = bool(synced_lyrics)

        if not lyrics_text:
            logger.info("Pipeline search: no lyrics found")
            return jsonify({'error': 'No lyrics found via pipeline'}), 404

        logger.info(
            f"Pipeline search found lyrics for '{resolved_title}' by '{resolved_artist}'"
            f"{' [synced]' if has_synced else ' [plain]'}"
        )

        return jsonify({
            'track_name': resolved_title,
            'artist_name': resolved_artist,
            'lyrics': lyrics_text,
            'has_synced': has_synced,
            'genius_url': genius_url,
        })

    except Exception as e:
        logger.error(f"Pipeline search error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
