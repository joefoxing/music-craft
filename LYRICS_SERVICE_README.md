# Lyrics Extraction Microservice

## Overview

Production-grade HTTP microservice for extracting lyrics from audio files using:
1. **Vocal Isolation** - Demucs (htdemucs) for source separation
2. **Speech-to-Text** - faster-whisper (large-v3) for ASR tuned for singing
3. **Post-processing** - Python heuristics for cleaning and formatting

Supports English/Vietnamese mixed content with optional word-level timestamps.

## Features

- ✅ Async job-based processing (no timeouts)
- ✅ Redis + RQ for job queue
- ✅ GPU and CPU support
- ✅ Safe file upload handling with size limits
- ✅ ffmpeg audio preprocessing (mono, 16kHz, filters)
- ✅ Deterministic decoding (temperature=0.0)
- ✅ Structured logging
- ✅ Docker & Docker Compose ready
- ✅ Health check endpoint
- ✅ No lyrics invention (only ASR output)
- ✅ No translation (preserves original language)

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /v1/lyrics (upload)
       ↓
┌─────────────────┐
│   FastAPI API   │──→ Returns job_id immediately
└────────┬────────┘
         │ Enqueue job
         ↓
┌─────────────────┐
│   Redis Queue   │
└────────┬────────┘
         │ Fetch job
         ↓
┌─────────────────┐
│   RQ Worker     │──→ Processes: separate → transcribe → postprocess
└─────────────────┘
         ↑
         │ GET /v1/lyrics/{job_id}
    ┌────┴────┐
    │ Client  │
    └─────────┘
```

## File Structure

```
app/lyrics_service/
├── __init__.py
├── main.py              # FastAPI routes (POST /v1/lyrics, GET /v1/lyrics/{job_id})
├── worker.py            # RQ worker entrypoint
├── config.py            # Configuration from env vars
└── pipeline/
    ├── __init__.py
    ├── separate.py      # Demucs vocal separation
    ├── transcribe.py    # faster-whisper ASR
    ├── postprocess.py   # Lyrics cleaning/formatting
    └── utils.py         # ffmpeg helpers, temp dirs, validation

Dockerfile.lyrics                 # Production Dockerfile
docker-compose.lyrics.yml         # CPU deployment
docker-compose.lyrics-gpu.yml     # GPU deployment
requirements.lyrics.txt           # Python dependencies
```

## API Endpoints

### POST /v1/lyrics

Create a lyrics extraction job.

**Request:**
```bash
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@song.mp3" \
  -F "language_hint=auto" \
  -F "timestamps=none"
```

**Fields:**
- `file` (required): Audio file (mp3, wav, flac, ogg, m4a, aac, opus, wma)
- `language_hint` (optional): "en", "vi", or "auto" (default: "auto")
- `timestamps` (optional): "none" or "word" (default: "none")
- `diarize` (optional): Always false, ignored

**Response:** (202 Accepted)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "meta": {
    "queue_position": 1,
    "language_hint": "auto",
    "timestamps": "none"
  }
}
```

### GET /v1/lyrics/{job_id}

Get job status and result.

**Request:**
```bash
curl http://localhost:8000/v1/lyrics/550e8400-e29b-41d4-a716-446655440000
```

**Response (Processing):**
```json
{
  "job_id": "...",
  "status": "running"
}
```

**Response (Success):**
```json
{
  "job_id": "...",
  "status": "done",
  "result": {
    "lyrics": "Never gonna give you up\nNever gonna let you down...",
    "words": [
      {"word": "Never", "start": 0.5, "end": 0.8},
      {"word": "gonna", "start": 0.9, "end": 1.1}
    ]
  },
  "meta": {
    "duration_sec": 213.5,
    "language_detected": "en",
    "model": {
      "separator": "htdemucs",
      "asr": "faster-whisper large-v3"
    }
  }
}
```

**Response (Error):**
```json
{
  "job_id": "...",
  "status": "error",
  "error": {
    "code": "extraction_failed",
    "message": "Audio file validation failed"
  }
}
```

**Status Values:**
- `queued` - Waiting to be processed
- `running` - Currently processing
- `done` - Completed successfully
- `error` - Failed
- `not_found` - Job ID not found or expired

### GET /healthz

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "lyrics-extraction-service",
  "version": "1.0.0",
  "redis_connected": true,
  "queue_size": 3
}
```

## Configuration (Environment Variables)

### Service Settings
- `LYRICS_SERVICE_NAME` - Service name (default: "lyrics-extraction-service")
- `LYRICS_SERVICE_VERSION` - Version (default: "1.0.0")
- `LYRICS_API_PREFIX` - API prefix (default: "/v1")
- `LOG_LEVEL` - Logging level (default: "INFO")

### Redis Settings
- `REDIS_HOST` - Redis hostname (default: "localhost")
- `REDIS_PORT` - Redis port (default: "6379")
- `REDIS_DB` - Redis database number (default: "0")
- `REDIS_PASSWORD` - Redis password (optional)

### Queue Settings
- `LYRICS_QUEUE_NAME` - RQ queue name (default: "lyrics_extraction")
- `LYRICS_QUEUE_TIMEOUT` - Job timeout in seconds (default: "900")
- `LYRICS_RESULT_TTL` - Result TTL in seconds (default: "3600")

### Upload Settings
- `LYRICS_MAX_UPLOAD_SIZE_MB` - Max file size (default: "50")

### Model Settings
- `LYRICS_WHISPER_MODEL` - Whisper model size (default: "large-v3")
  - Options: tiny, base, small, medium, large-v2, large-v3, turbo
- `LYRICS_DEMUCS_MODEL` - Demucs model (default: "htdemucs")

### Device Settings
- `LYRICS_DEVICE` - Device type (default: "cpu")
  - Options: "cpu", "cuda"
- `LYRICS_COMPUTE_TYPE` - Compute type (default: "int8" for CPU, "float16" for GPU)
  - CPU: int8, int8_float16, float32
  - GPU: float16, int8_float16

### Processing Settings
- `LYRICS_ENABLE_SEPARATION` - Enable vocal separation (default: "true")
- `LYRICS_PREPROCESS_AUDIO` - Enable ffmpeg preprocessing (default: "true")
- `LYRICS_VAD_FILTER` - Enable VAD filter (default: "true")
- `LYRICS_BEAM_SIZE` - Beam size for decoding (default: "5")
- `LYRICS_TEMPERATURE` - Sampling temperature (default: "0.0")

### System Settings
- `LYRICS_TEMP_DIR` - Temporary files directory (default: "/tmp/lyrics_extraction")
- `LYRICS_MAX_CONCURRENT_JOBS` - Max concurrent jobs (default: "1")

## Running Locally

### Using Docker Compose (Recommended)

**CPU Version:**
```bash
# Build and start services
docker compose -f docker-compose.lyrics.yml up --build

# Services:
# - API: http://localhost:8000
# - Redis: localhost:6379
# - Worker: Running in background
```

**GPU Version:**
```bash
# Requires nvidia-docker
docker compose -f docker-compose.lyrics-gpu.yml up --build
```

### Manual Setup (Development)

**1. Install system dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg python3.11 redis-server

# macOS
brew install ffmpeg python@3.11 redis
```

**2. Install Python dependencies:**
```bash
pip install -r requirements.lyrics.txt
```

**3. Start Redis:**
```bash
redis-server
```

**4. Start API server:**
```bash
cd app/lyrics_service
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**5. Start worker (separate terminal):**
```bash
python -m app.lyrics_service.worker
```

## Example Usage

**Submit a job:**
```bash
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@my_song.mp3" \
  -F "language_hint=vi" \
  -F "timestamps=word"
```

**Check status:**
```bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"
curl http://localhost:8000/v1/lyrics/$JOB_ID
```

**Python client example:**
```python
import requests
import time

# Upload file
with open("song.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/v1/lyrics",
        files={"file": f},
        data={"language_hint": "auto", "timestamps": "word"}
    )
job_id = response.json()["job_id"]

# Poll for result
while True:
    response = requests.get(f"http://localhost:8000/v1/lyrics/{job_id}")
    data = response.json()
    
    if data["status"] == "done":
        print("Lyrics:", data["result"]["lyrics"])
        break
    elif data["status"] == "error":
        print("Error:", data["error"])
        break
    
    time.sleep(2)
```

## GPU vs CPU

### GPU Setup
- **Device:** `LYRICS_DEVICE=cuda`
- **Compute Type:** `LYRICS_COMPUTE_TYPE=float16`
- **Speed:** ~5-10x faster
- **Memory:** Requires 8GB+ VRAM for large-v3

### CPU Setup
- **Device:** `LYRICS_DEVICE=cpu`
- **Compute Type:** `LYRICS_COMPUTE_TYPE=int8`
- **Speed:** Slower but works everywhere
- **Memory:** ~4GB RAM recommended

## Post-Processing Rules

The post-processing module follows strict rules:

1. ✅ **Never adds words** - Only cleans ASR output
2. ✅ **Never translates** - Preserves original language
3. ✅ **Removes noise tags** - (music), [noise], etc.
4. ✅ **Formats line breaks** - Based on segment timing gaps
5. ✅ **Deduplicates lines** - Removes excessive repetition
6. ✅ **Normalizes spacing** - Consistent punctuation and whitespace

## Troubleshooting

**Issue: "Demucs not found"**
- Ensure demucs is installed: `pip install demucs`
- Set `LYRICS_ENABLE_SEPARATION=false` to skip separation

**Issue: "ffmpeg not found"**
- Install ffmpeg: `apt-get install ffmpeg` or `brew install ffmpeg`
- Set `LYRICS_PREPROCESS_AUDIO=false` to skip preprocessing

**Issue: "Out of memory"**
- Use smaller model: `LYRICS_WHISPER_MODEL=medium`
- Disable separation: `LYRICS_ENABLE_SEPARATION=false`
- Reduce beam size: `LYRICS_BEAM_SIZE=3`

**Issue: "Job timeout"**
- Increase timeout: `LYRICS_QUEUE_TIMEOUT=1800` (30 minutes)
- Use GPU: `LYRICS_DEVICE=cuda`

**Issue: "Lyrics quality is poor"**
- Enable separation: `LYRICS_ENABLE_SEPARATION=true`
- Use larger model: `LYRICS_WHISPER_MODEL=large-v3`
- Enable preprocessing: `LYRICS_PREPROCESS_AUDIO=true`

## Performance Notes

**Typical Processing Times (large-v3 on CPU):**
- 3-minute song: ~5-10 minutes
- 5-minute song: ~10-20 minutes

**With GPU (CUDA):**
- 3-minute song: ~1-2 minutes
- 5-minute song: ~2-4 minutes

**Optimization Tips:**
- Use GPU for production
- Use smaller models (medium/small) for faster processing
- Disable separation if vocals are already isolated
- Enable VAD filter to skip silence

## Production Deployment

### Using Docker Compose

**1. Create `.env` file:**
```env
LYRICS_DEVICE=cuda
LYRICS_COMPUTE_TYPE=float16
LYRICS_WHISPER_MODEL=large-v3
LYRICS_ENABLE_SEPARATION=true
REDIS_PASSWORD=your_secure_password
```

**2. Start services:**
```bash
docker compose -f docker-compose.lyrics-gpu.yml up -d
```

**3. Scale workers:**
```bash
docker compose -f docker-compose.lyrics-gpu.yml up -d --scale lyrics-worker-gpu=3
```

### Monitoring

- Check API health: `curl http://localhost:8000/healthz`
- Monitor Redis: `redis-cli info`
- View worker logs: `docker logs lyrics-worker`

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

See project LICENSE file.

## Credits

- **faster-whisper**: https://github.com/guillaumekln/faster-whisper
- **Demucs**: https://github.com/facebookresearch/demucs
- **FastAPI**: https://fastapi.tiangolo.com/
- **RQ**: https://python-rq.org/
