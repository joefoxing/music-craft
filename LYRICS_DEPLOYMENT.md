# Lyrics Extraction Service — Deployment & Operations Guide

## Current Deployment Status

✅ **All services operational and tested**

All containers are running with:
- **API:** Port 8000 (host-bound via docker-compose)
- **Worker:** Processing jobs from Redis queue
- **Redis:** Internal queue service (port 6379, container-only)

## Container Architecture

```yaml
# File: docker-compose.lyrics.yml

lyrics-api       # FastAPI application, processes uploads, returns job IDs
lyrics-worker    # RQ worker, processes extraction jobs
lyrics-redis     # Redis queue for job management
```

## Quick Commands

### Check Service Status

```bash
# Health check
curl http://127.0.0.1:8000/healthz

# Docker status
docker ps | grep lyrics

# Worker logs (live)
docker logs -f lyrics-worker

# API logs (live)
docker logs -f lyrics-api
```

### Restart Services

```bash
# Restart all lyrics services
docker compose -f app/docker-compose.lyrics.yml restart

# Restart only worker
docker compose -f app/docker-compose.lyrics.yml restart lyrics-worker

# Full rebuild (if code changed)
docker compose -f app/docker-compose.lyrics.yml up -d --build
```

### Monitor Queue

```bash
# Check queued jobs count
curl -s http://127.0.0.1:8000/healthz | grep queue_size

# Redis CLI access
docker exec -it lyrics-redis redis-cli

# Inside redis-cli:
> LLEN rq:queue:lyrics_extraction    # Jobs in queue
> SMEMBERS rq:workers                 # Active workers
> KEYS "rq:job:*"                     # All job records
```

### View Logs

```bash
# Worker processing
docker logs --tail 100 lyrics-worker

# API requests
docker logs --tail 100 lyrics-api

# Live stream (both)
docker logs -f lyrics-worker &
docker logs -f lyrics-api

# Search for specific job
docker logs lyrics-worker | grep "9154a45a-7fc7"
```

## Configuration Management

### Current Settings (Feb 16, 2026)

File: `/home/deploy/app/docker-compose.lyrics.yml`

**API & Worker Config:**
```yaml
LYRICS_DEVICE: cpu
LYRICS_COMPUTE_TYPE: int8
LYRICS_WHISPER_MODEL: large-v3
LYRICS_ENABLE_SEPARATION: false      # ← Vocal separation disabled
LYRICS_VAD_FILTER: false             # ← VAD disabled (processes full audio)
LYRICS_PREPROCESS_AUDIO: true
LYRICS_BEAM_SIZE: 5
LYRICS_TEMPERATURE: 0.0
LYRICS_MAX_UPLOAD_SIZE_MB: 50
LYRICS_QUEUE_TIMEOUT: 900            # 15 minutes
LYRICS_RESULT_TTL: 3600              # 1 hour retention
LOG_LEVEL: INFO
```

### How to Modify Config

1. Edit the compose file:
   ```bash
   nano app/docker-compose.lyrics.yml
   ```

2. Update the `environment:` section under `lyrics-api` and `lyrics-worker`

3. Restart containers:
   ```bash
   docker compose -f app/docker-compose.lyrics.yml up -d --no-deps --force-recreate lyrics-api lyrics-worker
   ```

4. Verify change applied:
   ```bash
   docker logs lyrics-worker | head -20
   ```

## Volume Management

### Shared Volumes

```bash
# Temporary extraction files (shared between API and worker)
docker volume ls | grep lyrics_temp

# Whisper model cache (cached weights for faster reuse)
docker volume ls | grep lyrics_whisper_cache

# List files in temp volume
docker run --rm -v lyrics_temp:/data busybox ls -la /data/

# Clean temp files (warning: removes current uploads)
docker volume rm lyrics_temp
docker volume create lyrics_temp
```

## Testing & Validation

### 1. Basic Functionality Test

```bash
# Create 3-second test tone
python3 - << 'EOF'
import wave, math, struct
with wave.open('test.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    for i in range(48000):
        v = int(12000 * math.sin(2 * math.pi * 440 * i / 16000))
        w.writeframes(struct.pack('<h', v))
EOF

# Upload and process
curl -F "file=@test.wav" http://127.0.0.1:8000/v1/lyrics

# Expected: queued status with job_id
```

### 2. Real Audio Test

```bash
# Use one of your uploaded files
curl -F "file=@vocal_candidate.wav" http://127.0.0.1:8000/v1/lyrics

# Monitor with SSE
curl -N http://127.0.0.1:8000/v1/lyrics/<job_id>/events

# Check result
curl http://127.0.0.1:8000/v1/lyrics/<job_id>

# Expected: status "done" with lyrics extracted
```

### 3. Load Test (Multiple Concurrent Jobs)

```bash
for i in {1..5}; do
    echo "Uploading job $i..."
    curl -F "file=@vocal_candidate.wav" http://127.0.0.1:8000/v1/lyrics &
done
wait

# Monitor queue size
watch -n 1 'curl -s http://127.0.0.1:8000/healthz | python3 -c "import sys,json; print(f\"Queue: {json.load(sys.stdin)['\''queue_size'\'']}\"")'
```

## Known Limitations & Notes

### Current Implementation

| Feature | Status | Notes |
|---------|--------|-------|
| Basic transcription | ✅ Working | Full audio, no separation |
| Vocal separation | ⚠️ Available | Disabled by default; can re-enable for music |
| VAD filter | ⚠️ Available | Disabled by default; tends to remove audio |
| Progress tracking | ✅ Working | Via SSE or status polling |
| Multi-job queue | ✅ Working | Can handle multiple jobs |
| Language detection | ✅ Working | Auto-detects English, etc. |
| Word timestamps | 🔄 Implemented | Not exposed in UI yet |
| Speaker diarization | ❌ Not supported | Form parameter accepted but unused |

### Performance Profile

- **Model Load Time:** ~30-45 seconds (first job cold start)
- **Processing Time (1s audio):** ~25-30 seconds total (CPU bound)
- **Memory Usage:** ~2-3 GB peak (large-v3 model)
- **Disk Usage:** ~5 GB for model cache (cached after first use)

### Supported Audio Formats

- `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.aac`, `.opus`, `.wma`
- Max file size: 50 MB (configurable)
- Any sample rate (auto-normalized by ffmpeg)
- Mono or stereo (auto-converted)

## Troubleshooting

### Issue: Queue is growing, jobs not processing

**Symptoms:**
- Health check shows `queue_size > 0` but not decreasing
- Workers not active (`docker logs lyrics-worker` shows no recent activity)

**Solutions:**
```bash
# 1. Check if worker is running
docker ps | grep lyrics-worker

# 2. Restart worker
docker compose -f app/docker-compose.lyrics.yml restart lyrics-worker

# 3. Check for Python errors
docker logs lyrics-worker

# 4. Clear stale worker registrations (if needed)
docker exec lyrics-redis redis-cli
> FLUSHDB    # Warning: clears all job data
```

### Issue: API returns 502 or Connection Refused

**Symptoms:**
- `curl: (7) Failed to connect to 127.0.0.1 port 8000`

**Solutions:**
```bash
# 1. Check if API container is running
docker ps | grep lyrics-api

# 2. Restart API
docker compose -f app/docker-compose.lyrics.yml restart lyrics-api

# 3. Check API logs
docker logs lyrics-api | tail -50

# 4. Verify port mapping
docker port lyrics-api
```

### Issue: Jobs timeout or never complete

**Symptoms:**
- Status stays "running" indefinitely
- Docker logs show processing steps but then silence

**Solutions:**
```bash
# 1. Increase timeout in compose
# Edit: LYRICS_QUEUE_TIMEOUT=1800 (30 minutes)
docker compose -f app/docker-compose.lyrics.yml up -d --no-deps --force-recreate

# 2. Check worker memory/CPU
docker stats lyrics-worker

# 3. Check disk space
df -h /tmp/lyrics_extraction

# 4. Reduce model size (faster, less memory)
# Edit: LYRICS_WHISPER_MODEL=medium or small
```

### Issue: Memory spike / OOM killer

**Symptoms:**
- Worker stops with no error, container restarts
- Logs show `OutOfMemory` or kernel messages

**Solutions:**
```bash
# 1. Increase Docker memory limit (in compose)
# Add to lyrics-worker service:
deploy:
  resources:
    limits:
      memory: 12G  # Increase from 8G

# 2. Use smaller model
LYRICS_WHISPER_MODEL: medium

# 3. Limit concurrent jobs (processing one at a time)
# Redis config: rq:max-workers=1
```

## Maintenance

### Daily

```bash
# Monitor queue (during office hours)
watch -n 30 'curl -s http://127.0.0.1:8000/healthz | python3 -m json.tool'

# Check logs for errors
docker logs lyrics-worker | grep ERROR
docker logs lyrics-api | grep ERROR
```

### Weekly

```bash
# Clean old job records from Redis (older than 1 hour)
# (Automatic, enabled by result_ttl: 3600)

# Check disk usage
du -sh /var/lib/docker/volumes/lyrics_*

# Restart services for clean slate
docker compose -f app/docker-compose.lyrics.yml restart
```

### Monthly

```bash
# Rebuild containers (updates dependencies if Dockerfile changed)
docker compose -f app/docker-compose.lyrics.yml up -d --build

# Prune unused Docker artifacts
docker system prune -a

# Review and tune configuration based on metrics
docker logs lyrics-worker | grep "extraction" | tail -20
```

## Scaling Considerations

### Single-Instance (Current)

- **Concurrency:** Sequential (1 job at a time)
- **Throughput:** ~1 job per 30-60 seconds (CPU bound)
- **Deployment:** All on one host
- **Bottleneck:** Whisper model inference on CPU

### Future: Multi-Worker Setup

To handle more concurrent jobs:

1. **Option A: Multiple Worker Containers**
   ```yaml
   lyrics-worker-1:
     # ...same config
   lyrics-worker-2:
     # ...same config
   lyrics-worker-3:
     # ...same config
   ```
   - Pros: Simple, uses host CPU cores
   - Cons: High memory per worker (each loads full Whisper model)

2. **Option B: GPU Acceleration**
   ```yaml
   LYRICS_DEVICE: cuda
   LYRICS_COMPUTE_TYPE: float16
   ```
   - Pros: 5-10x speedup per job
   - Cons: Requires NVIDIA GPU

3. **Option C: Kubernetes Deployment**
   - Auto-scaling based on queue depth
   - Better resource isolation

## Monitoring

### Via Health Endpoint

```bash
# Every 10 seconds
watch -n 10 'curl -s http://127.0.0.1:8000/healthz | python3 -m json.tool'
```

### Via Docker Stats

```bash
# Monitor resource usage
docker stats lyrics-api lyrics-worker lyrics-redis
```

### Via Logs

```bash
# Follow all service logs
docker compose -f app/docker-compose.lyrics.yml logs -f

# Search logs for patterns
docker logs lyrics-worker | grep "Successfully extracted"
docker logs lyrics-worker | grep "ERROR\|FAIL"
```

## Backup & Recovery

### Backup Job Results

```bash
# Export active jobs from Redis
docker exec lyrics-redis redis-cli SAVE
docker cp lyrics-redis:/data/dump.rdb ./redis-backup-$(date +%s).rdb
```

### Recovery

```bash
# Restore Redis state
docker cp redis-backup-*.rdb lyrics-redis:/data/dump.rdb
docker exec lyrics-redis redis-cli BGREWRITEAOF
```

## Related Documentation

- [API Endpoints](LYRICS_API.md)
- [Configuration Reference](app/lyrics_service/config.py)
- [Architecture Overview](app/lyrics_service/README.md)

---

**Last Updated:** February 16, 2026  
**Deployment Version:** 1.0.0
