"""
Speech-to-text transcription module using faster-whisper.
Optimized for singing voice with Vietnamese/English mixed support.
"""
import logging
from typing import Dict, List, Optional, Literal

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("faster-whisper not installed")
    FASTER_WHISPER_AVAILABLE = False

LanguageCode = Literal["en", "vi", "auto"]


class LyricsTranscriber:
    """Wrapper for faster-whisper transcription tuned for singing."""
    
    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
        num_workers: int = 1
    ):
        """
        Initialize transcriber.
        
        Args:
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3', 'turbo')
            device: 'cpu' or 'cuda'
            compute_type: 
                - CPU: 'int8', 'int8_float16', 'float32'
                - GPU: 'float16', 'int8_float16'
            num_workers: Number of parallel workers for CPU inference
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError("faster-whisper is not installed. Install with: pip install faster-whisper")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.num_workers = num_workers
        
        logger.info(f"Loading Whisper model: {model_size} on {device} with {compute_type}")
        
        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                num_workers=num_workers
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: str,
        language: LanguageCode = "auto",
        word_timestamps: bool = False,
        vad_filter: bool = True,
        beam_size: int = 5,
        temperature: float = 0.0
    ) -> Dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language hint ('en', 'vi', 'auto')
            word_timestamps: Extract word-level timestamps
            vad_filter: Use voice activity detection to filter silence
            beam_size: Beam size for decoding (higher=better but slower)
            temperature: Sampling temperature (0.0=deterministic)
        
        Returns:
            Dict with:
                - text: Full transcription text
                - segments: List of segment dicts with timing and text
                - language: Detected language code
        """
        # Prepare transcription options
        transcribe_kwargs = {
            "word_timestamps": word_timestamps,
            "vad_filter": vad_filter,
            "beam_size": beam_size,
            "temperature": temperature,
            "condition_on_previous_text": False,  # Better for singing
            "compression_ratio_threshold": 2.4,
            "log_prob_threshold": -1.0,
            "no_speech_threshold": 0.6,  # Increased to reduce hallucinations (was 0.4)
            "initial_prompt": "♪ Music lyrics. No commentary or repetition.",  # Guide model
        }
        
        # Tune VAD parameters to be less aggressive for singing
        # Default Silero VAD is tuned for speech and removes singing sections
        if vad_filter:
            transcribe_kwargs["vad_parameters"] = {
                "onset": 0.35,                  # Lower voice onset threshold (default 0.5)
                "offset": 0.2,                  # Lower offset threshold (default 0.35)
                "min_speech_duration_ms": 100,   # Minimum speech segment (default 0)
                "min_silence_duration_ms": 600,  # Shorter silence to split (default 2000ms)
                "speech_pad_ms": 300,            # Pad speech segments (default 400ms)
            }
        
        # Set language if not auto
        if language and language != "auto":
            transcribe_kwargs["language"] = language
        
        logger.info(f"Transcribing audio: {audio_path}")
        logger.debug(f"Transcription options: {transcribe_kwargs}")
        
        try:
            segments, info = self.model.transcribe(audio_path, **transcribe_kwargs)
            
            # Convert generator to list and extract info
            segments_list = []
            full_text_parts = []
            
            for segment in segments:
                segment_dict = {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip()
                }
                
                # Add word-level info if available
                if word_timestamps and hasattr(segment, 'words'):
                    segment_dict["words"] = [
                        {
                            "word": word.word.strip(),
                            "start": round(word.start, 2),
                            "end": round(word.end, 2)
                        }
                        for word in segment.words
                    ]
                
                segments_list.append(segment_dict)
                full_text_parts.append(segment.text.strip())
            
            full_text = " ".join(full_text_parts)
            
            # DEBUG: Log raw Whisper output
            logger.info(f"[DEBUG] Raw Whisper text: len={len(full_text)}, repr={repr(full_text[:120])}")
            
            result = {
                "text": full_text,
                "segments": segments_list,
                "language": info.language if hasattr(info, 'language') else "unknown",
                "duration": info.duration if hasattr(info, 'duration') else None
            }
            
            logger.info(f"Transcription complete: {len(segments_list)} segments, language={result['language']}")
            
            return result
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise


def transcribe_audio(
    audio_path: str,
    model_size: str = "large-v3",
    device: str = "cpu",
    compute_type: str = "int8",
    language: LanguageCode = "auto",
    word_timestamps: bool = False
) -> Dict:
    """
    Convenience function for transcription.
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        device: 'cpu' or 'cuda'
        compute_type: Compute type for inference
        language: Language hint
        word_timestamps: Extract word timestamps
    
    Returns:
        Transcription result dict
    """
    transcriber = LyricsTranscriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type
    )
    
    return transcriber.transcribe(
        audio_path=audio_path,
        language=language,
        word_timestamps=word_timestamps
    )


def is_transcriber_available() -> bool:
    """Check if faster-whisper is available."""
    return FASTER_WHISPER_AVAILABLE
