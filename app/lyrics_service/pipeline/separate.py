"""
Vocal separation module using Demucs.
Isolates vocal stem from music for better ASR accuracy.
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VocalSeparator:
    """Wrapper for Demucs vocal separation."""
    
    def __init__(
        self,
        model_name: str = "htdemucs",
        device: str = "cpu",
        shifts: int = 1,
        overlap: float = 0.25
    ):
        """
        Initialize vocal separator.
        
        Args:
            model_name: Demucs model ('htdemucs', 'htdemucs_ft', 'mdx_extra', etc.)
            device: 'cpu' or 'cuda'
            shifts: Number of random shifts for better quality (higher=slower)
            overlap: Overlap between prediction windows (0.25 = 25%)
        """
        self.model_name = model_name
        self.device = device
        self.shifts = shifts
        self.overlap = overlap
        
        # Check if demucs is available
        if not shutil.which('demucs'):
            logger.warning("Demucs CLI not found in PATH")
    
    def separate(
        self,
        input_audio_path: str,
        output_dir: str,
        two_stems: str = "vocals"
    ) -> Optional[str]:
        """
        Separate vocals from audio file.
        
        Args:
            input_audio_path: Path to input audio file
            output_dir: Directory to save separated stems
            two_stems: Which stem to extract ('vocals' or 'no_vocals')
        
        Returns:
            Path to separated vocal file, or None if failed
        """
        if not shutil.which('demucs'):
            logger.error("Demucs not available, skipping separation")
            return None
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Build demucs command
        cmd = [
            'demucs',
            '--two-stems', two_stems,
            '-n', self.model_name,
            '-d', self.device,
            '--shifts', str(self.shifts),
            '--overlap', str(self.overlap),
            '-o', output_dir,
            input_audio_path
        ]
        
        logger.info(f"Running Demucs separation: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Demucs failed (code {result.returncode})")
                logger.error(f"Demucs stderr: {result.stderr[-2000:]}")
                logger.error(f"Demucs stdout: {result.stdout[-500:]}")
                return None
            
            # Find the output vocal file
            # Demucs outputs to: output_dir/model_name/audio_name/vocals.wav
            input_basename = Path(input_audio_path).stem
            
            # Try to find vocals.wav in output structure
            possible_paths = [
                Path(output_dir) / self.model_name / input_basename / f"{two_stems}.wav",
                Path(output_dir) / self.model_name / input_basename / "vocals.wav",
                Path(output_dir) / input_basename / f"{two_stems}.wav",
                Path(output_dir) / input_basename / "vocals.wav",
            ]
            
            for vocal_path in possible_paths:
                if vocal_path.exists():
                    logger.info(f"Successfully separated vocals: {vocal_path}")
                    return str(vocal_path)
            
            logger.error(f"Could not find separated vocal file in {output_dir}")
            return None
        
        except subprocess.TimeoutExpired:
            logger.error("Demucs separation timed out after 10 minutes")
            return None
        except Exception as e:
            logger.error(f"Demucs separation failed: {e}")
            return None
    
    @staticmethod
    def is_available() -> bool:
        """Check if Demucs is available on the system."""
        return shutil.which('demucs') is not None


def separate_vocals(
    input_audio_path: str,
    output_dir: str,
    model_name: str = "htdemucs",
    device: str = "cpu"
) -> Optional[str]:
    """
    Convenience function to separate vocals.
    
    Args:
        input_audio_path: Path to input audio
        output_dir: Output directory
        model_name: Demucs model name
        device: 'cpu' or 'cuda'
    
    Returns:
        Path to separated vocal file or None
    """
    separator = VocalSeparator(model_name=model_name, device=device)
    return separator.separate(input_audio_path, output_dir)
