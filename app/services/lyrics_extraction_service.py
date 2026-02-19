"""
Lyrics extraction service.
Uses multi-tier fallback strategy: metadata -> LRCLIB -> AssemblyAI.
"""
import os
import json
import re
import shutil
import subprocess
import tempfile
import importlib
import hashlib
import time
from collections import Counter
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import requests
from flask import current_app

from app import db
from app.models import LyricsCache


class LRCLIBClient:
    """Enhanced LRCLIB API client with advanced features."""
    
    BASE_URL = 'https://lrclib.net/api'
    SEARCH_ENDPOINT = '/search'
    GET_ENDPOINT = '/get'
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 50
    _request_times = []
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicCraft-LyricsExtractor/1.0'
        })
    
    @classmethod
    def _check_rate_limit(cls):
        """Implement rate limiting to respect API usage."""
        now = time.time()
        # Remove requests older than 1 minute
        cls._request_times = [t for t in cls._request_times if now - t < 60]
        
        if len(cls._request_times) >= cls.MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (now - cls._request_times[0])
            if sleep_time > 0:
                current_app.logger.warning(f'Rate limit reached, sleeping {sleep_time:.2f}s')
                time.sleep(sleep_time)
        
        cls._request_times.append(now)
    
    def search_lyrics(
        self,
        track_name: str,
        artist_name: Optional[str] = None,
        album_name: Optional[str] = None,
        duration: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search LRCLIB for lyrics with enhanced matching.
        
        Args:
            track_name: Track title (required)
            artist_name: Artist name (optional, improves accuracy)
            album_name: Album name (optional, for disambiguation)
            duration: Track duration in seconds (optional, for disambiguation)
            
        Returns:
            List of matching results with metadata
        """
        self._check_rate_limit()
        
        # Normalize track name for better matching
        normalized_track = self._normalize_for_search(track_name)
        
        params = {'track_name': normalized_track}
        if artist_name:
            params['artist_name'] = self._normalize_for_search(artist_name)
        if album_name:
            params['album_name'] = album_name
        
        try:
            url = f'{self.BASE_URL}{self.SEARCH_ENDPOINT}'
            current_app.logger.debug(f'LRCLIB search: {params}')
            
            response = self._request_with_retry(url, params=params)
            
            if not response:
                return []
            
            results = response.json()
            
            if not isinstance(results, list):
                current_app.logger.warning(f'Unexpected LRCLIB response type: {type(results)}')
                return []
            
            # Score and rank results
            scored_results = self._score_results(
                results,
                track_name=track_name,
                artist_name=artist_name,
                album_name=album_name,
                duration=duration
            )
            
            # Sort by score (highest first)
            scored_results.sort(key=lambda x: x['match_score'], reverse=True)
            
            current_app.logger.info(
                f'LRCLIB found {len(scored_results)} results for "{track_name}"'
            )
            
            return scored_results
            
        except Exception as exc:
            current_app.logger.warning(f'LRCLIB search error: {exc}')
            return []
    
    def get_lyrics_by_id(self, lrclib_id: int) -> Optional[Dict[str, Any]]:
        """
        Get lyrics by LRCLIB ID for exact retrieval.
        
        Args:
            lrclib_id: LRCLIB track ID
            
        Returns:
            Lyrics data or None
        """
        self._check_rate_limit()
        
        try:
            url = f'{self.BASE_URL}{self.GET_ENDPOINT}/{lrclib_id}'
            response = self._request_with_retry(url)
            
            if response:
                return response.json()
            
            return None
            
        except Exception as exc:
            current_app.logger.warning(f'LRCLIB get error: {exc}')
            return None
    
    def _request_with_retry(
        self,
        url: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
        timeout: int = 15
    ) -> Optional[requests.Response]:
        """
        Make request with exponential backoff retry logic.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    current_app.logger.warning(
                        f'LRCLIB timeout (attempt {attempt + 1}/{max_retries}), '
                        f'retrying in {wait_time}s'
                    )
                    time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1 and e.response is None:
                    # Network error, retry
                    wait_time = (2 ** attempt) * 0.5
                    current_app.logger.warning(
                        f'LRCLIB network error (attempt {attempt + 1}/{max_retries}), '
                        f'retrying in {wait_time}s'
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # HTTP error or final attempt
                    break
        
        if last_error:
            current_app.logger.error(f'LRCLIB request failed after {max_retries} attempts: {last_error}')
        
        return None
    
    def _score_results(
        self,
        results: List[Dict],
        track_name: str,
        artist_name: Optional[str] = None,
        album_name: Optional[str] = None,
        duration: Optional[int] = None
    ) -> List[Dict]:
        """
        Score search results based on similarity and metadata match.
        """
        scored = []
        
        for result in results:
            score = 0.0
            
            # Track name similarity (most important - max 50 points)
            result_track = result.get('trackName', '')
            if result_track:
                similarity = self._similarity_score(track_name, result_track)
                score += similarity * 50
            
            # Artist name match (max 25 points)
            if artist_name:
                result_artist = result.get('artistName', '')
                if result_artist:
                    similarity = self._similarity_score(artist_name, result_artist)
                    score += similarity * 25
            else:
                # No artist provided, give partial credit
                score += 12.5
            
            # Album match (max 10 points)
            if album_name:
                result_album = result.get('albumName', '')
                if result_album:
                    similarity = self._similarity_score(album_name, result_album)
                    score += similarity * 10
            else:
                score += 5
            
            # Duration match (max 10 points)
            if duration:
                result_duration = result.get('duration')
                if result_duration:
                    # Allow 5% variance
                    diff_ratio = abs(duration - result_duration) / max(duration, 1)
                    if diff_ratio <= 0.05:
                        score += 10
                    elif diff_ratio <= 0.10:
                        score += 5
            else:
                score += 5
            
            # Bonus for synced lyrics (5 points)
            if result.get('syncedLyrics'):
                score += 5
            
            # Store score in result
            result['match_score'] = score
            scored.append(result)
        
        return scored
    
    @staticmethod
    def _similarity_score(str1: str, str2: str) -> float:
        """
        Compute similarity score between two strings (0-1).
        Uses normalized fuzzy matching.
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = LRCLIBClient._normalize_for_comparison(str1)
        s2 = LRCLIBClient._normalize_for_comparison(str2)
        
        if s1 == s2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1, s2).ratio()
    
    @staticmethod
    def _normalize_for_search(text: str) -> str:
        """Normalize text for LRCLIB search query."""
        if not text:
            return ''
        
        # Remove extra whitespace
        normalized = ' '.join(text.split())
        
        return normalized.strip()
    
    @staticmethod
    def _normalize_for_comparison(text: str) -> str:
        """Normalize text for similarity comparison."""
        if not text:
            return ''
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common noise words
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheticals
        text = re.sub(r'\[.*?\]', '', text)  # Remove brackets
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()


class LyricsCacheManager:
    """Manage persistent caching of LRCLIB results."""
    
    @staticmethod
    def get_cache_key(artist: str, title: str) -> str:
        """Generate cache key for artist/title pair."""
        normalized = f"{artist}:{title}".lower().strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_cached_lyrics(artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached lyrics if available and not expired."""
        if not current_app.config.get('LYRICS_CACHE_ENABLED', True):
            return None
        
        cache_key = LyricsCacheManager.get_cache_key(artist, title)
        cache_ttl_days = int(current_app.config.get('LYRICS_CACHE_TTL_DAYS', 30))
        
        try:
            cached = LyricsCache.query.filter_by(cache_key=cache_key).first()
            
            if not cached:
                return None
            
            # Check if expired
            expiry = cached.created_at + timedelta(days=cache_ttl_days)
            if datetime.utcnow() > expiry:
                current_app.logger.debug(f'Cache expired for {artist} - {title}')
                db.session.delete(cached)
                db.session.commit()
                return None
            
            current_app.logger.info(f'Cache hit for {artist} - {title}')
            
            return {
                'lyrics': cached.lyrics_text,
                'synced_lyrics': cached.synced_lyrics,
                'source': 'lrclib_cache',
                'lrclib_id': cached.lrclib_id,
                'artist_name': cached.artist_name,
                'track_name': cached.track_name,
                'album_name': cached.album_name,
                'match_score': cached.match_score
            }
            
        except Exception as exc:
            current_app.logger.warning(f'Cache retrieval error: {exc}')
            return None
    
    @staticmethod
    def cache_lyrics(
        artist: str,
        title: str,
        lyrics_text: str,
        synced_lyrics: Optional[str] = None,
        lrclib_id: Optional[int] = None,
        album_name: Optional[str] = None,
        duration: Optional[int] = None,
        match_score: Optional[float] = None
    ):
        """Store lyrics in cache."""
        if not current_app.config.get('LYRICS_CACHE_ENABLED', True):
            return
        
        cache_key = LyricsCacheManager.get_cache_key(artist, title)
        
        try:
            # Check if already exists
            cached = LyricsCache.query.filter_by(cache_key=cache_key).first()
            
            if cached:
                # Update existing
                cached.lyrics_text = lyrics_text
                cached.synced_lyrics = synced_lyrics
                cached.lrclib_id = lrclib_id
                cached.album_name = album_name
                cached.duration = duration
                cached.match_score = match_score
                cached.created_at = datetime.utcnow()
            else:
                # Create new
                cached = LyricsCache(
                    cache_key=cache_key,
                    artist_name=artist,
                    track_name=title,
                    album_name=album_name,
                    lyrics_text=lyrics_text,
                    synced_lyrics=synced_lyrics,
                    lrclib_id=lrclib_id,
                    duration=duration,
                    match_score=match_score
                )
                db.session.add(cached)
            
            db.session.commit()
            current_app.logger.info(f'Cached lyrics for {artist} - {title}')
            
        except Exception as exc:
            current_app.logger.warning(f'Cache storage error: {exc}')
            db.session.rollback()


class LyricsExtractionService:
    """
    Service for extracting lyrics from audio.
    
    Uses an enhanced multi-tier strategy:
    1. Embedded metadata (free, instant)
    2. Cache lookup (instant)
    3. LRCLIB API with enhanced matching (free)
    4. AssemblyAI cloud transcription (paid)
    """
    
    def extract_lyrics(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract lyrics from audio source using enhanced LRCLIB integration.

        Returns:
            Tuple of (lyrics, source, error)
        """
        if not current_app.config.get('LYRICS_EXTRACTION_ENABLED', True):
            return None, None, 'Lyrics extraction is disabled'

        # Use enhanced service by default, fallback to legacy if needed
        use_enhanced = current_app.config.get('LYRICS_USE_ENHANCED_LRCLIB', True)
        
        if use_enhanced:
            service = LyricsExtractionServiceEnhanced()
        else:
            service = LyricsExtractionServiceLegacy()
            
        return service.extract_lyrics(
            audio_url=audio_url,
            local_file_path=local_file_path,
            whisper_language_override=whisper_language_override
        )



class LyricsExtractionServiceLegacy:
    """
    Legacy implementation of lyrics extraction using multi-tier strategy.
    
    Tier 1: Embedded metadata lyrics (free, instant)
    Tier 2: LRCLIB API search (by file tags, free, no API key)
    Tier 3: AssemblyAI speech-to-text (fast cloud transcription)
    """
    
    METADATA_KEYS = {
        'lyrics',
        'unsyncedlyrics',
        '\u00a9lyr',
        'lyric',
    }

    MIN_WORDS_FOR_ACCEPT = 6
    _VIETNAMESE_COMMON_FIXES = (
        (r'\blời\s+bay\s+hát\b', 'lời bài hát'),
        (r'\blời\s+bai\s+hát\b', 'lời bài hát'),
        (r'\bhệ\s+thống\s+nhận\s+dạng\s+dọng\s+nói\b', 'hệ thống nhận dạng giọng nói'),
        (r'\bdọng\s+nói\b', 'giọng nói'),
        (r'\bdong\s+noi\b', 'giọng nói'),
    )
    _ENGLISH_STOPWORDS = {
        'the', 'and', 'you', 'your', 'this', 'that', 'with', 'for', 'are', 'was', 'were',
        'have', 'has', 'from', 'into', 'song', 'lyrics', 'love', 'baby', 'night', 'heart',
        'when', 'what', 'where', 'why', 'how', 'hello', 'world', 'test'
    }

    def extract_lyrics(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract lyrics using multi-tier fallback chain.

        Tier 1: Embedded metadata (free, instant)
        Tier 2: LRCLIB API lookup by artist + title (free, no API key)
        Tier 3: AssemblyAI cloud transcription (of isolated vocals)

        Returns:
            Tuple of (lyrics, source, error)
        """
        if not current_app.config.get('LYRICS_EXTRACTION_ENABLED', True):
            return None, None, 'Lyrics extraction is disabled'

        if not audio_url and not local_file_path:
            return None, None, 'No audio source provided'

        temp_dir = tempfile.mkdtemp(prefix='lyrics_extract_')
        try:
            # Resolve audio file path
            target_path = local_file_path
            if not target_path:
                target_path = self._download_audio_file(audio_url, temp_dir)

            # --- Tier 1: Embedded metadata ---
            metadata_lyrics = self._extract_metadata_lyrics(target_path)
            if metadata_lyrics:
                current_app.logger.info('Lyrics resolved via Tier 1: embedded metadata')
                return metadata_lyrics, 'metadata', None

            # --- Tier 2: LRCLIB API lookup ---
            artist, title = self._extract_artist_title(target_path)
            lrclib_lyrics = self._lookup_lyrics_lrclib(artist, title)
            if lrclib_lyrics:
                current_app.logger.info('Lyrics resolved via Tier 2: LRCLIB')
                return lrclib_lyrics, 'lrclib', None

            # --- Tier 3: AssemblyAI transcription ---
            # Optionally separate vocals first for better accuracy
            transcription_target = target_path
            if current_app.config.get('LYRICS_VOCAL_SEPARATION_ENABLED', False):
                separated_path = self._separate_vocals_with_demucs(target_path, temp_dir)
                if separated_path:
                    transcription_target = separated_path

            raw_lyrics = self._transcribe_with_assemblyai(
                transcription_target,
                language_override=whisper_language_override,
            )

            if raw_lyrics:
                # Apply post-processing (de-duplication, cleanup)
                cleaned = self._postprocess_lyrics(raw_lyrics)
                # Apply Vietnamese corrections if applicable
                language = whisper_language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE')
                final = self._apply_language_post_corrections(cleaned, language)

                if final and self._is_transcription_usable(final, expected_language=language):
                    current_app.logger.info('Lyrics resolved via Tier 3: AssemblyAI')
                    return final, 'assemblyai', None

            return None, None, 'No lyrics detected from metadata, database lookup, or transcription'

        except Exception as exc:
            current_app.logger.warning(f'Lyrics extraction failed: {exc}')
            return None, None, str(exc)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _lookup_lyrics_lrclib(
        self,
        artist: Optional[str],
        title: Optional[str]
    ) -> Optional[str]:
        """
        Tier 2: Look up lyrics from LRCLIB by artist and track title.
        LRCLIB is free and requires no API key.
        Returns None if missing metadata or no match found.
        """
        if not current_app.config.get('LYRICS_USE_LRCLIB', False):
            return None

        if not artist or not title:
            current_app.logger.debug('Missing artist or title, skipping LRCLIB lookup')
            return None

        try:
            # Query LRCLIB API
            lrclib_url = 'https://lrclib.net/api/search'
            params = {
                'track_name': title.strip(),
                'artist_name': artist.strip()
            }
            
            current_app.logger.debug(f'LRCLIB search: "{artist}" - "{title}"')
            
            response = requests.get(
                lrclib_url,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            results = response.json()

            if not isinstance(results, list) or len(results) == 0:
                current_app.logger.debug(f'LRCLIB: No results found for "{artist}" - "{title}"')
                return None

            # Get the first result (best match)
            best_match = results[0]
            
            # Prefer synced lyrics if available, fallback to plain
            synced_lyrics = best_match.get('syncedLyrics', '').strip()
            plain_lyrics = best_match.get('plainLyrics', '').strip()
            
            lyrics_text = synced_lyrics if synced_lyrics else plain_lyrics
            
            if not lyrics_text:
                current_app.logger.debug(f'LRCLIB: No lyrics content in match for "{artist}" - "{title}"')
                return None

            current_app.logger.info(
                f'LRCLIB lyrics found for "{artist} - {title}": {len(lyrics_text)} chars'
            )
            return lyrics_text

        except requests.exceptions.Timeout:
            current_app.logger.warning(f'LRCLIB API timeout for "{artist}" - "{title}"')
            return None
        except Exception as exc:
            current_app.logger.warning(f'LRCLIB API error: {exc}')
            return None

    def _transcribe_with_assemblyai(
        self,
        audio_path: str,
        language_override: Optional[str] = None,
    ) -> Optional[str]:
        """
        Tier 3: Transcribe audio using AssemblyAI's cloud API.
        Uses the Universal-2 model. The SDK handles file upload and polling automatically.
        Free tier: 185 hours of pre-recorded audio.
        Paid: ~$0.0037/min (cheaper than OpenAI Whisper).
        """
        if not current_app.config.get('LYRICS_USE_ASSEMBLYAI', False):
            return None

        try:
            import assemblyai as aai
        except ImportError:
            current_app.logger.error('assemblyai package not installed')
            return None

        api_key = current_app.config.get('ASSEMBLYAI_API_KEY', '')
        if not api_key:
            current_app.logger.error('ASSEMBLYAI_API_KEY not configured')
            return None

        aai.settings.api_key = api_key

        try:
            # Configure with speech_models (v0.52.0+)
            language = language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE')
            
            if language:
                config = aai.TranscriptionConfig(
                    speech_models=['universal-2'],
                    language_code=language
                )
            else:
                config = aai.TranscriptionConfig(
                    speech_models=['universal-2'],
                    language_detection=True
                )

            # The SDK handles file upload and polling automatically
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_path, config=config)

            if transcript.status == aai.TranscriptStatus.error:
                current_app.logger.error(f'AssemblyAI transcription error: {transcript.error}')
                return None

            text = (transcript.text or '').strip()

            if not text:
                current_app.logger.warning('AssemblyAI returned empty transcript')
                return None

            current_app.logger.info(
                f'AssemblyAI transcription complete: {len(text)} chars'
            )
            return text

        except Exception as exc:
            current_app.logger.error(f'AssemblyAI API error: {exc}')
            return None

    def _extract_artist_title(self, audio_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract artist and title from audio file metadata tags."""
        try:
            mutagen_module = importlib.import_module('mutagen')
            mutagen_file_loader = getattr(mutagen_module, 'File')
        except Exception:
            return None, None

        try:
            audio_file = mutagen_file_loader(audio_path)
            if not audio_file or not getattr(audio_file, 'tags', None):
                return None, None

            tags = audio_file.tags
            artist = None
            title = None

            # ID3 tags (MP3)
            for key in ['TPE1', 'TPE2']:
                if key in tags:
                    artist = self._normalize_tag_value(tags[key])
                    if artist:
                        break
            if 'TIT2' in tags:
                title = self._normalize_tag_value(tags['TIT2'])

            # Vorbis comments (FLAC, OGG)
            if not artist:
                for key in ['artist', 'ARTIST', 'albumartist', 'ALBUMARTIST']:
                    if key in tags:
                        val = tags[key]
                        artist = val[0] if isinstance(val, list) else str(val)
                        artist = artist.strip() if artist else None
                        if artist:
                            break
            if not title:
                for key in ['title', 'TITLE']:
                    if key in tags:
                        val = tags[key]
                        title = val[0] if isinstance(val, list) else str(val)
                        title = title.strip() if title else None
                        if title:
                            break

            # MP4/M4A atoms
            if not artist and '\xa9ART' in tags:
                val = tags['\xa9ART']
                artist = val[0] if isinstance(val, list) else str(val)
                artist = artist.strip() if artist else None
            if not title and '\xa9nam' in tags:
                val = tags['\xa9nam']
                title = val[0] if isinstance(val, list) else str(val)
                title = title.strip() if title else None

            return artist, title

        except Exception as exc:
            current_app.logger.debug(f'Error extracting artist/title: {exc}')
            return None, None

    def _extract_metadata_lyrics(self, audio_path: str) -> Optional[str]:
        """Extract lyrics from metadata tags (ID3, MP4 tags, etc)."""
        try:
            mutagen_module = importlib.import_module('mutagen')
            mutagen_file_loader = getattr(mutagen_module, 'File')
        except Exception as exc:
            current_app.logger.info(f'Mutagen unavailable for metadata extraction: {exc}')
            return None

        try:
            audio_file = mutagen_file_loader(audio_path)
            if not audio_file or not getattr(audio_file, 'tags', None):
                return None

            tags = audio_file.tags

            for key in self.METADATA_KEYS:
                if key in tags:
                    value = tags.get(key)
                    lyrics = self._normalize_tag_value(value)
                    if lyrics:
                        return lyrics

            for key, value in tags.items():
                lowered = str(key).lower()
                if 'lyric' in lowered or key == 'USLT':
                    lyrics = self._normalize_tag_value(value)
                    if lyrics:
                        return lyrics
        except Exception as exc:
            current_app.logger.info(f'Metadata lyrics extraction failed: {exc}')

        return None

    def _separate_vocals_with_demucs(self, audio_path: str, temp_dir: str) -> Optional[str]:
        """Run Demucs CLI and return separated vocal stem path when available."""
        demucs_bin = shutil.which('demucs')
        if not demucs_bin:
            current_app.logger.info('Demucs CLI not available; skipping vocal separation')
            return None

        output_dir = os.path.join(temp_dir, 'demucs')
        os.makedirs(output_dir, exist_ok=True)

        command = [
            demucs_bin,
            '--two-stems',
            'vocals',
            '-o',
            output_dir,
            audio_path,
        ]

        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=300)
            if completed.returncode != 0:
                current_app.logger.info(
                    f'Demucs failed ({completed.returncode}): {completed.stderr[:300] if completed.stderr else ""}'
                )
                return None

            audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
            for model_dir in os.listdir(output_dir):
                candidate = os.path.join(output_dir, model_dir, audio_basename, 'vocals.wav')
                if os.path.exists(candidate):
                    return candidate

        except Exception as exc:
            current_app.logger.info(f'Demucs separation error: {exc}')

        return None

    def _is_transcription_usable(self, text: Optional[str], expected_language: Optional[str] = None) -> bool:
        """Heuristic check to reject obviously bad repetitive/hallucinated output."""
        if not text:
            return False

        if self._looks_translated_output(text, expected_language):
            current_app.logger.info('Rejected transcription that appears translated instead of original language')
            return False

        words = self._tokenize_words(text)
        if len(words) < self.MIN_WORDS_FOR_ACCEPT:
            return False

        unique_ratio = len(set(words)) / max(len(words), 1)
        if unique_ratio < float(current_app.config.get('LYRICS_MIN_UNIQUE_WORD_RATIO', 0.22)):
            return False

        if self._has_excessive_ngram_repetition(words, n=4):
            return False

        return True

    def _looks_translated_output(self, text: Optional[str], expected_language: Optional[str]) -> bool:
        """Detect likely translated output when we expect Vietnamese original text."""
        if not text or not expected_language:
            return False

        language = expected_language.strip().lower()
        enforce_original = current_app.config.get('LYRICS_ENFORCE_ORIGINAL_LANGUAGE', True)
        if not enforce_original:
            return False

        if not language.startswith('vi'):
            return False

        words = self._tokenize_words(text)
        if not words:
            return False

        has_vietnamese_chars = bool(re.search(r'[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]', text.lower()))
        english_hits = sum(1 for w in words if w in self._ENGLISH_STOPWORDS)
        english_ratio = english_hits / max(len(words), 1)

        if not has_vietnamese_chars and english_ratio >= 0.18:
            return True

        return False

    def _postprocess_lyrics(self, text: Optional[str]) -> Optional[str]:
        """Clean and de-repeat transcription text for prompt use."""
        if not text:
            return None

        # Remove common hallucinations (YouTube prompts, channel names, etc.)
        text = self._filter_hallucinations(text)
        
        normalized_text = re.sub(r'\s+', ' ', text).strip()
        if not normalized_text:
            return None

        chunks = re.split(r'(?<=[.!?])\s+|\n+', normalized_text)
        cleaned_chunks = []
        chunk_counts = Counter()
        previous = None

        max_chunk_repeats = int(current_app.config.get('LYRICS_MAX_SAME_CHUNK_REPEATS', 2))
        for chunk in chunks:
            candidate = chunk.strip(' ,;')
            if not candidate:
                continue
            key = self._normalize_for_repeat_check(candidate)
            if not key:
                continue
            if key == previous:
                continue
            if chunk_counts[key] >= max_chunk_repeats:
                continue
            chunk_counts[key] += 1
            cleaned_chunks.append(candidate)
            previous = key

        if not cleaned_chunks:
            return None

        rebuilt = ' '.join(cleaned_chunks)
        rebuilt_words = self._tokenize_words(rebuilt)
        if self._has_excessive_ngram_repetition(rebuilt_words, n=3):
            rebuilt = self._dedupe_rolling_ngrams(rebuilt_words, n=3)

        rebuilt = re.sub(r'\s+', ' ', rebuilt).strip(' ,;')
        
        # Add line breaks for better readability
        rebuilt = self._add_line_breaks(rebuilt)
        
        return rebuilt or None
    
    def _filter_hallucinations(self, text: str) -> str:
        """Remove common hallucination patterns from transcription."""
        hallucination_patterns = [
            # YouTube/social media prompts (Vietnamese)
            r'[Hh]ãy\s+subscribe\s+.*?(?:kênh|channel).*?(?:\.|$)',
            r'[Đđ]ừng\s+quên\s+(?:đăng\s+ký|subscribe).*?(?:\.|$)',
            r'[Nn]hấn\s+(?:like|subscribe|đăng\s+ký).*?(?:\.|$)',
            r'[Tt]heo\s+dõi\s+kênh.*?(?:\.|$)',
            r'[Cc]ảm\s+ơn\s+(?:các\s+)?bạn\s+đã\s+(?:xem|theo\s+dõi).*?(?:\.|$)',
            r'[Đđ]ể\s+không\s+bỏ\s+lỡ.*?(?:video|clip).*?(?:\.|$)',
            r'[Gg]hiền\s+[Mm]ì\s+[Gg]õ.*?(?:\.|$)',
            # English versions
            r'[Pp]lease\s+subscribe.*?(?:\.|$)',
            r'[Dd]on\'t\s+forget\s+to\s+(?:like|subscribe).*?(?:\.|$)',
            r'[Hh]it\s+the\s+(?:bell|like|subscribe).*?(?:\.|$)',
            r'[Tt]hanks\s+for\s+watching.*?(?:\.|$)',
            # Generic channel/intro/outro markers
            r'\[.*?(?:[Mm]usic|[Ii]ntro|[Oo]utro).*?\]',
            r'♪.*?♪',
        ]
        
        for pattern in hallucination_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _add_line_breaks(self, text: str) -> str:
        """Add line breaks to lyrics for better readability."""
        if not text:
            return text
            
        # Split into sentences or approximate lines
        words = text.split()
        lines = []
        current_line = []
        word_count = 0
        
        for word in words:
            current_line.append(word)
            word_count += 1
            
            # Add line break after 8-12 words, or at sentence boundaries
            ends_sentence = word.rstrip(',;').endswith(('.', '!', '?'))
            
            if ends_sentence and word_count >= 4:
                # End line at sentence boundary if we have at least 4 words
                lines.append(' '.join(current_line))
                current_line = []
                word_count = 0
            elif word_count >= 10:
                # Force line break after ~10 words
                lines.append(' '.join(current_line))
                current_line = []
                word_count = 0
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)

    def _apply_language_post_corrections(self, text: Optional[str], language: Optional[str]) -> Optional[str]:
        """Apply lightweight language-specific typo corrections after post-processing."""
        if not text:
            return text

        normalized_language = (language or '').strip().lower()
        if not normalized_language.startswith('vi'):
            return text

        corrected = text
        for pattern, replacement in self._VIETNAMESE_COMMON_FIXES:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

        custom_fixes = self._get_vietnamese_custom_corrections()
        for wrong, right in custom_fixes.items():
            corrected = re.sub(re.escape(wrong), right, corrected, flags=re.IGNORECASE)

        # Collapse horizontal whitespace only, preserve line breaks
        corrected = re.sub(r'[^\S\n]+', ' ', corrected)
        corrected = re.sub(r'\n{3,}', '\n\n', corrected)
        corrected = corrected.strip()
        return corrected or text

    def _get_vietnamese_custom_corrections(self):
        raw_json = current_app.config.get('LYRICS_VI_CUSTOM_CORRECTIONS_JSON')
        if not raw_json:
            return {}

        try:
            parsed = json.loads(raw_json)
        except Exception as exc:
            current_app.logger.warning(f'Invalid LYRICS_VI_CUSTOM_CORRECTIONS_JSON: {exc}')
            return {}

        if not isinstance(parsed, dict):
            current_app.logger.warning('LYRICS_VI_CUSTOM_CORRECTIONS_JSON must be a JSON object')
            return {}

        normalized = {}
        for wrong, right in parsed.items():
            if isinstance(wrong, str) and isinstance(right, str) and wrong.strip() and right.strip():
                normalized[wrong.strip()] = right.strip()

        return normalized

    def _has_excessive_ngram_repetition(self, words, n: int = 4) -> bool:
        if len(words) < n * 2:
            return False

        ngrams = [' '.join(words[i:i + n]) for i in range(len(words) - n + 1)]
        if not ngrams:
            return False

        most_common_count = Counter(ngrams).most_common(1)[0][1]
        max_ratio = float(current_app.config.get('LYRICS_MAX_REPEATED_NGRAM_RATIO', 0.08))
        return (most_common_count / max(len(ngrams), 1)) > max_ratio

    @staticmethod
    def _dedupe_rolling_ngrams(words, n: int = 3) -> str:
        if len(words) < n * 2:
            return ' '.join(words)

        output = []
        seen_ngrams = set()
        i = 0
        while i < len(words):
            if i + n <= len(words):
                ngram = tuple(words[i:i + n])
                if ngram in seen_ngrams:
                    i += n
                    continue
                seen_ngrams.add(ngram)
            output.append(words[i])
            i += 1

        return ' '.join(output)

    @staticmethod
    def _tokenize_words(text: str):
        # Support Vietnamese and other Unicode characters, not just English a-z
        # Match sequences of letters (including Unicode) and apostrophes
        return re.findall(r"[\w']+", text.lower(), re.UNICODE)

    @staticmethod
    def _normalize_for_repeat_check(text: str) -> str:
        # Preserve Unicode characters (Vietnamese, etc.), only remove punctuation except apostrophes
        # Keep letters (Unicode), digits, apostrophes, and spaces
        cleaned = re.sub(r"[^\w\s']", '', text.lower(), flags=re.UNICODE)
        return re.sub(r"\s+", ' ', cleaned).strip()
    
    def _download_audio_file(self, audio_url: str, temp_dir: str) -> str:
        """Download remote audio URL to a temporary local file."""
        max_size_mb = int(current_app.config.get('LYRICS_MAX_DOWNLOAD_MB', 30))
        max_size_bytes = max_size_mb * 1024 * 1024

        response = requests.get(audio_url, stream=True, timeout=45)
        response.raise_for_status()

        extension = self._guess_extension_helper(audio_url, response.headers.get('Content-Type', ''))
        local_file_path = os.path.join(temp_dir, f'input{extension}')

        bytes_written = 0
        with open(local_file_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if bytes_written > max_size_bytes:
                    raise ValueError(f'Audio file exceeds limit of {max_size_mb}MB')
                out_file.write(chunk)

        return local_file_path
    
    @staticmethod
    def _guess_extension_helper(audio_url: str, content_type: str) -> str:
        lower_content = (content_type or '').lower()
        if 'mpeg' in lower_content or audio_url.lower().endswith('.mp3'):
            return '.mp3'
        if 'wav' in lower_content or audio_url.lower().endswith('.wav'):
            return '.wav'
        if 'flac' in lower_content or audio_url.lower().endswith('.flac'):
            return '.flac'
        if 'ogg' in lower_content or audio_url.lower().endswith('.ogg'):
            return '.ogg'
        if 'mp4' in lower_content or audio_url.lower().endswith('.m4a'):
            return '.m4a'
        return '.tmp'

    @staticmethod
    def _normalize_tag_value(value) -> Optional[str]:
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


class LyricsExtractionServiceEnhanced(LyricsExtractionServiceLegacy):
    """
    Enhanced lyrics extraction with improved LRCLIB integration.
    
    Improvements:
    - Persistent caching of LRCLIB results
    - Fuzzy matching with scoring algorithm
    - Multiple fallback search strategies
    - Better error handling with exponential backoff
    - Support for synced lyrics (LRC format)
    """
    
    def extract_lyrics(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract lyrics using enhanced multi-tier fallback chain.

        Tier 1: Embedded metadata (free, instant)
        Tier 2a: Cache lookup (instant)
        Tier 2b: LRCLIB API with enhanced matching (free)
        Tier 3: AssemblyAI cloud transcription

        Returns:
            Tuple of (lyrics, source, error)
        """
        if not current_app.config.get('LYRICS_EXTRACTION_ENABLED', True):
            return None, None, 'Lyrics extraction is disabled'

        if not audio_url and not local_file_path:
            return None, None, 'No audio source provided'

        temp_dir = tempfile.mkdtemp(prefix='lyrics_extract_')
        try:
            # Resolve audio file path
            target_path = local_file_path
            if not target_path:
                target_path = self._download_audio_file(audio_url, temp_dir)

            # --- Tier 1: Embedded metadata ---
            metadata_lyrics = self._extract_metadata_lyrics(target_path)
            if metadata_lyrics:
                current_app.logger.info('Lyrics resolved via Tier 1: embedded metadata')
                return metadata_lyrics, 'metadata', None

            # Extract artist/title for LRCLIB lookup
            artist, title = self._extract_artist_title(target_path)
            
            # --- Tier 2a: Cache lookup ---
            if artist and title:
                cached_lyrics = LyricsCacheManager.get_cached_lyrics(artist, title)
                if cached_lyrics:
                    current_app.logger.info('Lyrics resolved via Tier 2a: cache')
                    return cached_lyrics['lyrics'], 'lrclib_cache', None

            # --- Tier 2b: Enhanced LRCLIB API lookup ---
            lrclib_lyrics, lrclib_metadata = self._lookup_lyrics_lrclib_enhanced(
                target_path, artist, title
            )
            if lrclib_lyrics:
                current_app.logger.info('Lyrics resolved via Tier 2b: LRCLIB (enhanced)')
                
                # Cache the result
                if artist and title and lrclib_metadata:
                    LyricsCacheManager.cache_lyrics(
                        artist=artist,
                        title=title,
                        lyrics_text=lrclib_lyrics,
                        synced_lyrics=lrclib_metadata.get('synced_lyrics'),
                        lrclib_id=lrclib_metadata.get('id'),
                        album_name=lrclib_metadata.get('album_name'),
                        duration=lrclib_metadata.get('duration'),
                        match_score=lrclib_metadata.get('match_score')
                    )
                
                return lrclib_lyrics, 'lrclib', None

            # --- Tier 3: AssemblyAI transcription ---
            # (Keep existing implementation from parent class)
            transcription_target = target_path
            if current_app.config.get('LYRICS_VOCAL_SEPARATION_ENABLED', False):
                separated_path = self._separate_vocals_with_demucs(target_path, temp_dir)
                if separated_path:
                    transcription_target = separated_path

            raw_lyrics = self._transcribe_with_assemblyai(
                transcription_target,
                language_override=whisper_language_override,
            )

            if raw_lyrics:
                cleaned = self._postprocess_lyrics(raw_lyrics)
                language = whisper_language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE')
                final = self._apply_language_post_corrections(cleaned, language)

                if final and self._is_transcription_usable(final, expected_language=language):
                    current_app.logger.info('Lyrics resolved via Tier 3: AssemblyAI')
                    return final, 'assemblyai', None

            return None, None, 'No lyrics detected from all tiers'

        except Exception as exc:
            current_app.logger.warning(f'Lyrics extraction failed: {exc}')
            return None, None, str(exc)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _lookup_lyrics_lrclib_enhanced(
        self,
        audio_path: str,
        artist: Optional[str],
        title: Optional[str]
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Enhanced LRCLIB lookup with fuzzy matching and fallback strategies.
        
        Returns:
            Tuple of (lyrics_text, metadata)
        """
        if not current_app.config.get('LYRICS_USE_LRCLIB', False):
            return None, None

        if not title:
            current_app.logger.debug('Missing title, skipping LRCLIB lookup')
            return None, None

        client = LRCLIBClient()
        
        # Extract additional metadata for better matching
        duration = self._extract_duration(audio_path)
        album = self._extract_album(audio_path)
        
        # Strategy 1: Search with all available metadata
        results = client.search_lyrics(
            track_name=title,
            artist_name=artist,
            album_name=album,
            duration=duration
        )
        
        if not results:
            # Strategy 2: Try without artist (broaden search)
            if artist:
                current_app.logger.debug('Retrying LRCLIB search without artist')
                results = client.search_lyrics(
                    track_name=title,
                    album_name=album,
                    duration=duration
                )
        
        if not results:
            # Strategy 3: Try with cleaned/simplified title
            cleaned_title = self._clean_track_title(title)
            if cleaned_title != title:
                current_app.logger.debug(f'Retrying with cleaned title: {cleaned_title}')
                results = client.search_lyrics(
                    track_name=cleaned_title,
                    artist_name=artist,
                    duration=duration
                )
        
        if not results:
            current_app.logger.debug(f'No LRCLIB results for "{title}"')
            return None, None
        
        # Get best match (highest score)
        best_match = results[0]
        match_score = best_match.get('match_score', 0)
        
        # Only accept matches with reasonable confidence
        min_score = float(current_app.config.get('LRCLIB_MIN_MATCH_SCORE', 50.0))
        if match_score < min_score:
            current_app.logger.info(
                f'LRCLIB best match score {match_score:.1f} below threshold {min_score}'
            )
            return None, None
        
        # Check for instrumental
        if best_match.get('instrumental', False):
            current_app.logger.info('LRCLIB match is instrumental')
            return None, None
        
        # Prefer synced lyrics, fallback to plain
        synced_lyrics = best_match.get('syncedLyrics', '').strip()
        plain_lyrics = best_match.get('plainLyrics', '').strip()
        
        lyrics_text = plain_lyrics  # Use plain for now
        
        # Parse synced lyrics if needed
        if synced_lyrics and current_app.config.get('LRCLIB_USE_SYNCED_LYRICS', False):
            parsed_plain = self._parse_lrc_to_plain(synced_lyrics)
            if parsed_plain:
                lyrics_text = parsed_plain
        
        if not lyrics_text:
            current_app.logger.debug('LRCLIB match has no lyrics content')
            return None, None
        
        # Prepare metadata
        metadata = {
            'id': best_match.get('id'),
            'track_name': best_match.get('trackName'),
            'artist_name': best_match.get('artistName'),
            'album_name': best_match.get('albumName'),
            'duration': best_match.get('duration'),
            'synced_lyrics': synced_lyrics if synced_lyrics else None,
            'match_score': match_score
        }
        
        current_app.logger.info(
            f'LRCLIB lyrics found: "{best_match.get("trackName")}" by '
            f'"{best_match.get("artistName")}" (score: {match_score:.1f}, '
            f'{len(lyrics_text)} chars)'
        )
        
        return lyrics_text, metadata
    
    def _extract_duration(self, audio_path: str) -> Optional[int]:
        """Extract audio duration in seconds."""
        try:
            mutagen_module = importlib.import_module('mutagen')
            mutagen_file_loader = getattr(mutagen_module, 'File')
            
            audio_file = mutagen_file_loader(audio_path)
            if audio_file and hasattr(audio_file.info, 'length'):
                return int(audio_file.info.length)
        except Exception as exc:
            current_app.logger.debug(f'Could not extract duration: {exc}')
        
        return None
    
    def _extract_album(self, audio_path: str) -> Optional[str]:
        """Extract album name from metadata."""
        try:
            mutagen_module = importlib.import_module('mutagen')
            mutagen_file_loader = getattr(mutagen_module, 'File')
            
            audio_file = mutagen_file_loader(audio_path)
            if not audio_file or not getattr(audio_file, 'tags', None):
                return None
            
            tags = audio_file.tags
            
            # ID3 tags
            if 'TALB' in tags:
                return self._normalize_tag_value(tags['TALB'])
            
            # Vorbis comments
            for key in ['album', 'ALBUM']:
                if key in tags:
                    val = tags[key]
                    album = val[0] if isinstance(val, list) else str(val)
                    return album.strip() if album else None
            
            # MP4 atoms
            if '\xa9alb' in tags:
                val = tags['\xa9alb']
                album = val[0] if isinstance(val, list) else str(val)
                return album.strip() if album else None
                
        except Exception as exc:
            current_app.logger.debug(f'Could not extract album: {exc}')
        
        return None
    
    @staticmethod
    def _clean_track_title(title: str) -> str:
        """
        Remove noise from track title for better matching.
        E.g., "Song Name (Remix)" -> "Song Name"
        """
        if not title:
            return title
        
        # Remove parentheticals (Remix), [feat. Artist], etc.
        cleaned = re.sub(r'\([^)]*(?:remix|radio edit|album version|live)[^)]*\)', '', title, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[[^\]]*feat[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
        
        # Remove trailing dashes or other noise
        cleaned = re.sub(r'\s*[-–—]\s*$', '', cleaned)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    @staticmethod
    def _parse_lrc_to_plain(lrc_content: str) -> Optional[str]:
        """
        Parse LRC (synced lyrics) format to plain text.
        
        LRC format: [mm:ss.xx]lyrics line
        """
        if not lrc_content:
            return None
        
        lines = []
        for line in lrc_content.split('\n'):
            # Remove timestamp markers
            cleaned = re.sub(r'\[\d+:\d+\.\d+\]', '', line).strip()
            if cleaned:
                lines.append(cleaned)
        
        return '\n'.join(lines) if lines else None
