"""
Asynchronous lyrics extraction job service.
Uses in-process worker threads to run extraction without blocking API requests.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Set
from urllib.parse import unquote, urlparse

from flask import current_app

from app import db
from app.models import AudioLibrary
from app.services.lyrics_extraction_service import LyricsExtractionService


class LyricsJobService:
    """Manage asynchronous lyrics extraction jobs."""

    _executor = None
    _executor_workers = None
    _active_job_ids: Set[str] = set()
    _job_language_overrides = {}
    _lock = Lock()

    @classmethod
    def enqueue_extraction(cls, audio_item_id: str, whisper_language_override: str = None) -> bool:
        """Queue extraction for an audio library item."""
        app = current_app._get_current_object()

        with cls._lock:
            if audio_item_id in cls._active_job_ids:
                return False
            cls._active_job_ids.add(audio_item_id)
            if whisper_language_override:
                cls._job_language_overrides[audio_item_id] = whisper_language_override

        cls._ensure_executor(app)

        try:
            cls._executor.submit(cls._process_extraction_job, app, audio_item_id)
            return True
        except Exception:
            with cls._lock:
                cls._active_job_ids.discard(audio_item_id)
            raise

    @classmethod
    def _ensure_executor(cls, app):
        workers = int(app.config.get('LYRICS_EXTRACTION_WORKERS', 2))
        if cls._executor is None or cls._executor_workers != workers:
            cls._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='lyrics-worker')
            cls._executor_workers = workers

    @classmethod
    def _process_extraction_job(cls, app, audio_item_id: str):
        """Run one extraction task in background."""
        try:
            with app.app_context():
                # Mark as processing and gather info needed for extraction
                audio_item = AudioLibrary.query.get(audio_item_id)
                if not audio_item:
                    return

                audio_url = audio_item.audio_url
                audio_item.lyrics_extraction_status = 'processing'
                audio_item.lyrics_extraction_error = None
                db.session.commit()

                # Close the DB session before the long-running extraction
                # to avoid idle-in-transaction timeouts from PostgreSQL.
                db.session.remove()

                extractor = LyricsExtractionService()
                language_override = cls._job_language_overrides.get(audio_item_id)
                local_file_path = cls._resolve_local_audio_path(
                    audio_url,
                    app.config.get('UPLOAD_FOLDER')
                )
                lyrics, source, error = extractor.extract_lyrics(
                    audio_url=audio_url,
                    local_file_path=local_file_path,
                    whisper_language_override=language_override
                )

                # Open a fresh DB session to save the result
                audio_item = AudioLibrary.query.get(audio_item_id)
                if not audio_item:
                    return

                if lyrics:
                    audio_item.lyrics = lyrics
                    audio_item.lyrics_source = source
                    audio_item.lyrics_extraction_status = 'completed'
                    audio_item.lyrics_extraction_error = None
                else:
                    audio_item.lyrics_extraction_status = 'failed'
                    audio_item.lyrics_extraction_error = error or 'No lyrics detected'

                db.session.commit()

        except Exception as exc:
            try:
                with app.app_context():
                    db.session.remove()
                    audio_item = AudioLibrary.query.get(audio_item_id)
                    if audio_item:
                        audio_item.lyrics_extraction_status = 'failed'
                        audio_item.lyrics_extraction_error = str(exc)[:500]
                        db.session.commit()
            except Exception:
                pass
            with app.app_context():
                app.logger.error(f'Async lyrics extraction failed for {audio_item_id}: {exc}')
        finally:
            with cls._lock:
                cls._active_job_ids.discard(audio_item_id)
                cls._job_language_overrides.pop(audio_item_id, None)

    @staticmethod
    def _resolve_local_audio_path(audio_url: str, upload_folder: str):
        """Map local serve-audio URLs back to on-disk files when available."""
        if not audio_url or not upload_folder:
            return None

        try:
            parsed = urlparse(audio_url)
            if '/serve-audio/' not in parsed.path:
                return None

            filename = os.path.basename(unquote(parsed.path))
            if not filename:
                return None

            candidate = os.path.join(upload_folder, filename)
            if os.path.exists(candidate):
                return candidate
        except Exception:
            return None

        return None
