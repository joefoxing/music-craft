# Lyrics Extraction Library - Integration Guide

This guide shows how to integrate the lyrics extraction library into your existing project.

## Installation

### Option 1: Local Installation (Development)
```bash
# From your main project directory
pip install -e ./lyrics_extraction_lib
```

### Option 2: PyPI Installation (Production)
```bash
pip install lyrics-extraction
```

### Option 3: Git Installation
```bash
pip install git+https://github.com/lyric-cover-staging/lyrics-extraction-lib.git
```

## Integration Examples

### 1. Simple Flask Integration

In your Flask app:

```python
from flask import Flask, request, jsonify
from lyrics_extraction import extract_lyrics
import tempfile
import os

app = Flask(__name__)

@app.route('/api/extract-lyrics', methods=['POST'])
def extract_lyrics_endpoint():
    """Extract lyrics from uploaded audio."""
    
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        file.save(tmp.name)
        
        try:
            result = extract_lyrics(
                tmp.name,
                model_size="base",  # Faster for API
                language=request.form.get('language', 'auto'),
                include_timestamps=request.form.get('timestamps', False)
            )
            
            return jsonify(result)
        
        finally:
            os.unlink(tmp.name)

if __name__ == '__main__':
    app.run()
```

### 2. Job Queue Integration (Celery)

For async processing with Celery:

```python
from celery import Celery, Task
from lyrics_extraction import LyricsExtractor
import redis

app = Celery('lyrics_tasks')
app.conf.broker_url = 'redis://localhost:6379'
app.conf.result_backend = 'redis://localhost:6379'

# Initialize extractor once
extractor = LyricsExtractor(
    model_size="large-v3",
    device="cuda"  # GPU for batch processing
)

@app.task(bind=True)
def extract_lyrics_task(self, audio_path: str, language: str = "auto"):
    """Background task to extract lyrics."""
    
    try:
        # Update progress
        self.update_state(state='PROCESSING', meta={'current': 0, 'total': 100})
        
        result = extractor.extract(
            audio_path,
            language=language,
            include_timestamps=True
        )
        
        return {
            'status': 'success',
            'lyrics': result['lyrics'],
            'language': result['language'],
            'metadata': result['metadata']
        }
    
    except Exception as e:
        self.update_state(state='FAILURE', meta=str(e))
        raise

# Usage:
# task = extract_lyrics_task.delay('song.mp3', language='auto')
```

### 3. FastAPI Integration

```python
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from lyrics_extraction import LyricsExtractor
import tempfile
import os

app = FastAPI()
extractor = LyricsExtractor(device="cuda")

results_storage = {}  # Use database in production

@app.post("/extract")
async def extract_lyrics_endpoint(
    file: UploadFile = File(...),
    language: str = "auto",
    timestamps: bool = False,
    background_tasks: BackgroundTasks = None
):
    """Extract lyrics from uploaded audio."""
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        
        try:
            # Run in background
            def process_file(path):
                try:
                    result = extractor.extract(path, language=language, include_timestamps=timestamps)
                    results_storage[file.filename] = result
                except Exception as e:
                    results_storage[file.filename] = {'error': str(e)}
                finally:
                    os.unlink(path)
            
            background_tasks.add_task(process_file, tmp.name)
            
            return {
                'status': 'processing',
                'file': file.filename,
                'check_url': f'/result/{file.filename}'
            }
        
        except Exception as e:
            os.unlink(tmp.name)
            return {'error': str(e)}, 400

@app.get("/result/{filename}")
def get_result(filename: str):
    """Check extraction result."""
    if filename not in results_storage:
        return {'status': 'not_found'}, 404
    
    result = results_storage[filename]
    if 'error' in result:
        return {'status': 'error', 'error': result['error']}
    
    return {'status': 'complete', 'result': result}
```

### 4. Microservice Architecture

Create a dedicated lyrics service:

```python
# lyrics_service/main.py
from fastapi import FastAPI
from lyrics_extraction import LyricsExtractor
from pydantic import BaseModel
import os

app = FastAPI(title="Lyrics Extraction Service")

extractor = LyricsExtractor(
    model_size=os.getenv("WHISPER_MODEL", "large-v3"),
    device=os.getenv("DEVICE", "cuda"),
    enable_vocal_separation=os.getenv("ENABLE_SEPARATION", "true").lower() == "true"
)

class ExtractionRequest(BaseModel):
    audio_path: str
    language: str = "auto"
    include_timestamps: bool = False

class ExtractionResponse(BaseModel):
    lyrics: str
    language: str
    metadata: dict

@app.post("/extract", response_model=ExtractionResponse)
async def extract(request: ExtractionRequest):
    result = extractor.extract(
        request.audio_path,
        language=request.language,
        include_timestamps=request.include_timestamps
    )
    
    return ExtractionResponse(
        lyrics=result['lyrics'],
        language=result['language'],
        metadata=result['metadata']
    )

@app.get("/healthz")
async def health():
    return {"status": "healthy"}
```

### 5. Batch Processing Script

```python
from lyrics_extraction import LyricsExtractor
from pathlib import Path
import json
from datetime import datetime

extractor = LyricsExtractor(device="cuda")

audio_dir = Path("./music")
output_dir = Path("./lyrics")
output_dir.mkdir(exist_ok=True)

results = []

for audio_file in audio_dir.glob("**/*.mp3"):
    print(f"Processing: {audio_file.name}")
    
    try:
        result = extractor.extract(str(audio_file))
        
        # Save lyrics
        lyrics_file = output_dir / audio_file.with_suffix('.txt').name
        lyrics_file.write_text(result['lyrics'], encoding='utf-8')
        
        # Store metadata
        results.append({
            'file': audio_file.name,
            'language': result['language'],
            'length': len(result['lyrics']),
            'duration': result['metadata']['duration_seconds'],
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"✓ Saved to {lyrics_file}")
    
    except Exception as e:
        print(f"✗ Failed: {e}")
        results.append({
            'file': audio_file.name,
            'error': str(e)
        })

# Save summary
with open(output_dir / "summary.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
```

## Updating Existing Code

If you have existing lyrics extraction code:

### Before (monolithic):
```python
from app.lyrics_service.worker import process_lyrics_extraction
from app.lyrics_service import config

result = process_lyrics_extraction(job_id, audio_path)
```

### After (using library):
```python
from lyrics_extraction import extract_lyrics

result = extract_lyrics(audio_path, model_size="large-v3")
```

## Performance Considerations

### For Web APIs
```python
# Use smaller model for faster response
extractor = LyricsExtractor(model_size="base", device="cuda")
```

### For Batch Processing
```python
# Use largest model for best quality
extractor = LyricsExtractor(model_size="large-v3", device="cuda")
```

### For Limited Resources
```python
# Use CPU-friendly settings
extractor = LyricsExtractor(
    model_size="small",
    device="cpu",
    enable_vocal_separation=False  # Optional
)
```

## Upgrading from Local Code

If you're currently using the local lyrics service:

```python
# Old way:
from app.lyrics_service.pipeline import transcribe, postprocess

# New way:
from lyrics_extraction.pipeline import transcribe, postprocess

# Everything else stays the same!
```

## Error Handling

```python
from lyrics_extraction import extract_lyrics
from lyrics_extraction.pipeline import utils

try:
    result = extract_lyrics("audio.mp3")
except FileNotFoundError:
    print("Audio file not found")
except ValueError as e:
    print(f"Invalid audio: {e}")
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Configuration via Environment Variables

```bash
# .env file
LYRICS_WHISPER_MODEL=large-v3
LYRICS_DEVICE=cuda
LYRICS_COMPUTE_TYPE=float16
LYRICS_DEMUCS_MODEL=htdemucs
LYRICS_MAX_CHARS_PER_LINE=60
LYRICS_ENABLE_SEPARATION=true
LYRICS_PREPROCESS_AUDIO=true
```

Then in Python:
```python
import os
from lyrics_extraction import LyricsExtractor

extractor = LyricsExtractor(
    model_size=os.getenv('LYRICS_WHISPER_MODEL', 'large-v3'),
    device=os.getenv('LYRICS_DEVICE', 'cpu')
)
```

## Testing

```python
import pytest  
from lyrics_extraction import extract_lyrics

def test_extraction():
    """Test extraction with sample audio."""
    result = extract_lyrics("test_audio.mp3")
    
    assert 'lyrics' in result
    assert len(result['lyrics']) > 0
    assert result['language'] in ['en', 'vi', 'mixed', 'unknown']

def test_with_timestamps():
    """Test extraction with timestamps."""
    result = extract_lyrics("test_audio.mp3", include_timestamps=True)
    
    assert result['words'] is not None
    assert all('word' in w and 'start' in w and 'end' in w for w in result['words'])
```

## Monitoring

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('lyrics_extraction')

result = extract_lyrics("audio.mp3")  # Logs will show progress
```

## Support

See the [README.md](./README.md) for more information and examples.
