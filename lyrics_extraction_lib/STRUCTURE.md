# Lyrics Extraction Library - Project Structure

## Overview

The extracted lyrics extraction library is a standalone, reusable Python package with professional structure and documentation.

## Directory Structure

```
lyrics_extraction_lib/
├── lyrics_extraction/              # Main package
│   ├── __init__.py                # Package initialization & exports
│   ├── extractor.py               # High-level API (LyricsExtractor class)
│   └── pipeline/                  # Core pipeline components
│       ├── __init__.py
│       ├── separate.py            # Vocal separation (Demucs)
│       ├── transcribe.py          # Speech-to-text (faster-whisper)
│       ├── postprocess.py         # Lyrics formatting & cleanup
│       └── utils.py               # Audio utilities & file management
│
├── examples/                      # Usage examples
│   ├── example_basic.py          # Simple usage
│   ├── example_advanced.py       # Advanced with timestamps
│   ├── example_batch.py          # Batch processing
│   ├── example_components.py     # Using individual components
│   └── example_error_handling.py # Error handling patterns
│
├── tests/                         # Unit tests (to be added)
│   ├── test_separate.py
│   ├── test_transcribe.py
│   ├── test_postprocess.py
│   └── test_utils.py
│
├── docs/                          # Additional documentation
│   └── (API documentation, guides, etc.)
│
├── setup.py                       # Python packaging
├── pyproject.toml                # Modern Python packaging config
├── requirements.txt              # Package dependencies
├── MANIFEST.in                   # Package manifest
├── LICENSE                       # MIT License
├── README.md                     # Main documentation
├── INTEGRATION.md               # Integration guide
├── MIGRATION.md                 # Migration guide from old code
└── .gitignore                   # Git ignore rules
```

## Key Features

### 1. **Core Pipeline Modules**

#### `lyrics_extraction/pipeline/separate.py`
- `VocalSeparator` class for Demucs-based vocal separation
- `separate_vocals()` convenience function
- Supports multiple models and devices (CPU/GPU)

#### `lyrics_extraction/pipeline/transcribe.py`
- `LyricsTranscriber` class for faster-whisper transcription
- `transcribe_audio()` convenience function
- Optimized for singing with VAD tuning
- Multi-language support (EN/VI)
- Word-level timestamps support

#### `lyrics_extraction/pipeline/postprocess.py`
- `clean_transcription_text()` - Remove noise tags
- `detect_language()` - EN/VI/mixed detection
- `format_lyrics_with_timestamps()` - Smart line breaking
- `deduplicate_repetitive_lines()` - Remove repetition
- `postprocess_lyrics()` - Main post-processing orchestration
- Pure Python, no LLM dependency

#### `lyrics_extraction/pipeline/utils.py`
- `TempFileManager` - Context manager for temp files
- `preprocess_audio_ffmpeg()` - Audio normalization
- `get_audio_duration()` - Duration detection
- `validate_audio_file()` - File validation
- `safe_filename()` - Path sanitization
- `get_file_hash()` - File deduplication

### 2. **High-Level API**

#### `lyrics_extraction/extractor.py`
- `LyricsExtractor` class - Full-featured extraction orchestration
- `extract_lyrics()` - Convenience function
- Combines all pipeline stages
- Handles end-to-end workflow

### 3. **Public API**

Main exports in `lyrics_extraction/__init__.py`:
```python
from lyrics_extraction import (
    extract_lyrics,          # Quick function
    LyricsExtractor,         # Full class
    separate,                # Vocal separation module
    transcribe,              # Transcription module
    postprocess,             # Post-processing module
    utils                    # Utilities module
)
```

## Usage Patterns

### Pattern 1: Simple One-Liner
```python
from lyrics_extraction import extract_lyrics
result = extract_lyrics("song.mp3")
print(result['lyrics'])
```

### Pattern 2: Full Control
```python
from lyrics_extraction import LyricsExtractor
extractor = LyricsExtractor(model_size="large-v3", device="cuda")
result = extractor.extract("song.mp3", include_timestamps=True)
```

### Pattern 3: Component-Based
```python
from lyrics_extraction.pipeline import separate, transcribe, postprocess
# Use individual components for custom workflows
```

## Installation & Distribution

### Local Development
```bash
pip install -e ./lyrics_extraction_lib
```

### PyPI Distribution (Future)
```bash
# Build
python setup.py sdist bdist_wheel

# Upload
twine upload dist/*
```

### Direct Installation
```bash
pip install git+https://github.com/lyric-cover-staging/lyrics-extraction-lib.git
```

## Dependencies

### Required
- `faster-whisper>=1.1.0` - Speech-to-text
- `demucs>=4.0.1` - Vocal separation
- `torchcodec>=0.10.0` - Audio codec support

### Optional
- `torch` - GPU acceleration (NVIDIA CUDA)

### System
- `ffmpeg` - Audio processing
- `ffprobe` - Audio analysis

## Configuration

Uses environment variables for configuration:
```env
LYRICS_WHISPER_MODEL=large-v3
LYRICS_DEVICE=cuda
LYRICS_DEMUCS_MODEL=htdemucs
LYRICS_MAX_CHARS_PER_LINE=60
```

## Example Scripts

Located in `examples/`:
1. `example_basic.py` - Simple extraction
2. `example_advanced.py` - With timestamps and JSON output
3. `example_batch.py` - Processing multiple files
4. `example_components.py` - Using individual pipeline components
5. `example_error_handling.py` - Proper error handling

## Documentation

- **README.md** - Complete user guide with API reference
- **INTEGRATION.md** - How to integrate into existing projects
- **MIGRATION.md** - How to migrate from old code
- **examples/** - Code examples for common tasks

## Testing

Comprehensive test coverage (to be implemented):
```bash
pytest tests/ -v --cov=lyrics_extraction
```

## Code Quality

- **Type hints** throughout for IDE support
- **Docstrings** for all public functions
- **Error handling** with meaningful messages
- **Logging** for debugging
- **Clean separation** of concerns

## Performance

### Typical Times (on various hardware)
- **CPU (Intel i7, 16GB)**: 30-60 minutes per song
- **GPU (NVIDIA RTX 3090)**: 2-5 minutes per song
- **GPU (NVIDIA T4)**: 5-15 minutes per song

### Optimization Tips
- Use `device="cuda"` for significant speedup
- Use smaller model (`base`, `small`) for faster processing
- Disable preprocessing for clean audio
- Disable vocal separation if unnecessary

## Limitations & Constraints

✅ **What it does:**
- Accurate lyrics extraction from audio
- Multi-language support (EN/VI)
- Smart formatting and line breaking
- Optional word-level timestamps
- Batch processing capability

❌ **What it doesn't do:**
- Translate lyrics or add words
- Identify speakers/singers
- Provide musical notation
- Modify audio quality

## Standards Compliance

- **Python 3.9+** - Modern Python compatibility
- **PEP 8** - Code style guidelines
- **Type hints** - Runtime type checking support
- **Semantic versioning** - Clear version numbering
- **MIT License** - Permissive open source

## Security Considerations

- ✅ Path sanitization for uploaded files
- ✅ File size validation
- ✅ Audio format validation
- ✅ Safe temp file handling
- ✅ No arbitrary code execution

## Maintenance

The library is designed for:
- ✅ Easy updates and improvements
- ✅ Backward compatibility
- ✅ Minimal dependencies
- ✅ Clear test coverage
- ✅ Comprehensive documentation

## Next Steps

1. **Installation**: `pip install -e ./lyrics_extraction_lib`
2. **Integration**: Follow [INTEGRATION.md](./INTEGRATION.md)
3. **Testing**: Run examples from `examples/` directory
4. **Deployment**: Use in your projects as documented
5. **Contribution**: Submit issues and PRs on GitHub

---

For detailed information, see:
- **Installation & Usage**: [README.md](./README.md)
- **Integration Guide**: [INTEGRATION.md](./INTEGRATION.md)  
- **Migration from Old Code**: [MIGRATION.md](./MIGRATION.md)
- **Code Examples**: [examples/](./examples/)
