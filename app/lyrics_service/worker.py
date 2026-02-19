"""
RQ worker for processing lyrics extraction jobs.
Runs the full pipeline: separation -> transcription -> post-processing.
"""
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.lyrics_service import config
from app.lyrics_service.pipeline import separate, transcribe, postprocess, utils

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_lyrics_extraction(
    job_id: str,
    audio_file_path: str,
    language_hint: str = "auto",
    include_timestamps: str = "none"
) -> Dict:
    """
    Main job processing function.
    Extracts lyrics from audio file using the full pipeline.
    
    Args:
        job_id: Unique job identifier
        audio_file_path: Path to uploaded audio file
        language_hint: Language hint ('en', 'vi', 'auto')
        include_timestamps: 'none' or 'word'
    
    Returns:
        Result dictionary with lyrics, metadata, and optional timestamps
    """
    start_time = time.time()
    logger.info(f"[{job_id}] Starting lyrics extraction: {audio_file_path}")

    from rq import get_current_job

    # Base result structure
    result: Dict = {
        "job_id": job_id,
        "status": "running",
        "result": None,
        "meta": {
            "duration_sec": None,
            "language_detected": "unknown",
            "model": {
                "separator": config.DEMUCS_MODEL if config.ENABLE_VOCAL_SEPARATION else None,
                "asr": f"faster-whisper {config.WHISPER_MODEL_SIZE}"
            }
        },
        "error": None,
    }

    temp_manager = None

    # RQ job progress reporting helper
    job = get_current_job()
    def set_progress(percent: int, stage: str = None, extra: Dict = None):
        try:
            if not job:
                return
            job.meta = job.meta or {}
            job.meta['progress'] = int(percent)
            if stage:
                job.meta['stage'] = stage
            if extra and isinstance(extra, dict):
                job.meta.update(extra)
            job.save_meta()
        except Exception:
            pass

    try:
        set_progress(0, 'started')

        # Validate input file
        is_valid, error_msg = utils.validate_audio_file(audio_file_path, config.MAX_UPLOAD_SIZE_MB)
        if not is_valid:
            set_progress(100, 'error', {'error': error_msg})
            raise ValueError(f"Invalid audio file: {error_msg}")

        set_progress(5, 'validated')

        # Get audio duration
        duration = utils.get_audio_duration(audio_file_path)
        if duration:
            result["meta"]["duration_sec"] = round(duration, 2)
            logger.info(f"[{job_id}] Audio duration: {duration:.2f}s")

        # Create temporary working directory
        temp_manager = utils.TempFileManager(prefix=f"lyrics_{job_id}_")
        temp_dir = temp_manager.__enter__()
        logger.info(f"[{job_id}] Working directory: {temp_dir}")

        # Step 1: Preprocess audio with ffmpeg
        processed_audio = audio_file_path
        if config.PREPROCESS_AUDIO:
            logger.info(f"[{job_id}] Preprocessing audio with ffmpeg")
            preprocessed_path = str(temp_dir / "preprocessed.wav")
            success = utils.preprocess_audio_ffmpeg(audio_file_path, preprocessed_path)
            if success and os.path.exists(preprocessed_path):
                processed_audio = preprocessed_path
                logger.info(f"[{job_id}] Audio preprocessed successfully")
        set_progress(30, 'preprocessed')

        # Step 2: Vocal separation (optional)
        transcription_input = processed_audio
        if config.ENABLE_VOCAL_SEPARATION:
            logger.info(f"[{job_id}] Separating vocals with Demucs")
            separation_output_dir = str(temp_dir / "demucs_output")

            separator = separate.VocalSeparator(
                model_name=config.DEMUCS_MODEL,
                device=config.DEVICE,
                shifts=1,
                overlap=0.25
            )

            set_progress(35, 'separating')

            vocal_path = separator.separate(
                processed_audio,
                separation_output_dir,
                two_stems="vocals"
            )

            if vocal_path and os.path.exists(vocal_path):
                transcription_input = vocal_path
                logger.info(f"[{job_id}] Vocals separated successfully")
                set_progress(55, 'separated')
            else:
                logger.warning(f"[{job_id}] Vocal separation failed, using original audio")
                set_progress(45, 'separation_failed')

        # Step 3: Transcribe with faster-whisper
        logger.info(f"[{job_id}] Transcribing with Whisper model: {config.WHISPER_MODEL_SIZE}")
        set_progress(60, 'transcribing')

        # Always enable word timestamps internally for line-break formatting.
        # The include_timestamps parameter only controls whether we *return* them to the caller.
        word_timestamps = True

        transcriber = transcribe.LyricsTranscriber(
            model_size=config.WHISPER_MODEL_SIZE,
            device=config.DEVICE,
            compute_type=config.COMPUTE_TYPE,
            num_workers=1
        )

        transcribe_language = language_hint if language_hint != "auto" else None

        transcription_result = transcriber.transcribe(
            audio_path=transcription_input,
            language=transcribe_language,
            word_timestamps=word_timestamps,
            vad_filter=config.VAD_FILTER,
            beam_size=config.BEAM_SIZE,
            temperature=config.TEMPERATURE
        )

        logger.info(f"[{job_id}] Transcription complete: {len(transcription_result.get('segments', []))} segments")
        set_progress(85, 'transcribed')

        # Step 4: Post-process lyrics
        logger.info(f"[{job_id}] Post-processing lyrics")

        processed = postprocess.postprocess_lyrics(
            segments=transcription_result.get("segments"),
            include_word_timestamps=True,
            deduplicate=True
        )

        # Build result
        result["status"] = "done"
        result["result"] = {
            "lyrics": processed.get("lyrics"),
            "raw_transcript": transcription_result.get("text", ""),
        }

        # Only return word timestamps to caller if they explicitly requested them
        return_timestamps = include_timestamps in ("word", "segment")
        if return_timestamps and processed.get("words"):
            result["result"]["words"] = processed["words"]
            logger.info(f"[{job_id}] Included {len(processed['words'])} word timestamps")

        result["meta"]["language_detected"] = processed.get("language_detected", "unknown")
        if not result["meta"].get("duration_sec") and transcription_result.get("duration"):
            result["meta"]["duration_sec"] = round(transcription_result["duration"], 2)

        set_progress(90, 'postprocessing')

        elapsed = time.time() - start_time
        logger.info(f"[{job_id}] Successfully extracted lyrics in {elapsed:.2f}s")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"[{job_id}] Lyrics extraction failed after {elapsed:.2f}s: {error_msg}", exc_info=True)

        result["status"] = "error"
        result["error"] = {
            "code": "extraction_failed",
            "message": error_msg
        }
        set_progress(100, 'error', {'error': error_msg})
        return result

    finally:
        # Cleanup temporary files
        if temp_manager:
            try:
                temp_manager.__exit__(None, None, None)
            except Exception:
                pass

        # Cleanup uploaded file
        try:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            set_progress(100, 'done', {'duration_sec': result.get('meta', {}).get('duration_sec')})
            logger.info(f"[{job_id}] Cleaned up uploaded file")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to cleanup uploaded file: {e}")


if __name__ == "__main__":
    """Run RQ worker."""
    import redis
    from rq import Worker, Queue, Connection
    
    logger.info("Starting RQ worker for lyrics extraction")
    logger.info(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}")
    logger.info(f"Queue: {config.QUEUE_NAME}")
    logger.info(f"Device: {config.DEVICE}, Compute: {config.COMPUTE_TYPE}")
    logger.info(f"Whisper model: {config.WHISPER_MODEL_SIZE}")
    logger.info(f"Vocal separation: {config.ENABLE_VOCAL_SEPARATION}")

    # Connect to Redis
    redis_conn = redis.from_url(config.get_redis_url())

    # Create queue
    queue = Queue(config.QUEUE_NAME, connection=redis_conn)

    # Start worker
    with Connection(redis_conn):
        worker = Worker([queue], name=f"{config.SERVICE_NAME}-worker-{os.getpid()}")
        logger.info("Worker started, waiting for jobs...")
        worker.work()
