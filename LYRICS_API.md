# Lyrics Extraction API Documentation

## Overview

The Lyrics Extraction Service provides a REST API for extracting lyrics from audio files using Whisper ASR (Automatic Speech Recognition). The service processes uploads asynchronously via a Redis-backed job queue, allowing you to monitor progress in real time.

## Service Status

**Current Status:** ✅ Operational

- **API Endpoint:** `http://127.0.0.1:8000`
- **Queue Service:** Redis (internal, port 6379)
- **Worker Configuration:**
  - Model: faster-whisper large-v3
  - Device: CPU (int8 quantization)
  - VAD Filter: Disabled (processes full audio)
  - Vocal Separation: Disabled (uses full audio, not isolated vocals)

## Quick Start

### 1. Health Check

```bash
curl -s http://127.0.0.1:8000/healthz | python3 -m json.tool
```

**Response:**
```json
{
  "status": "healthy",
  "service": "lyrics-extraction-service",
  "version": "1.0.0",
  "redis_connected": true,
  "queue_size": 0
}
```

### 2. Upload and Enqueue Job

```bash
curl -F "file=@song.wav" \
     -F "language_hint=auto" \
     http://127.0.0.1:8000/v1/lyrics
```

**Response (HTTP 202 Accepted):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "queued",
  "result": null,
  "meta": {
    "queue_position": 0,
    "language_hint": "auto",
    "timestamps": "none"
  },
  "error": null
}
```

### 3. Check Job Status

```bash
curl -s http://127.0.0.1:8000/v1/lyrics/abc12345-6789-.../
```

**Response (Job Running):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "running",
  "meta": {
    "progress": 60,
    "stage": "transcribing",
    "duration_sec": 1.0
  }
}
```

**Response (Job Complete):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "done",
  "result": {
    "lyrics": "Thank you.",
    "raw_transcript": "Thank you."
  },
  "meta": {
    "progress": 100,
    "stage": "done",
    "duration_sec": 1.0,
    "language_detected": "en",
    "model": {
      "separator": null,
      "asr": "faster-whisper large-v3"
    }
  },
  "error": null
}
```

### 4. Stream Progress (Server-Sent Events)

Open an SSE connection to watch job progress in real time:

```bash
curl -N http://127.0.0.1:8000/v1/lyrics/abc12345-6789-.../events
```

**Event Stream Output:**
```
data: {"job_id": "abc12345-...", "status": "started", "meta": {"progress": 0, "stage": "started"}}

data: {"job_id": "abc12345-...", "status": "started", "meta": {"progress": 60, "stage": "transcribing"}}

data: {"job_id": "abc12345-...", "status": "finished", "meta": {"progress": 100, "stage": "done", "duration_sec": 1.0}}
```

## API Endpoints

### `POST /v1/lyrics` — Create Lyrics Extraction Job

**Request:**
- **Content-Type:** multipart/form-data
- **Fields:**
  - `file` (file, required): Audio file (supported: .mp3, .wav, .flac, .ogg, .m4a, .aac, .opus, .wma)
  - `language_hint` (string, optional): Language hint for ASR. Default: `"auto"`
    - Valid values: `"en"`, `"vi"`, `"auto"`
  - `timestamps` (string, optional): Timestamp mode. Default: `"none"`
    - Valid values: `"none"`, `"word"`
  - `diarize` (boolean, optional): Speaker diarization (currently unsupported). Default: `false`

**Response (HTTP 202 Accepted):**
```json
{
  "job_id": "string",
  "status": "queued",
  "result": null,
  "meta": {
    "queue_position": 0,
    "language_hint": "string",
    "timestamps": "string"
  },
  "error": null
}
```

**Example:**
```bash
curl -X POST \
  -F "file=@audio.wav" \
  -F "language_hint=auto" \
  -F "timestamps=none" \
  http://127.0.0.1:8000/v1/lyrics
```

---

### `GET /v1/lyrics/{job_id}` — Get Job Status and Result

**Request:**
- **Path Parameters:**
  - `job_id` (string, required): Job ID returned from creation

**Response:**
```json
{
  "job_id": "string",
  "status": "queued|running|done|error|not_found",
  "result": {
    "lyrics": "string (formatted lyrics)",
    "raw_transcript": "string (unformatted text)"
  } | null,
  "meta": {
    "progress": 0-100,
    "stage": "string",
    "duration_sec": number,
    "language_detected": "string",
    "model": {
      "separator": null | "string",
      "asr": "string"
    }
  } | null,
  "error": {
    "code": "string",
    "message": "string"
  } | null
}
```

**Status Values:**
- `queued`: Job waiting to be processed
- `running`: Job currently being processed
- `done`: Job completed successfully (result available)
- `error`: Job failed (error details available)
- `not_found`: Job ID not found or expired

**Progress Stages:**
- `started`: Validation and setup
- `validated`: Input validation passed
- `preprocessed`: Audio preprocessing complete
- `separating`: Vocal separation starting
- `separated`: Vocal separation complete
- `transcribing`: Whisper transcription in progress
- `transcribed`: Transcription complete
- `postprocessing`: Formatting and cleanup
- `done`: Success
- `error`: Processing failed

**Example:**
```bash
curl -s http://127.0.0.1:8000/v1/lyrics/abc12345-6789-.../ | python3 -m json.tool
```

---

### `GET /v1/lyrics/{job_id}/events` — Stream Job Progress (SSE)

**Request:**
- **Path Parameters:**
  - `job_id` (string, required): Job ID returned from creation
- **Accept:** text/event-stream

**Response:** Server-Sent Events stream of progress updates

**Event Format:**
```
data: {"job_id": "string", "status": "string", "meta": {...}}

```

Stream continues until job status is `finished` or `failed`, then closes.

**Example with curl:**
```bash
curl -N http://127.0.0.1:8000/v1/lyrics/abc12345-6789-.../events
```

**Example with Python:**
```python
import requests
import json

job_id = "abc12345-6789-..."
url = f"http://127.0.0.1:8000/v1/lyrics/{job_id}/events"

with requests.get(url, stream=True) as r:
    for line in r.iter_lines():
        if line.startswith(b"data: "):
            event = json.loads(line[6:])
            print(f"Status: {event['status']}, Progress: {event['meta'].get('progress')}%")
```

---

### `GET /healthz` — Health Check

**Request:**
- No parameters

**Response:**
```json
{
  "status": "healthy|unhealthy",
  "service": "lyrics-extraction-service",
  "version": "1.0.0",
  "redis_connected": true|false,
  "queue_size": 0
}
```

**Example:**
```bash
curl -s http://127.0.0.1:8000/healthz | python3 -m json.tool
```

---

## Configuration

Edit `/home/deploy/app/docker-compose.lyrics.yml` to adjust the following environment variables:

### API & Worker Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LYRICS_DEVICE` | `cpu` | Processing device: `cpu` or `cuda` |
| `LYRICS_COMPUTE_TYPE` | `int8` | Quantization: `int8` (CPU), `float16` (CUDA) |
| `LYRICS_WHISPER_MODEL` | `large-v3` | Whisper model size (affects accuracy vs speed) |
| `LYRICS_ENABLE_SEPARATION` | `false` | Enable vocal separation (True: isolates vocals; False: uses full audio) |
| `LYRICS_VAD_FILTER` | `false` | Enable Voice Activity Detection (True: removes silence; False: processes full audio) |
| `LYRICS_PREPROCESS_AUDIO` | `true` | Enable ffmpeg preprocessing (normalize sample rate/channels) |
| `LYRICS_BEAM_SIZE` | `5` | Whisper beam search width (higher = more accurate, slower) |
| `LYRICS_TEMPERATURE` | `0.0` | Sampling temperature (0.0 = deterministic) |
| `LYRICS_MAX_UPLOAD_SIZE_MB` | `50` | Maximum upload file size in MB |
| `LYRICS_QUEUE_TIMEOUT` | `900` | Job timeout in seconds (15 minutes default) |
| `LYRICS_RESULT_TTL` | `3600` | Result storage TTL in seconds (1 hour default) |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

### Tuning Guide

**For Better Accuracy:**
```yaml
LYRICS_WHISPER_MODEL: large-v3      # Use large model (slower but more accurate)
LYRICS_BEAM_SIZE: 10                # Increase beam search (slower)
LYRICS_TEMPERATURE: 0.1             # Slight variation for robustness
LYRICS_VAD_FILTER: false            # Process full audio
```

**For Faster Processing:**
```yaml
LYRICS_WHISPER_MODEL: medium        # Smaller model (faster)
LYRICS_BEAM_SIZE: 3                 # Lower beam search (faster)
LYRICS_ENABLE_SEPARATION: false     # Skip vocal separation (faster)
```

**For Music with Backing Tracks:**
```yaml
LYRICS_ENABLE_SEPARATION: true      # Isolate vocals only
LYRICS_VAD_FILTER: false            # Process full vocals track
```

## Error Handling

### Common Error Responses

**File Too Large (HTTP 413):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "error",
  "error": {
    "code": "file_too_large",
    "message": "File size exceeds 50MB limit"
  }
}
```

**Invalid File Type (HTTP 400):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "error",
  "error": {
    "code": "invalid_file_type",
    "message": "File type .xyz not supported. Allowed: .mp3, .wav, ..."
  }
}
```

**Processing Failed (HTTP 200, status: error):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "error",
  "meta": {
    "progress": 100,
    "stage": "error"
  },
  "error": {
    "code": "extraction_failed",
    "message": "Invalid audio file: audio duration too short"
  }
}
```

**Job Expired (HTTP 200, status: not_found):**
```json
{
  "job_id": "abc12345-6789-...",
  "status": "not_found",
  "error": {
    "code": "not_found",
    "message": "Job not found or expired"
  }
}
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ (REST API)
┌──────▼──────────────┐
│  lyrics-api         │
│  (FastAPI/Uvicorn)  │
└──────┬──────────────┘
       │ (Redis Queue)
┌──────▼──────────────┐
│  lyrics-redis       │
│  (Job Queue)        │
└──────┬──────────────┘
       │ (RQ Worker)
┌──────▼──────────────┐
│  lyrics-worker      │
│  (Processing)       │
│  - ffmpeg           │
│  - faster-whisper   │
│  - demucs (optional)│
└─────────────────────┘
```

## Troubleshooting

### No Transcripts (Empty Result)

**Issue:** Transcription returns 0 segments or empty lyrics.

**Solutions:**
1. Check if `LYRICS_VAD_FILTER=false` in compose (if true, VAD may remove all audio)
2. Try with `LYRICS_ENABLE_SEPARATION=false` to use full audio
3. Verify audio file quality and volume (very quiet or compressed files may not work)
4. Check worker logs: `docker logs lyrics-worker`

### Jobs Stuck in Queue

**Issue:** Jobs not processing; worker not running.

**Solutions:**
1. Check if worker is running: `docker ps | grep lyrics-worker`
2. Restart worker: `docker compose -f app/docker-compose.lyrics.yml restart lyrics-worker`
3. Check Redis connection: `curl http://127.0.0.1:8000/healthz`
4. View worker logs: `docker logs -f lyrics-worker`

### High Memory Usage

**Issue:** Worker consuming too much memory.

**Solutions:**
1. Reduce model size: Change `LYRICS_WHISPER_MODEL` to `medium` or `small`
2. Lower quantization: Change `LYRICS_COMPUTE_TYPE` to `int8` (already optimized)
3. Set job timeout: Increase `LYRICS_QUEUE_TIMEOUT` for long files
4. Limit concurrent jobs via RQ configuration

## Example Workflows

### Workflow 1: Batch Processing with Progress Polling

```bash
#!/bin/bash

# Upload file
response=$(curl -s -F "file=@song.wav" http://127.0.0.1:8000/v1/lyrics)
job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

# Poll status until done
while true; do
    status=$(curl -s "http://127.0.0.1:8000/v1/lyrics/$job_id")
    state=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    
    if [ "$state" = "done" ]; then
        echo "Lyrics: $(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['lyrics'])")"
        break
    elif [ "$state" = "error" ]; then
        echo "Error: $(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin)['error']['message'])")"
        break
    fi
    
    progress=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin)['meta']['progress'])")
    echo "Progress: $progress%"
    sleep 2
done
```

### Workflow 2: Real-Time Progress Streaming (SSE)

```bash
#!/bin/bash

# Upload file
response=$(curl -s -F "file=@song.wav" http://127.0.0.1:8000/v1/lyrics)
job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

# Stream progress
curl -N "http://127.0.0.1:8000/v1/lyrics/$job_id/events" | \
  python3 -c "
import sys, json
for line in sys.stdin:
    if line.startswith('data: '):
        event = json.loads(line[6:])
        meta = event.get('meta', {})
        print(f\"Progress: {meta.get('progress')}% - {meta.get('stage')}\")
        if event['status'] in ('finished', 'error'):
            break
"

# Fetch final result
curl -s "http://127.0.0.1:8000/v1/lyrics/$job_id" | python3 -m json.tool
```

### Workflow 3: Multi-File Processing

```bash
#!/bin/bash

for file in *.wav; do
    echo "Processing: $file"
    
    response=$(curl -s -F "file=@$file" http://127.0.0.1:8000/v1/lyrics)
    job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
    
    echo "$file -> $job_id" >> jobs.txt
done

# Monitor all jobs
echo "Waiting for all jobs to complete..."
sleep 5
python3 << 'EOF'
import requests
import json

with open('jobs.txt') as f:
    for line in f:
        filename, job_id = line.strip().split(' -> ')
        resp = requests.get(f"http://127.0.0.1:8000/v1/lyrics/{job_id}").json()
        status = resp['status']
        lyrics = resp.get('result', {}).get('lyrics', '(no transcription)')
        print(f"{filename}: {status} - {lyrics[:50]}")
EOF
```

## Support & Debugging

For detailed debugging:

1. **Check API logs:**
   ```bash
   docker logs -f lyrics-api
   ```

2. **Check worker logs:**
   ```bash
   docker logs -f lyrics-worker
   ```

3. **Check Redis queue:**
   ```bash
   docker exec lyrics-redis redis-cli LLEN rq:queue:lyrics_extraction
   docker exec lyrics-redis redis-cli HGETALL rq:job:<job_id>
   ```

4. **Restart all services:**
   ```bash
   docker compose -f app/docker-compose.lyrics.yml restart
   ```

---

**Last Updated:** February 16, 2026  
**Service Version:** 1.0.0
