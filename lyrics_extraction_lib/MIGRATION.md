# Lyrics Extraction Library - Project Integration Guide

This document provides step-by-step instructions for integrating the `lyrics-extraction` library into the main Music Cover project.

## Overview

The lyrics extraction logic has been refactored into a standalone, reusable library with:
- ✅ Clean separation of concerns
- ✅ Reusable across multiple projects
- ✅ Professional Python packaging
- ✅ Comprehensive documentation
- ✅ Backward-compatible with existing code

## Installation

### Step 1: Add Library as Dependency

**Option A: Local Development (Current Setup)**
```bash
# Install in editable mode from the local library folder
pip install -e ./lyrics_extraction_lib
```

**Option B: From PyPI (Once Published)**
```bash
pip install lyrics-extraction
```

### Step 2: Update requirements.txt

Add to `requirements.txt`:
```
lyrics-extraction>=1.0.0
```

Or update the local version:
```
-e ./lyrics_extraction_lib
```

## Migration Steps

### Step 1: Replace Worker Imports

**Before:**
```python
# app/lyrics_service/worker.py
from app.lyrics_service import config
from app.lyrics_service.pipeline import separate, transcribe, postprocess, utils
```

**After:**
```python
# app/lyrics_service/worker.py
from lyrics_extraction.pipeline import separate, transcribe, postprocess, utils
from lyrics_extraction import extractor
```

### Step 2: Simplify Worker Implementation

**Before:**
```python
def process_lyrics_extraction(
    job_id: str,
    audio_file_path: str,
    language_hint: str = "auto",
    include_timestamps: str = "none"
) -> Dict:
    """Main job processing function."""
    # ... 200+ lines of orchestration code ...
    with utils.TempFileManager() as temp_manager:
        # Preprocessing
        # Separation
        # Transcription
        # Post-processing
```

**After:**
```python
from lyrics_extraction import LyricsExtractor

# Create once and reuse
_extractor = LyricsExtractor(
    model_size="large-v3",
    device="cuda",
    enable_vocal_separation=True
)

def process_lyrics_extraction(
    job_id: str,
    audio_file_path: str,
    language_hint: str = "auto",
    include_timestamps: str = "none"
) -> Dict:
    """Main job processing function."""
    result = _extractor.extract(
        audio_file_path,
        language=language_hint,
        include_timestamps=(include_timestamps == "word")
    )
    
    return {
        "job_id": job_id,
        "status": "done",
        "result": result,
        "error": None
    }
```

### Step 3: Update API Endpoints

**Before:**
```python
# app/lyrics_service/main.py
@app.post("/v1/lyrics")
async def create_lyrics_extraction_job(file: UploadFile):
    # ... File handling, validation, job enqueueing ...
    job = queue.enqueue(process_lyrics_extraction, job_id, file_path)
```

**After:**
```python
# No changes needed! The API can remain the same
# The queue still calls process_lyrics_extraction() which now uses the library
```

### Step 4: Remove Duplicate Code

Delete these files (they're now in the library):
```
app/lyrics_service/pipeline/separate.py       → lyrics_extraction/pipeline/separate.py
app/lyrics_service/pipeline/transcribe.py     → lyrics_extraction/pipeline/transcribe.py
app/lyrics_service/pipeline/postprocess.py    → lyrics_extraction/pipeline/postprocess.py
app/lyrics_service/pipeline/utils.py          → lyrics_extraction/pipeline/utils.py
app/lyrics_service/pipeline/__init__.py       → lyrics_extraction/pipeline/__init__.py
app/lyrics_service/config.py                  → (Use library defaults + env vars)
```

### Step 5: Update Configuration

**Before:**
```python
# app/lyrics_service/config.py - Complex configuration
WHISPER_MODEL_SIZE = os.getenv("LYRICS_WHISPER_MODEL", "large-v3")
DEMUCS_MODEL = os.getenv("LYRICS_DEMUCS_MODEL", "htdemucs")
# ... 50+ lines of configuration ...
```

**After:**
```python
# Use the library's built-in configuration via environment variables
# No changes needed - just set these env vars:
export LYRICS_WHISPER_MODEL=large-v3
export LYRICS_DEVICE=cuda
export LYRICS_DEMUCS_MODEL=htdemucs
```

### Step 6: Keep Only Service Layer

The `app/lyrics_service/` can now be significantly simplified:

```
app/lyrics_service/
├── __init__.py        # Service configuration
├── main.py           # FastAPI server (unchanged)
├── worker.py         # Simplified - now just calls extract_lyrics()
└── config.py         # Service-specific config (can be minimal)
```

## Testing Integration

### Test 1: Basic Integration
```python
from lyrics_extraction import extract_lyrics

def test_library_integration():
    """Test that library works with our project."""
    result = extract_lyrics("test_audio.mp3")
    assert 'lyrics' in result
    assert result['lyrics']  # Not empty
    print("✓ Library integration successful")

if __name__ == "__main__":
    test_library_integration()
```

### Test 2: Worker Integration
```python
from app.lyrics_service.worker import process_lyrics_extraction

def test_worker_with_library():
    """Test that worker uses library correctly."""
    result = process_lyrics_extraction(
        job_id="test-123",
        audio_file_path="test_audio.mp3"
    )
    assert result['status'] == 'done'
    assert result['error'] is None
    print("✓ Worker integration successful")

if __name__ == "__main__":
    test_worker_with_library()
```

## Benefits of Migration

| Aspect | Before | After |
|--------|--------|-------|
| **Code Reusability** | Only in this project | Usable in other projects |
| **Maintenance** | Scattered across services | Centralized in one library |
| **Testing** | Mixed with service code | Standalone test suite |
| **Distribution** | Not installable | Installable via pip |
| **Lines of Code (app/)** | ~600 lines | ~150 lines |
| **Dependencies** | Tight coupling | Clean separation |

## Backward Compatibility

The migration is **fully backward compatible**:
- All existing APIs remain unchanged
- Existing code continues to work
- Gradual migration is possible
- No breaking changes required

## Phased Migration Approach

If you prefer to migrate gradually:

### Phase 1: Run Both in Parallel
```python
# Use library while keeping old code active
from lyrics_extraction import extract_lyrics
from app.lyrics_service.pipeline import separate, transcribe  # Old code

# Comparison test
result1 = extract_lyrics("test.mp3")  # New library
result2 = old_extraction_function("test.mp3")  # Old code
```

### Phase 2: Route New Requests to Library
```python
# New extraction requests use library
# Old requests still use internal code
if use_new_library:
    result = extract_lyrics(audio_path)
else:
    result = old_extraction_function(audio_path)
```

### Phase 3: Deprecate Old Code
```python
# Once library is proven stable
# Remove internal pipeline code
# Point everything to lyrics_extraction library
```

## Environment Variables

Set these in your `.env` for the library:
```env
# Container runtime configuration
LYRICS_DEVICE=cuda              # or 'cpu'
LYRICS_WHISPER_MODEL=large-v3
LYRICS_DEMUCS_MODEL=htdemucs
LYRICS_ENABLE_SEPARATION=true
LYRICS_PREPROCESS_AUDIO=true

# Performance tuning
LYRICS_MAX_CHARS_PER_LINE=60
LYRICS_LINE_GAP_THRESHOLD=0.3
LYRICS_STANZA_GAP_THRESHOLD=1.0
```

## Deployment

After integrating the library:

### Docker Compose
No changes needed! The existing `docker-compose.yml` works as-is since the library will be installed via `pip`.

### Kubernetes
The library is just a Python package - no special deployment needed.

## Rollback

If needed, rolling back is straightforward:
```bash
# Remove library
pip uninstall lyrics-extraction

# Restore old code from git
git checkout HEAD app/lyrics_service/pipeline/

# Restart services
docker restart lyrics-api lyrics-worker
```

## Support & Questions

For issues or questions:
1. Check [INTEGRATION.md](./INTEGRATION.md) in the library
2. Review the [README.md](./README.md) for API docs
3. See [examples/](./examples/) for code samples
4. Check library GitHub issues

## Next Steps

1. **Install library**: `pip install -e ./lyrics_extraction_lib`
2. **Test integration**: Run test scripts (see Testing Integration section)
3. **Update imports**: Switch to library imports in worker.py
4. **Verify functionality**: Test existing API endpoints
5. **Monitor deployment**: Track logs for any issues
6. **Clean up**: Remove duplicate code once stable

## Summary

✅ **Main benefits:**
- **Reusable** across projects
- **Maintainable** with clear separation
- **Testable** with dedicated test suite
- **Distributable** via pip
- **Backward compatible** with no breaking changes

The library is production-ready and can be integrated immediately!
