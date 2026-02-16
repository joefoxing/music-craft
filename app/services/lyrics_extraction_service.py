"""
Lyrics extraction service.
Supports both microservice API and legacy local extraction.
"""
import os
import json
import re
import shutil
import subprocess
import tempfile
import importlib
import time
from collections import Counter
from typing import Optional, Tuple

import requests
from flask import current_app


class LyricsExtractionService:
    """
    Service for extracting lyrics from audio.
    
    This service can use either:
    1. NEW: External microservice API (recommended, production-grade)
    2. LEGACY: Local Whisper processing (fallback)
    
    Set LYRICS_USE_MICROSERVICE=true to enable microservice mode.
    """
    
    def extract_lyrics(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract lyrics from audio source.

        Returns:
            Tuple of (lyrics, source, error)
        """
        if not current_app.config.get('LYRICS_EXTRACTION_ENABLED', True):
            return None, None, 'Lyrics extraction is disabled'

        # Check if microservice mode is enabled
        use_microservice = current_app.config.get('LYRICS_USE_MICROSERVICE', False)
        
        if use_microservice:
            return self._extract_via_microservice(
                audio_url=audio_url,
                local_file_path=local_file_path,
                language_override=whisper_language_override
            )
        else:
            return self._extract_legacy(
                audio_url=audio_url,
                local_file_path=local_file_path,
                whisper_language_override=whisper_language_override
            )
    
    def _extract_via_microservice(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract lyrics using the microservice API."""
        try:
            microservice_url = current_app.config.get('LYRICS_MICROSERVICE_URL', 'http://localhost:8000/v1')
            timeout = current_app.config.get('LYRICS_MICROSERVICE_TIMEOUT', 600)
            poll_interval = current_app.config.get('LYRICS_MICROSERVICE_POLL_INTERVAL', 2)
            
            # Prepare audio file
            temp_file_cleanup = None
            if local_file_path:
                audio_path = local_file_path
            elif audio_url:
                # Download to temp location
                temp_file_cleanup = tempfile.mkdtemp(prefix='lyrics_download_')
                audio_path = self._download_audio(audio_url, temp_file_cleanup)
            else:
                return None, None, 'No audio source provided'
            
            try:
                # Submit job to microservice
                current_app.logger.info(f'Submitting lyrics extraction job to microservice: {microservice_url}')
                
                with open(audio_path, 'rb') as f:
                    files = {'file': f}
                    data = {
                        'language_hint': language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE') or 'auto',
                        'timestamps': 'none'
                    }
                    
                    response = requests.post(
                        f"{microservice_url}/lyrics",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    job_data = response.json()
                    job_id = job_data.get('job_id')
                    
                    if not job_id:
                        return None, None, 'Microservice did not return job_id'
                    
                    current_app.logger.info(f'Job submitted: {job_id}')
                
                # Poll for result
                start_time = time.time()
                
                while True:
                    elapsed = time.time() - start_time
                    
                    if elapsed > timeout:
                        return None, None, f'Microservice timeout after {timeout}s'
                    
                    try:
                        response = requests.get(
                            f"{microservice_url}/lyrics/{job_id}",
                            timeout=10
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        status = result.get('status')
                        
                        if status == 'done':
                            lyrics = result.get('result', {}).get('lyrics')
                            if lyrics:
                                current_app.logger.info(f'Lyrics extracted via microservice: {len(lyrics)} chars')
                                return lyrics, 'microservice', None
                            else:
                                return None, None, 'Microservice returned empty lyrics'
                        
                        elif status == 'error':
                            error_msg = result.get('error', {}).get('message', 'Unknown error')
                            current_app.logger.error(f'Microservice error: {error_msg}')
                            return None, None, f'Microservice error: {error_msg}'
                        
                        elif status == 'not_found':
                            return None, None, 'Job not found or expired'
                        
                        # Still processing, wait and retry
                        time.sleep(poll_interval)
                    
                    except requests.exceptions.RequestException as e:
                        current_app.logger.error(f'Error polling microservice: {e}')
                        time.sleep(poll_interval)
            
            finally:
                # Cleanup temp download
                if temp_file_cleanup and os.path.exists(temp_file_cleanup):
                    shutil.rmtree(temp_file_cleanup, ignore_errors=True)
        
        except Exception as e:
            current_app.logger.error(f'Microservice lyrics extraction failed: {e}')
            return None, None, f'Microservice error: {str(e)}'
    
    def _extract_legacy(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Legacy lyrics extraction using local Whisper processing."""
        legacy_service = LyricsExtractionServiceLegacy()
        return legacy_service.extract_lyrics(
            audio_url=audio_url,
            local_file_path=local_file_path,
            whisper_language_override=whisper_language_override
        )
    
    def _download_audio(self, audio_url: str, temp_dir: str) -> str:
        """Download remote audio URL to a temporary local file."""
        max_size_mb = int(current_app.config.get('LYRICS_MAX_DOWNLOAD_MB', 30))
        max_size_bytes = max_size_mb * 1024 * 1024

        response = requests.get(audio_url, stream=True, timeout=45)
        response.raise_for_status()

        extension = self._guess_extension(audio_url, response.headers.get('Content-Type', ''))
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
    def _guess_extension(audio_url: str, content_type: str) -> str:
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


class LyricsExtractionServiceLegacy:
    """Legacy implementation of lyrics extraction (kept for backward compatibility)."""
    
    METADATA_KEYS = {
        'lyrics',
        'unsyncedlyrics',
        '\u00a9lyr',
        'lyric',
    }

    MIN_WORDS_FOR_ACCEPT = 6
    _WHISPER_MODEL_RANK = {
        'tiny': 1,
        'base': 2,
        'small': 3,
        'medium': 4,
        'large': 5,
        'turbo': 5,
    }
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
        Extract lyrics from audio source.

        Returns:
            Tuple of (lyrics, source, error)
            source is one of: metadata, whisper
        """
        if not current_app.config.get('LYRICS_EXTRACTION_ENABLED', True):
            return None, None, 'Lyrics extraction is disabled'

        if not audio_url and not local_file_path:
            return None, None, 'No audio source provided'

        temp_dir = tempfile.mkdtemp(prefix='lyrics_extract_')
        try:
            target_path = local_file_path
            if not target_path:
                    target_path = self._download_audio_file(audio_url, temp_dir)
            metadata_lyrics = self._extract_metadata_lyrics(target_path)
            if metadata_lyrics:
                return metadata_lyrics, 'metadata', None

            transcription_target = target_path
            separated_path = None
            if current_app.config.get('LYRICS_VOCAL_SEPARATION_ENABLED', False):
                separated_path = self._separate_vocals_with_demucs(target_path, temp_dir)
                if separated_path:
                    transcription_target = separated_path

            whisper_lyrics = self._transcribe_with_whisper(
                transcription_target,
                language_override=whisper_language_override
            )
            expected_language = whisper_language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE')
            if self._is_transcription_usable(whisper_lyrics, expected_language=expected_language):
                return whisper_lyrics, 'whisper', None

            if self._looks_translated_output(whisper_lyrics, expected_language):
                retried_lyrics = self._transcribe_with_whisper(
                    transcription_target,
                    language_override=whisper_language_override,
                    force_original_language=True
                )
                if self._is_transcription_usable(retried_lyrics, expected_language=expected_language):
                    return retried_lyrics, 'whisper', None

            fallback_model = current_app.config.get('LYRICS_WHISPER_FALLBACK_MODEL')
            primary_model = current_app.config.get('LYRICS_WHISPER_MODEL', 'base')
            if self._should_try_fallback_model(primary_model, fallback_model):
                fallback_lyrics = self._transcribe_with_whisper(
                    transcription_target,
                    model_name=fallback_model,
                    language_override=whisper_language_override
                )
                if self._is_transcription_usable(fallback_lyrics, expected_language=expected_language):
                    return fallback_lyrics, 'whisper', None

            auto_retry_separation = current_app.config.get('LYRICS_AUTO_RETRY_WITH_VOCAL_SEPARATION', True)
            if auto_retry_separation and not separated_path:
                separated_path = self._separate_vocals_with_demucs(target_path, temp_dir)
                if separated_path:
                    separated_lyrics = self._transcribe_with_whisper(
                        separated_path,
                        language_override=whisper_language_override
                    )
                    if self._is_transcription_usable(separated_lyrics, expected_language=expected_language):
                        return separated_lyrics, 'whisper+demucs', None

                    if self._should_try_fallback_model(primary_model, fallback_model):
                        separated_fallback_lyrics = self._transcribe_with_whisper(
                            separated_path,
                            model_name=fallback_model,
                            language_override=whisper_language_override
                        )
                        if self._is_transcription_usable(separated_fallback_lyrics, expected_language=expected_language):
                            return separated_fallback_lyrics, 'whisper+demucs', None

            cleaned_candidate = self._postprocess_lyrics(whisper_lyrics)
            if cleaned_candidate and len(self._tokenize_words(cleaned_candidate)) >= self.MIN_WORDS_FOR_ACCEPT:
                current_app.logger.info('Returning low-confidence cleaned transcription')
                return cleaned_candidate, 'whisper-low-confidence', None

            return None, None, 'No lyrics detected from metadata or transcription'

        except Exception as exc:
            current_app.logger.warning(f'Lyrics extraction failed: {exc}')
            return None, None, str(exc)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

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

    def _transcribe_with_whisper(
        self,
        audio_path: str,
        model_name: Optional[str] = None,
        language_override: Optional[str] = None,
        force_original_language: bool = False
    ) -> Optional[str]:
        """Transcribe audio with Whisper."""
        try:
            whisper = importlib.import_module('whisper')
        except Exception as exc:
            current_app.logger.info(f'Whisper unavailable for transcription: {exc}')
            return None

        model_name = model_name or current_app.config.get('LYRICS_WHISPER_MODEL', 'base')
        language = language_override or current_app.config.get('LYRICS_WHISPER_LANGUAGE')
        transcribe_options = {
            'task': 'transcribe',
            'temperature': float(current_app.config.get('LYRICS_WHISPER_TEMPERATURE', 0.0)),
            'beam_size': int(current_app.config.get('LYRICS_WHISPER_BEAM_SIZE', 5)),
            'best_of': int(current_app.config.get('LYRICS_WHISPER_BEST_OF', 5)),
            'patience': float(current_app.config.get('LYRICS_WHISPER_PATIENCE', 1.0)),
            'condition_on_previous_text': current_app.config.get('LYRICS_WHISPER_CONDITION_ON_PREVIOUS_TEXT', False),
            'compression_ratio_threshold': float(current_app.config.get('LYRICS_WHISPER_COMPRESSION_RATIO_THRESHOLD', 2.2)),
            'logprob_threshold': float(current_app.config.get('LYRICS_WHISPER_LOGPROB_THRESHOLD', -1.0)),
            'no_speech_threshold': float(current_app.config.get('LYRICS_WHISPER_NO_SPEECH_THRESHOLD', 0.6)),
        }
        if language:
            transcribe_options['language'] = language
        if force_original_language and language:
            transcribe_options['initial_prompt'] = (
                'Transcribe exactly in the original spoken language. '
                'Do not translate to English. Keep original wording only.'
            )

        try:
            model = whisper.load_model(model_name)
            result = model.transcribe(audio_path, **transcribe_options)
            text = self._extract_text_from_whisper_result(result)
            # DEBUG: Log raw Whisper output
            current_app.logger.info(f'[DEBUG] Raw Whisper output: len={len(text) if text else 0}, repr={repr(text[:120] if text else "")}')
            cleaned = self._postprocess_lyrics(text)
            # DEBUG: Log after postprocessing
            current_app.logger.info(f'[DEBUG] After postprocess: len={len(cleaned) if cleaned else 0}, repr={repr(cleaned[:120] if cleaned else "")}')
            final = self._apply_language_post_corrections(cleaned, language)
            # DEBUG: Log final output
            current_app.logger.info(f'[DEBUG] Final lyrics: len={len(final) if final else 0}, repr={repr(final[:120] if final else "")}')
            return final
        except Exception as exc:
            current_app.logger.info(f'Whisper transcription failed: {exc}')
            return None

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

        corrected = re.sub(r'\s+', ' ', corrected).strip()
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

    def _extract_text_from_whisper_result(self, result) -> Optional[str]:
        """Extract text from Whisper result, preferring cleaned segments."""
        if not result:
            return None

        segments = result.get('segments') or []
        if segments:
            cleaned_segments = []
            previous_normalized = None
            for segment in segments:
                segment_text = (segment.get('text') or '').strip()
                if not segment_text:
                    continue
                normalized = self._normalize_for_repeat_check(segment_text)
                if normalized == previous_normalized:
                    continue
                cleaned_segments.append(segment_text)
                previous_normalized = normalized

            if cleaned_segments:
                return '\n'.join(cleaned_segments).strip()

        return (result.get('text') or '').strip() or None

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
        return rebuilt or None

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

    def _should_try_fallback_model(self, primary_model: str, fallback_model: Optional[str]) -> bool:
        if not fallback_model or fallback_model == primary_model:
            return False

        allow_uncached_heavier = current_app.config.get('LYRICS_ALLOW_UNCACHED_HEAVIER_FALLBACK', False)
        if allow_uncached_heavier:
            return True

        if self._is_heavier_model(fallback_model, primary_model) and not self._is_whisper_model_cached(fallback_model):
            current_app.logger.info(
                f'Skipping fallback Whisper model {fallback_model}: not cached and heavier than primary model {primary_model}'
            )
            return False

        return True

    def _is_heavier_model(self, candidate_model: str, baseline_model: str) -> bool:
        return self._get_model_rank(candidate_model) > self._get_model_rank(baseline_model)

    def _get_model_rank(self, model_name: str) -> int:
        normalized = (model_name or '').lower().split('.')[0]
        return self._WHISPER_MODEL_RANK.get(normalized, 0)

    @staticmethod
    def _is_whisper_model_cached(model_name: str) -> bool:
        cache_root = os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache')
        whisper_cache_dir = os.path.join(cache_root, 'whisper')
        candidate_file = os.path.join(whisper_cache_dir, f'{model_name}.pt')
        return os.path.exists(candidate_file)

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
