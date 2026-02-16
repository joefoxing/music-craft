# Quick Start Commands

## Fastest Way to Get Started (Docker)

```bash
# One command to rule them all
bash start-lyrics-service.sh
```

That's it! The service will be running at http://localhost:8000

## Alternative: Using Make

```bash
# Start everything
make -f Makefile.lyrics start

# View logs
make -f Makefile.lyrics logs

# Check health
make -f Makefile.lyrics health

# Stop
make -f Makefile.lyrics stop
```

## Alternative: Manual Docker Compose

```bash
# CPU version
docker compose -f docker-compose.lyrics.yml up --build -d

# GPU version (requires NVIDIA GPU)
docker compose -f docker-compose.lyrics-gpu.yml up --build -d

# View logs
docker compose -f docker-compose.lyrics.yml logs -f

# Stop
docker compose -f docker-compose.lyrics.yml down
```

## Test It

```bash
# Using test script
python test_lyrics_service.py path/to/your_song.mp3

# Or manually with curl
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@your_song.mp3" \
  -F "language_hint=auto"

# Get the job_id from response, then:
curl http://localhost:8000/v1/lyrics/{job_id}
```

## Development (No Docker)

```bash
# 1. Install dependencies
pip install -r requirements.lyrics.txt

# Also install system dependencies:
# Ubuntu/Debian: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg

# 2. Start Redis
redis-server

# 3. Terminal 1: Start API
cd app/lyrics_service
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Terminal 2: Start Worker
python -m app.lyrics_service.worker
```

## Verify Everything Works

```bash
# 1. Health check
curl http://localhost:8000/healthz

# Should return:
# {
#   "status": "healthy",
#   "service": "lyrics-extraction-service",
#   "redis_connected": true,
#   "queue_size": 0
# }

# 2. API docs
# Open browser: http://localhost:8000/docs

# 3. Submit test job
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@test.mp3" \
  -F "language_hint=en" \
  -F "timestamps=word"

# 4. Check status (replace JOB_ID)
curl http://localhost:8000/v1/lyrics/JOB_ID
```

## Common Commands

```bash
# View API logs
docker logs -f lyrics-api

# View worker logs
docker logs -f lyrics-worker

# Restart everything
docker compose -f docker-compose.lyrics.yml restart

# Remove everything (including volumes)
docker compose -f docker-compose.lyrics.yml down -v

# Scale workers
docker compose -f docker-compose.lyrics.yml up -d --scale lyrics-worker=3

# Enter API container
docker exec -it lyrics-api bash

# Enter worker container
docker exec -it lyrics-worker bash

# View Redis queue
docker exec -it lyrics-redis redis-cli
# Then: KEYS *
```

## Troubleshooting

```bash
# Check if containers are running
docker ps | grep lyrics

# Check Docker logs
docker compose -f docker-compose.lyrics.yml logs

# Check Redis
docker exec -it lyrics-redis redis-cli ping
# Should return: PONG

# Check disk space (models need space)
df -h

# Cleanup old containers
docker system prune

# Rebuild from scratch
docker compose -f docker-compose.lyrics.yml down -v
docker compose -f docker-compose.lyrics.yml up --build
```

## Configuration

```bash
# Create/edit config
cp .env.lyrics.example .env.lyrics
nano .env.lyrics

# Important settings:
# LYRICS_DEVICE=cpu           # or 'cuda' for GPU
# LYRICS_WHISPER_MODEL=large-v3   # or tiny/base/small/medium for speed
# LYRICS_ENABLE_SEPARATION=true  # or false to skip vocal separation
```

## Integration with Flask App

See `LYRICS_SERVICE_INTEGRATION.md` for detailed integration.

Quick version:

```python
# In your Flask app
import requests

# Submit job
with open('audio.mp3', 'rb') as f:
    r = requests.post('http://lyrics-api:8000/v1/lyrics', 
                      files={'file': f},
                      data={'language_hint': 'auto'})
job_id = r.json()['job_id']

# Poll for result
import time
while True:
    r = requests.get(f'http://lyrics-api:8000/v1/lyrics/{job_id}')
    result = r.json()
    if result['status'] == 'done':
        lyrics = result['result']['lyrics']
        break
    time.sleep(2)
```

## Performance Tips

**For faster processing:**
- Use GPU: `LYRICS_DEVICE=cuda` in .env.lyrics
- Use smaller model: `LYRICS_WHISPER_MODEL=medium`
- Disable separation: `LYRICS_ENABLE_SEPARATION=false`
- Reduce beam size: `LYRICS_BEAM_SIZE=3`

**For better quality:**
- Use large model: `LYRICS_WHISPER_MODEL=large-v3`
- Enable separation: `LYRICS_ENABLE_SEPARATION=true`
- Enable preprocessing: `LYRICS_PREPROCESS_AUDIO=true`

## Next Steps

1. ✅ Start the service (see above)
2. ✅ Test with a sample audio file
3. ✅ Review the API docs at http://localhost:8000/docs
4. ✅ Integrate with your Flask app
5. ✅ Deploy to production
6. ✅ Monitor logs and metrics

## Full Documentation

- **Service README**: `LYRICS_SERVICE_README.md`
- **Integration Guide**: `LYRICS_SERVICE_INTEGRATION.md`
- **Implementation Summary**: `LYRICS_SERVICE_IMPLEMENTATION_SUMMARY.md`
- **File Tree**: `LYRICS_SERVICE_FILE_TREE.md`

---

**Everything is ready to go!** 🚀
