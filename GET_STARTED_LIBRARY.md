# Getting Started with Lyrics Extraction Library

## Quick Install

```bash
# Navigate to your project
cd e:\Developer\lyric_cover_staging

# Install the library in development mode
pip install -e ./lyrics_extraction_lib
```

## Verify Installation

```bash
python -c "from lyrics_extraction import extract_lyrics; print('✓ Ready to use!')"
```

## First Run

Create a test script:

```python
# test_lyrics.py
from lyrics_extraction import extract_lyrics

# Extract lyrics from any audio file
result = extract_lyrics("your_audio.mp3")

print("=== Extracted Lyrics ===")
print(result['lyrics'])
print(f"\nLanguage: {result['language']}")
print(f"Duration: {result['metadata']['duration_seconds']:.1f}s")
```

Run it:
```bash
python test_lyrics.py
```

## Documentation Files

The library includes comprehensive documentation:

| File | Purpose |
|------|---------|
| **README.md** | Complete API reference (500+ lines) |
| **QUICKSTART.md** | 5-minute quick start guide |
| **INTEGRATION.md** | How to integrate into your project |
| **MIGRATION.md** | Migrate from old code to library |
| **STRUCTURE.md** | Library architecture overview |

## Example Scripts

Five ready-to-run examples in `lyrics_extraction_lib/examples/`:

```bash
# Simple extraction
python lyrics_extraction_lib/examples/example_basic.py

# With timestamps
python lyrics_extraction_lib/examples/example_advanced.py

# Batch processing
python lyrics_extraction_lib/examples/example_batch.py

# Using components individually
python lyrics_extraction_lib/examples/example_components.py

# Error handling patterns
python lyrics_extraction_lib/examples/example_error_handling.py
```

## Python API

### Simplest Usage
```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics("song.mp3")
print(result['lyrics'])
```

### Full Control
```python
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(
    model_size="large-v3",
    device="cuda"  # or "cpu"
)

result = extractor.extract(
    "song.mp3",
    language="auto",
    include_timestamps=True
)

print(result['lyrics'])
print(result['language'])
print(result['metadata'])
```

### Component-Based
```python
from lyrics_extraction.pipeline import separate, transcribe, postprocess, utils

# Use individual components for custom workflows
```

## Integration into Your Project

To use in your main Flask/FastAPI app:

```python
# Instead of:
# from app.lyrics_service.pipeline import transcribe, postprocess

# Use:
from lyrics_extraction import LyricsExtractor, extract_lyrics

# That's it! Everything else stays the same
```

See [INTEGRATION.md](./lyrics_extraction_lib/INTEGRATION.md) for complete integration guide.

## Directory Structure

```
lyrics_extraction_lib/
├── lyrics_extraction/          # Main package
│   ├── extractor.py           # High-level API
│   └── pipeline/
│       ├── separate.py        # Vocal separation
│       ├── transcribe.py      # Speech-to-text
│       ├── postprocess.py     # Formatting
│       └── utils.py           # Utilities
│
├── examples/                  # 5 example scripts
│
├── README.md                  # Full documentation
├── QUICKSTART.md             # Quick start guide
├── INTEGRATION.md            # Integration guide
├── MIGRATION.md              # Migration guide
├── STRUCTURE.md              # Architecture
│
├── setup.py                  # Python packaging
├── pyproject.toml           # Modern config
└── requirements.txt         # Dependencies
```

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the right directory
cd e:\Developer\lyric_cover_staging

# Reinstall
pip install -e ./lyrics_extraction_lib

# Verify
python -c "import lyrics_extraction"
```

### ffmpeg not found
```bash
# Windows (if you have Chocolatey)
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### Slow performance
Use GPU:
```python
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(device="cuda")  # Much faster!
```

Or use smaller model:
```python
extractor = LyricsExtractor(model_size="base")  # Quick
```

## What's Next?

1. ✅ **Install** - Done! (`pip install -e ./lyrics_extraction_lib`)
2. 📚 **Read** - Check [README.md](./lyrics_extraction_lib/README.md)
3. 💡 **Try** - Run examples from `examples/` directory
4. 🔌 **Integrate** - Follow [INTEGRATION.md](./lyrics_extraction_lib/INTEGRATION.md)
5. 📝 **Migrate** - Use [MIGRATION.md](./lyrics_extraction_lib/MIGRATION.md) for existing code

## Support

- **Full Guide**: [README.md](./lyrics_extraction_lib/README.md)
- **Quick Start**: [QUICKSTART.md](./lyrics_extraction_lib/QUICKSTART.md)
- **Integration**: [INTEGRATION.md](./lyrics_extraction_lib/INTEGRATION.md)
- **Examples**: [examples/](./lyrics_extraction_lib/examples/)

---

**🎉 You're all set! Start extracting lyrics!**
