# Lyrics Extraction Library - Quick Start Guide

Get up and running in 5 minutes!

## Installation

### 1. Install the library

```bash
# From local folder (development)
pip install -e ./lyrics_extraction_lib

# Or from PyPI (once published)
pip install lyrics-extraction
```

### 2. Verify installation

```bash
python -c "import lyrics_extraction; print('✓ Installation successful')"
```

### 3. Check system dependencies

```bash
which ffmpeg ffprobe
# Should show both are installed
```

If missing:
```bash
# Windows
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

## 5-Minute Tutorial

### Example 1: Extract Lyrics (Simplest)

```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics("song.mp3")
print(result['lyrics'])
```

### Example 2: With Timestamps

```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics(
    "song.mp3",
    include_timestamps=True
)

print(result['lyrics'])
print("\nFirst 5 words:")
for word in result['words'][:5]:
    print(f"  {word['word']}: {word['start']:.2f}s")
```

### Example 3: Use GPU for Speed

```python
from lyrics_extraction import extract_lyrics

# Requires NVIDIA GPU with CUDA
result = extract_lyrics(
    "song.mp3",
    device="cuda",  # Much faster!
    model_size="large-v3"
)
```

### Example 4: Process Multiple Files

```python
from lyrics_extraction import LyricsExtractor
from pathlib import Path

extractor = LyricsExtractor(device="cuda")

for mp3_file in Path("./music").glob("*.mp3"):
    result = extractor.extract(str(mp3_file))
    
    with open(mp3_file.with_suffix(".txt"), "w") as f:
        f.write(result['lyrics'])
    
    print(f"✓ {mp3_file.name}")
```

## Common Questions

### Q: How do I choose model size?

| Model | Speed | Accuracy | Uses |
|-------|-------|----------|------|
| `tiny` | ⚡⚡⚡ Fast | Basic | Quick testing |
| `base` | ⚡⚡ Normal | Good | API servers |
| `small` | ⚡ Slower | Better | Batch processing |
| `large-v3` | 🐢 Slow | Excellent | Production |

```python
# For API (fast responses)
extract_lyrics("song.mp3", model_size="base")

# For batch (best quality)
extract_lyrics("song.mp3", model_size="large-v3")
```

### Q: When should I disable vocal separation?

Use `enable_vocal_separation=False` if:
- ✓ Audio already has clear vocals (studio recording)
- ✓ You need faster processing
- ✓ Background music is minimal

```python
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(enable_vocal_separation=False)
result = extractor.extract("song.mp3")
```

### Q: Can I use this on CPU only?

Yes! Set `device="cpu"`:

```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics(
    "song.mp3",
    device="cpu"  # No GPU needed
)
```

Expected times: 30-60 minutes per song.

### Q: How do I detect the language?

It's automatic! Check the result:

```python
result = extract_lyrics("song.mp3")
print(result['language'])
# Output: 'en', 'vi', 'mixed', or 'unknown'
```

### Q: What audio formats are supported?

All common formats:
- ✓ MP3, WAV, FLAC
- ✓ M4A, AAC, OGG
- ✓ OPUS, WMA
- And more (via ffmpeg)

## Performance Tips

### Tip 1: Reuse Extractor Instance

```python
# ✓ GOOD - Creates extractor once
from lyrics_extraction import LyricsExtractor
extractor = LyricsExtractor()
for file in files:
    result = extractor.extract(file)

# ✗ BAD - Creates new extractor for each file
from lyrics_extraction import extract_lyrics
for file in files:
    result = extract_lyrics(file)  # Loads model each time!
```

### Tip 2: Use GPU for Batch Jobs

```python
# 10 songs on GPU: ~50 minutes
# 10 songs on CPU: ~300 minutes

extractor = LyricsExtractor(device="cuda")
```

### Tip 3: Smaller Model for Web APIs

```python
# Faster response to users
extractor = LyricsExtractor(
    model_size="base",  # Instead of "large-v3"
    device="cuda"
)
```

### Tip 4: Disable Preprocessing for Clean Audio

```python
# Already clean studio recording?
extractor = LyricsExtractor(
    preprocess_audio=False  # Skip filtering
)
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'faster_whisper'"

**Solution:**
```bash
pip install faster-whisper
```

### Issue: "ffmpeg not found"

**Solution:** Install ffmpeg (see Installation section)

### Issue: ImportError for CUDA/GPU

**Solution:**
```bash
# Install PyTorch with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

Then use: `device="cuda"`

### Issue: Out of memory error

**Solutions:**
1. Use smaller model: `model_size="base"`
2. Use CPU instead: `device="cpu"`
3. Disable vocal separation: `enable_vocal_separation=False`

### Issue: Slow processing

**Check:**
- Using CPU? Consider getting a GPU
- Using large model? Try `model_size="base"`
- File too large? Try shorter audio files

## Next Steps

1. **Try the examples**: Check [examples/](../examples/) directory
2. **Read the docs**: See [README.md](../README.md) for full API reference
3. **Integrate**: Follow [INTEGRATION.md](../INTEGRATION.md) for your project
4. **Get help**: Check [INTEGRATION.md](../INTEGRATION.md) troubleshooting section

## API Reference Quick

```python
from lyrics_extraction import (
    extract_lyrics,        # Quick extraction function
    LyricsExtractor,       # Full-featured class
    separate,              # Vocal separation module
    transcribe,            # Transcription module
    postprocess,           # Post-processing module
    utils                  # Utilities module
)
```

**Most Common:**
```python
# Simple case
result = extract_lyrics("song.mp3")

# Full control
extractor = LyricsExtractor(model_size="large-v3", device="cuda")
result = extractor.extract("song.mp3", include_timestamps=True)
```

**Result Structure:**
```python
{
    'lyrics': str,           # Formatted lyrics
    'language': str,         # 'en', 'vi', 'mixed', 'unknown'
    'words': List[Dict],     # Word timestamps (if requested)
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

## Getting Help

- 📖 **Documentation**: [README.md](../README.md)
- 🔧 **Integration**: [INTEGRATION.md](../INTEGRATION.md)
- 📝 **Examples**: [examples/](../examples/)
- ❓ **FAQ**: Above in this quick start

Happy extracting! 🎵
