"""
High-level API for lyrics extraction.
Provides a convenient interface to the full extraction pipeline.
"""
import logging
import os
from typing import Dict, Optional

from .pipeline import separate, transcribe, postprocess, utils

logger = logging.getLogger(__name__)


class LyricsExtractor:
    """High-level interface for extracting lyrics from audio."""
    
    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
        enable_vocal_separation: bool = True,
        preprocess_audio: bool = True
    ):
        """
        Initialize lyrics extractor.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3', 'turbo')
            device: 'cpu' or 'cuda'
            compute_type: Compute precision ('int8', 'float16', etc.)
            enable_vocal_separation: Whether to use Demucs for vocal separation
            preprocess_audio: Whether to preprocess audio with ffmpeg
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.enable_vocal_separation = enable_vocal_separation
        self.preprocess_audio = preprocess_audio
        
        # Initialize transcriber (will load model)
        try:
            self.transcriber = transcribe.LyricsTranscriber(
                model_size=model_size,
                device=device,
                compute_type=compute_type
            )
            logger.info(f"Initialized LyricsExtractor with {model_size} on {device}")
        except Exception as e:
            logger.error(f"Failed to initialize transcriber: {e}")
            raise
    
    def extract(
        self,
        audio_path: str,
        language: str = "auto",
        include_timestamps: bool = False,
        output_dir: str = None
    ) -> Dict:
        """
        Extract lyrics from audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language hint ('en', 'vi', 'auto')
            include_timestamps: Whether to include word-level timestamps
            output_dir: Optional directory for intermediate files
        
        Returns:
            Dict with:
                - lyrics: Extracted and formatted lyrics
                - language: Detected language
                - words: Word-level timestamps (if requested)
                - metadata: Processing metadata
        
        Raises:
            FileNotFoundError: If audio file not found
            ValueError: If file validation fails
        """
        # Validate input file
        is_valid, error_msg = utils.validate_audio_file(audio_path)
        if not is_valid:
            raise ValueError(f"Invalid audio file: {error_msg}")
        
        # Get audio duration
        duration = utils.get_audio_duration(audio_path)
        logger.info(f"Processing audio: {audio_path} (duration: {duration}s)")
        
        # Create temp directory for intermediate files
        with utils.TempFileManager() as temp_dir:
            current_audio = audio_path
            
            # Step 1: Preprocess audio if requested
            if self.preprocess_audio:
                logger.info("Step 1/3: Preprocessing audio...")
                preprocessed_audio = os.path.join(temp_dir, "preprocessed.wav")
                if utils.preprocess_audio_ffmpeg(audio_path, preprocessed_audio):
                    current_audio = preprocessed_audio
                else:
                    logger.warning("Audio preprocessing failed, continuing with original")
            
            # Step 2: Separate vocals if requested
            if self.enable_vocal_separation:
                logger.info("Step 2/3: Separating vocals...")
                try:
                    demucs_output_dir = os.path.join(temp_dir, "demucs")
                    vocal_stem = separate.separate_vocals(
                        current_audio,
                        demucs_output_dir,
                        device=self.device
                    )
                    if vocal_stem:
                        current_audio = vocal_stem
                        logger.info(f"Vocal stem extracted: {vocal_stem}")
                    else:
                        logger.warning("Vocal separation failed, continuing with original audio")
                except Exception as e:
                    logger.warning(f"Vocal separation error: {e}, continuing with original audio")
            
            # Step 3: Transcribe audio
            logger.info("Step 3/3: Transcribing audio...")
            transcription = self.transcriber.transcribe(
                current_audio,
                language=language,
                word_timestamps=include_timestamps
            )
            
            # Step 4: Post-process lyrics
            logger.info("Post-processing lyrics...")
            post_result = postprocess.postprocess_lyrics(
                segments=transcription['segments'],
                include_word_timestamps=include_timestamps
            )
            
            # Compile final result
            result = {
                'lyrics': post_result['lyrics'],
                'language': post_result['language_detected'],
                'words': post_result['words'] if include_timestamps else None,
                'metadata': {
                    'duration_seconds': duration,
                    'model': self.model_size,
                    'device': self.device,
                    'vocal_separation_enabled': self.enable_vocal_separation,
                    'preprocessing_enabled': self.preprocess_audio,
                    'segments_count': len(transcription['segments'])
                }
            }
            
            logger.info(f"Extraction complete: {len(result['lyrics'])} chars, {result['metadata']['segments_count']} segments")
            return result


def extract_lyrics(
    audio_path: str,
    model_size: str = "large-v3",
    device: str = "cpu",
    language: str = "auto",
    include_timestamps: bool = False,
    enable_vocal_separation: bool = True,
    preprocess_audio: bool = True
) -> Dict:
    """
    Convenience function to extract lyrics from audio.
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        device: 'cpu' or 'cuda'
        language: Language hint
        include_timestamps: Whether to include word timestamps
        enable_vocal_separation: Use vocal separation
        preprocess_audio: Preprocess audio before transcription
    
    Returns:
        Extraction result dict
    """
    extractor = LyricsExtractor(
        model_size=model_size,
        device=device,
        enable_vocal_separation=enable_vocal_separation,
        preprocess_audio=preprocess_audio
    )
    
    return extractor.extract(
        audio_path,
        language=language,
        include_timestamps=include_timestamps
    )
