"""
Lyrics Extraction Library
A reusable Python library for extracting lyrics from audio using AI.

Main components:
- Vocal separation (Demucs)
- Speech-to-text transcription (faster-whisper)  
- Lyrics post-processing and formatting

Quick Start:
    from lyrics_extraction import extract_lyrics
    result = extract_lyrics("song.mp3")
    print(result['lyrics'])
"""

__version__ = "1.0.0"
__author__ = "Music Cover AI Team"

from . import pipeline
from .pipeline import separate, transcribe, postprocess, utils
from .extractor import LyricsExtractor, extract_lyrics

__all__ = [
    'pipeline',
    'separate',
    'transcribe',
    'postprocess',
    'utils',
    'LyricsExtractor',
    'extract_lyrics'
]
