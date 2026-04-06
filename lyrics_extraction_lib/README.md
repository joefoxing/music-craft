# Lyrics Extraction Library

A production-grade Python library for extracting lyrics from audio files using AI. Combines vocal separation (Demucs) with speech-to-text transcription (faster-whisper) to accurately extract and format lyrics from music.

## Features

- **🎙️ AI-Powered Extraction**: Uses state-of-the-art Whisper ASR model for accurate transcription
- **🎵 Vocal Separation**: Demucs-based separation for improved accuracy on instrumental backgrounds  
- **🌍 Multi-Language Support**: English, Vietnamese, and mixed-language detection
- **📝 Smart Formatting**: Automatic line breaks based on timing and linguistic cues
- **⏱️ Timestamp Support**: Optional word-level timestamps for karaoke/sync applications
- **🔧 Configurable Pipeline**: Mix and match components or use high-level API
- **📦 Production-Ready**: Comprehensive error handling, logging, and validation

## Installation

### Basic Installation
```bash
pip install lyrics-extraction
```

### GPU Support (Optional)
For GPU acceleration with CUDA:
```bash
pip install lyrics-extraction[gpu]
```

### From Source
```bash
git clone https://github.com/lyric-cover-staging/lyrics-extraction-lib.git
cd lyrics-extraction-lib
pip install -e .
```

## System Dependencies

The library requires `ffmpeg` and `ffprobe`:

**Windows** (via Chocolatey):
```bash
choco install ffmpeg
```

**Mac** (via Homebrew):
```bash
brew install ffmpeg
```

**Linux** (via apt):
```bash
sudo apt-get install ffmpeg
```

## Quick Start

### Simple Usage
```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics("song.mp3")
print(result['lyrics'])
```

### Advanced Usage
```python
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(
    model_size="large-v3",
    device="cuda",  # or "cpu"
    enable_vocal_separation=True,
    preprocess_audio=True
)

result = extractor.extract(
    audio_path="song.mp3",
    language="auto",
    include_timestamps=True
)

print("Lyrics:")
print(result['lyrics'])
print("\nLanguage:", result['language'])
print("Duration:", result['metadata']['duration_seconds'], "seconds")

if result['words']:
    print("\nFirst 5 words with timestamps:")
    for word in result['words'][:5]:
        print(f"  {word['word']}: {word['start']:.2f}s - {word['end']:.2f}s")
```

## API Reference

### High-Level API

#### `extract_lyrics(audio_path, **options)`
Convenience function for quick extraction.

**Parameters:**
- `audio_path` (str): Path to audio file
- `model_size` (str): Whisper model ('tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3', 'turbo') - default: "large-v3"
- `device` (str): 'cpu' or 'cuda' - default: "cpu"
- `language` (str): Language hint ('en', 'vi', 'auto') - default: "auto"
- `include_timestamps` (bool): Extract word timestamps - default: False
- `enable_vocal_separation` (bool): Use vocal separation - default: True
- `preprocess_audio` (bool): Preprocess with filters - default: True

**Returns:**
```python
{
    'lyrics': str,                          # Formatted lyrics text
    'language': str,                        # Detected language ('en', 'vi', 'mixed', 'unknown')
    'words': List[Dict] or None,            # Word timestamps if requested
    'metadata': {
        'duration_seconds': float,
        'model': str,
        'device': str,
        'vocal_separation_enabled': bool,
        'preprocessing_enabled': bool,
        'segments_count': int
    }
}
```

#### `LyricsExtractor` class
Full-featured extractor for advanced use cases.

```python
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(
    model_size="large-v3",
    device="cpu",
    compute_type="int8",
    enable_vocal_separation=True,
    preprocess_audio=True
)

result = extractor.extract(
    audio_path="song.mp3",
    language="auto",
    include_timestamps=False,
    output_dir="/tmp/lyrics_work"  # Optional
)
```

### Low-Level API (Pipeline Components)

#### Vocal Separation
```python
from lyrics_extraction.pipeline import separate

# Using the class
separator = separate.VocalSeparator(
    model_name="htdemucs",
    device="cpu"
)
vocal_path = separator.separate("input.mp3", "/tmp/output")

# Or use convenience function
vocal_path = separate.separate_vocals("input.mp3", "/tmp/output")
```

#### Transcription
```python
from lyrics_extraction.pipeline import transcribe

# Initialize transcriber
transcriber = transcribe.LyricsTranscriber(
    model_size="large-v3",
    device="cpu",
    compute_type="int8"
)

# Transcribe audio
result = transcriber.transcribe(
    audio_path="audio.wav",
    language="auto",
    word_timestamps=True,
    vad_filter=True,
    beam_size=5,
    temperature=0.0  # Deterministic
)

print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Segments: {len(result['segments'])}")
```

#### Post-Processing
```python
from lyrics_extraction.pipeline import postprocess

# Post-process transcription segments
result = postprocess.postprocess_lyrics(
    segments=transcription_segments,
    include_word_timestamps=True,
    deduplicate=True,
    max_chars_per_line=60,
    line_gap_threshold=0.3,
    stanza_gap_threshold=1.0
)

print(f"Lyrics:\n{result['lyrics']}")
print(f"Language: {result['language_detected']}")
```

#### Audio Utilities
```python
from lyrics_extraction.pipeline import utils

# Validate audio file
is_valid, error = utils.validate_audio_file("audio.mp3", max_size_mb=50)
if not is_valid:
    print(f"Validation failed: {error}")

# Get audio duration
duration = utils.get_audio_duration("audio.mp3")
print(f"Duration: {duration} seconds")

# Preprocess audio
utils.preprocess_audio_ffmpeg(
    "input.mp3",
    "output.wav",
    sample_rate=16000,
    channels=1,
    apply_filters=True
)

# Temporary file management
with utils.TempFileManager() as temp_dir:
    # Work with temporary directory
    pass
    # Automatically cleaned up on exit
```

## Configuration

Customize behavior through environment variables or constructor parameters:

```python
import os

# Environment variables (used as defaults)
os.environ['LYRICS_WHISPER_MODEL'] = 'large-v3'
os.environ['LYRICS_DEVICE'] = 'cuda'
os.environ['LYRICS_COMPUTE_TYPE'] = 'float16'
os.environ['LYRICS_DEMUCS_MODEL'] = 'htdemucs'
os.environ['LYRICS_MAX_CHARS_PER_LINE'] = '60'
```

## Examples

### Example 1: Basic Extraction
```python
from lyrics_extraction import extract_lyrics

# Simple one-liner
result = extract_lyrics("my_song.mp3")
with open("lyrics.txt", "w") as f:
    f.write(result['lyrics'])
```

### Example 2: Batch Processing
```python
from lyrics_extraction import LyricsExtractor
from pathlib import Path

extractor = LyricsExtractor(
    model_size="base",  # Faster, smaller model
    device="cuda"
)

audio_files = Path("./music").glob("*.mp3")
for audio_file in audio_files:
    print(f"Processing {audio_file.name}...")
    result = extractor.extract(str(audio_file))
    
    output_file = audio_file.with_suffix('.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result['lyrics'])
```

### Example 3: With Timestamps for Karaoke
```python
from lyrics_extraction import extract_lyrics
import json

result = extract_lyrics(
    "song.mp3",
    include_timestamps=True
)

# Save with timing information
karaoke_data = {
    "lyrics": result['lyrics'],
    "timing": [
        {
            "word": word['word'],
            "start": word['start'],
            "end": word['end']
        }
        for word in result['words']
    ]
}

with open("karaoke.json", "w") as f:
    json.dump(karaoke_data, f, indent=2)
```

### Example 4: Language Detection
```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics("multilingual_song.mp3")
print(f"Detected: {result['language']}")

if result['language'] == 'mixed':
    print("This is a mixed-language song!")
elif result['language'] == 'vi':
    print("Vietnamese detected")
elif result['language'] == 'en':
    print("English detected")
```

## Performance Tips

1. **Model Size Trade-offs**:
   - `tiny` / `base`: Fast, lower accuracy (~2-5 min)
   - `small` / `medium`: Balanced (~10-20 min)
   - `large-v3` / `turbo`: Most accurate (~30-60 min)

2. **GPU Acceleration**:
   - Use `device="cuda"` with NVIDIA GPU for 10-20x speedup
   - Requires CUDA-capable GPU and `torch` with CUDA support

3. **Disable Vocal Separation**:
   - If lyrics are already clear, set `enable_vocal_separation=False` to save time
   - Useful for recordings with minimal background music

4. **Audio Preprocessing**:
   - Enable `preprocess_audio=True` for noisy recordings
   - Disable for already clean audio to save processing time

## Output Format

The library returns well-formatted lyrics with:
- **Line breaks** based on timing gaps and linguistic cues
- **Stanza breaks** (double line breaks) for major pauses
- **Uppercase handling** for proper line breaks at sentence starts
- **Punctuation normalization** for consistent formatting
- **Noise removal** (music tags, applause, etc. from ASR)

Example output:
```
I'm standing on the edge
Waiting for your call

Can you hear me now?
I'm calling out so loud
```

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg (see System Dependencies above)

### "faster-whisper not installed"
```bash
pip install faster-whisper
```

### "CUDA not available"
GPU requires:
1. NVIDIA GPU with CUDA compute capability
2. CUDA Toolkit installed
3. PyTorch with CUDA support: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

### Slow Processing
- Reduce model size: `model_size="base"` 
- Disable vocal separation: `enable_vocal_separation=False`
- Use GPU: `device="cuda"`
- Disable preprocessing: `preprocess_audio=False`

### Memory Issues
- Reduce batch processing size
- Use smaller model (`tiny`, `base`)
- Process on CPU instead of GPU
- Split large audio files

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit pull requests.

## Support

For issues and questions:
- GitHub Issues: https://github.com/lyric-cover-staging/lyrics-extraction-lib/issues
- Documentation: https://github.com/lyric-cover-staging/lyrics-extraction-lib/blob/main/README.md
