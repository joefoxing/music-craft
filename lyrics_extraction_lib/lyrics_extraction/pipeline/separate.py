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
            two_stems: Which stem to extract ('vocals' or 'drums')
        
        Returns:
            Path to extracted vocal stem, or None if failed
        """
        if not os.path.exists(input_audio_path):
            logger.error(f"Input audio file not found: {input_audio_path}")
            return None
        
        if not shutil.which('demucs'):
            logger.error("Demucs CLI not found. Install with: pip install demucs")
            return None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Build demucs command
        cmd = [
            'demucs',
            '--model', self.model_name,
            '--device', self.device,
            '--shifts', str(self.shifts),
            '--overlap', str(self.overlap),
            '--two-stems=' + two_stems,
            '--out', output_dir,
            input_audio_path
        ]
        
        try:
            logger.info(f"Running Demucs separation: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Demucs failed: {result.stderr[:500]}")
                return None
            
            # Find the separated vocals file
            # Demucs output structure: output_dir/model_name/track_name/vocals.wav
            audio_name = Path(input_audio_path).stem
            model_output_dir = Path(output_dir) / self.model_name / audio_name
            
            vocal_stem = model_output_dir / 'vocals.wav'
            if vocal_stem.exists():
                logger.info(f"Vocal separation complete: {vocal_stem}")
                return str(vocal_stem)
            
            logger.error(f"Vocal stem not found at expected location: {vocal_stem}")
            return None
        
        except subprocess.TimeoutExpired:
            logger.error("Demucs processing timed out")
            return None
        except Exception as e:
            logger.error(f"Demucs separation error: {e}")
            return None


def separate_vocals(
    input_audio_path: str,
    output_dir: str,
    model_name: str = "htdemucs",
    device: str = "cpu"
) -> Optional[str]:
    """
    Convenience function for vocal separation.
    
    Args:
        input_audio_path: Path to input audio file
        output_dir: Directory for output files
        model_name: Demucs model to use
        device: 'cpu' or 'cuda'
    
    Returns:
        Path to vocal stem file
    """
    separator = VocalSeparator(
        model_name=model_name,
        device=device
    )
    return separator.separate(input_audio_path, output_dir)
