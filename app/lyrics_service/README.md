# Lyrics Extraction Service

Extract lyrics from audio files using Whisper ASR with a REST API.

## Quick Start

### 1. Check Service Status

```bash
curl http://127.0.0.1:8000/healthz
```

### 2. Upload Audio & Get Job ID

```bash
curl -F "file=@song.wav" http://127.0.0.1:8000/v1/lyrics
```

Response:
```json
{
  "job_id": "abc12345-...",
  "status": "queued"
}
```

### 3. Check Result

```bash
curl http://127.0.0.1:8000/v1/lyrics/abc12345-.../
```

Response (when done):
```json
{
  "job_id": "abc12345-...",
  "status": "done",
  "result": {
    "lyrics": "Thank you.",
    "raw_transcript": "Thank you."
  }
}
```

### 4. Watch Progress (Optional)

```bash
curl -N http://127.0.0.1:8000/v1/lyrics/abc12345-.../events
```

## Documentation

- **[API Reference](../LYRICS_API.md)** — Endpoint documentation, parameters, examples
- **[Deployment Guide](../LYRICS_DEPLOYMENT.md)** — Operations, configuration, troubleshooting

## Quick Commands

```bash
# Start services
docker compose -f ../docker-compose.lyrics.yml up -d

# Check logs
docker logs -f lyrics-worker

# Check health
curl http://127.0.0.1:8000/healthz

# Restart
docker compose -f ../docker-compose.lyrics.yml restart

# Stop
docker compose -f ../docker-compose.lyrics.yml down
```

## Architecture

```
Request → lyrics-api → Redis Queue → lyrics-worker → Whisper ASR
                              ↓
                         (progress)
                              ↓
                         Response
```

## Features

✅ Asynchronous job processing  
✅ Real-time progress via SSE  
✅ Language auto-detection  
✅ Multi-format audio support  
✅ Configurable ASR model & parameters  

## Configuration

Edit environment variables in `docker-compose.lyrics.yml`:

```yaml
LYRICS_DEVICE: cpu              # or 'cuda'
LYRICS_WHISPER_MODEL: large-v3  # or 'medium', 'small'
LYRICS_VAD_FILTER: false        # Disable audio removal
LYRICS_ENABLE_SEPARATION: false # Process full audio
```

See [Deployment Guide](../LYRICS_DEPLOYMENT.md) for all options.

## Troubleshooting

### No transcripts (empty result)
- Ensure `LYRICS_VAD_FILTER=false` in compose
- Check if audio file is clear and loud enough
- View worker logs: `docker logs lyrics-worker`

### Queue growing but jobs not processing
- Restart worker: `docker compose -f ../docker-compose.lyrics.yml restart lyrics-worker`
- Check if worker is running: `docker ps | grep lyrics-worker`

### High memory usage
- Use smaller model: `LYRICS_WHISPER_MODEL=medium`
- Or enable GPU: `LYRICS_DEVICE=cuda`

See [Deployment Guide - Troubleshooting](../LYRICS_DEPLOYMENT.md#troubleshooting) for more.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/lyrics` | Upload & enqueue job |
| GET | `/v1/lyrics/{job_id}` | Check status & result |
| GET | `/v1/lyrics/{job_id}/events` | Stream progress (SSE) |
| GET | `/healthz` | Service health check |

Full details in [API Reference](../LYRICS_API.md).

## Service Status

✅ **Operational** (as of Feb 16, 2026)

- API: Port 8000
- Worker: Active
- Redis: Ready
- Model: Whisper large-v3 (cached)

---

For detailed information, see the documentation files in the parent directory.
