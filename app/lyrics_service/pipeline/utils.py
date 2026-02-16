"""
Utility functions for lyrics extraction pipeline.
Handles ffmpeg preprocessing, temp file management, and hashing.
"""
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TempFileManager:
    """Context manager for temporary directories."""
    
    def __init__(self, prefix: str = "lyrics_"):
        self.prefix = prefix
        self.temp_dir: Optional[Path] = None
    
    def __enter__(self) -> Path:
        self.temp_dir = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.temp_dir
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def get_file_hash(file_path: str) -> str:
    """Generate SHA256 hash of file for caching/deduplication."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def preprocess_audio_ffmpeg(
    input_path: str,
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1,
    apply_filters: bool = True
) -> bool:
    """
    Preprocess audio using ffmpeg.
    - Convert to mono
    - Resample to target sample rate
    - Apply highpass filter and loudness normalization
    
    Args:
        input_path: Source audio file
        output_path: Destination preprocessed file
        sample_rate: Target sample rate (default 16kHz for Whisper)
        channels: Number of audio channels (1=mono)
        apply_filters: Whether to apply highpass and loudnorm filters
    
    Returns:
        True if successful, False otherwise
    """
    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        logger.warning("ffmpeg not found, skipping preprocessing")
        shutil.copy(input_path, output_path)
        return True
    
    # Build ffmpeg command
    cmd = ['ffmpeg', '-i', input_path, '-y']
    
    # Audio codec and format
    cmd.extend(['-acodec', 'pcm_s16le', '-ar', str(sample_rate), '-ac', str(channels)])
    
    # Apply audio filters if requested
    if apply_filters:
        # Highpass filter at 200Hz to remove low-frequency rumble
        # Loudness normalization for consistent volume
        audio_filter = 'highpass=f=200,loudnorm=I=-16:TP=-1.5:LRA=11'
        cmd.extend(['-af', audio_filter])
    
    cmd.append(output_path)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"ffmpeg preprocessing failed: {result.stderr[:500]}")
            return False
        
        logger.info(f"Audio preprocessed: {input_path} -> {output_path}")
        return True
    
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg preprocessing timed out")
        return False
    except Exception as e:
        logger.error(f"ffmpeg preprocessing error: {e}")
        return False


def get_audio_duration(file_path: str) -> Optional[float]:
    """Get audio duration in seconds using ffprobe."""
    if not shutil.which('ffprobe'):
        logger.warning("ffprobe not found, cannot determine duration")
        return None
    
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        duration_str = result.stdout.strip()
        if duration_str:
            return float(duration_str)
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}")
    
    return None


def validate_audio_file(file_path: str, max_size_mb: int = 50) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded audio file.
    
    Returns:
        (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file size
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    if file_size < 1024:  # Less than 1KB
        return False, "File is too small to be valid audio"
    
    # Check basic audio validity using ffprobe
    if shutil.which('ffprobe'):
        cmd = ['ffprobe', '-v', 'error', file_path]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10, check=False)
            if result.returncode != 0:
                return False, "File is not a valid audio file"
        except Exception as e:
            logger.warning(f"Could not validate audio: {e}")
    
    return True, None


def safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove directory separators and null bytes
    filename = os.path.basename(filename)
    filename = filename.replace('\x00', '')
    
    # Replace problematic characters
    for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename or 'audio'
