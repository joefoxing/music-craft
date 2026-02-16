# Complete File Tree - Lyrics Extraction Service

```
lyric_cover_staging/
│
├── app/
│   ├── lyrics_service/                          # NEW: Microservice root
│   │   ├── __init__.py
│   │   ├── config.py                           # Configuration from env vars
│   │   ├── main.py                             # FastAPI REST API server
│   │   ├── worker.py                           # RQ background worker
│   │   └── pipeline/                           # Processing pipeline
│   │       ├── __init__.py
│   │       ├── separate.py                     # Demucs vocal separation
│   │       ├── transcribe.py                   # faster-whisper ASR
│   │       ├── postprocess.py                  # Lyrics cleaning/formatting
│   │       └── utils.py                        # ffmpeg helpers, validation
│   │
│   └── services/
│       └── lyrics_extraction_service.py         # EXISTING: Can be updated to call microservice
│
├── Dockerfile.lyrics                            # NEW: Service Dockerfile
├── docker-compose.lyrics.yml                    # NEW: CPU deployment
├── docker-compose.lyrics-gpu.yml               # NEW: GPU deployment
├── requirements.lyrics.txt                      # NEW: Service dependencies
├── .env.lyrics.example                          # NEW: Environment template
│
├── Makefile.lyrics                              # NEW: Make commands
├── start-lyrics-service.sh                      # NEW: Quick start script
├── test_lyrics_service.py                       # NEW: Testing script
│
├── LYRICS_SERVICE_README.md                     # NEW: Complete documentation
├── LYRICS_SERVICE_INTEGRATION.md               # NEW: Integration guide
└── LYRICS_SERVICE_IMPLEMENTATION_SUMMARY.md    # NEW: This summary
```

## Key Files Explained

### Core Service (`app/lyrics_service/`)

**main.py** (311 lines)
- FastAPI application
- POST /v1/lyrics - Create extraction job
- GET /v1/lyrics/{job_id} - Get job status/result
- GET /healthz - Health check
- Handles file uploads, validation, job enqueueing

**worker.py** (214 lines)
- RQ worker process
- `process_lyrics_extraction()` - Main job function
- Orchestrates full pipeline: preprocess → separate → transcribe → postprocess
- Comprehensive error handling and logging
- Cleanup of temp files

**config.py** (60 lines)
- Centralized configuration
- All settings from environment variables
- Redis connection string builder
- Defaults for all parameters

### Pipeline Modules (`app/lyrics_service/pipeline/`)

**separate.py** (143 lines)
- `VocalSeparator` class wraps Demucs
- Isolates vocal stem from music
- Configurable model, device, quality settings
- Error handling for missing Demucs

**transcribe.py** (190 lines)
- `LyricsTranscriber` class wraps faster-whisper
- ASR tuned for singing (VAD, beam search, deterministic)
- Word-level timestamps support
- EN/VI support with auto-detection

**postprocess.py** (252 lines)
- `clean_transcription_text()` - Remove noise tags
- `detect_language()` - EN/VI/mixed detection
- `format_lyrics_with_timestamps()` - Smart line breaks
- `deduplicate_repetitive_lines()` - Remove repetition
- Pure Python, no LLM, no invention

**utils.py** (185 lines)
- `TempFileManager` - Context manager for temp dirs
- `preprocess_audio_ffmpeg()` - Audio normalization
- `validate_audio_file()` - File validation
- `safe_filename()` - Path sanitization
- Hash generation for deduplication

### Docker & Deployment

**Dockerfile.lyrics**
- Based on Python 3.11-slim
- Installs ffmpeg and system deps
- Installs Python packages
- Default command runs API server
- Can be overridden to run worker

**docker-compose.lyrics.yml**
- 3 services: redis, lyrics-api, lyrics-worker
- CPU configuration
- Volume mounts for data persistence
- Health checks
- Resource limits

**docker-compose.lyrics-gpu.yml**
- Same as CPU version but with GPU support
- NVIDIA GPU device mapping
- CUDA environment variables
- Optimized compute types

**requirements.lyrics.txt**
- FastAPI + Uvicorn (web server)
- Redis + RQ (job queue)
- faster-whisper (ASR)
- demucs (separation)
- Supporting libraries

### Documentation

**LYRICS_SERVICE_README.md** (600+ lines)
- Complete service documentation
- Architecture overview
- API endpoint specifications
- Configuration reference
- Quick start guides
- Troubleshooting
- Performance notes
- Examples

**LYRICS_SERVICE_INTEGRATION.md** (400+ lines)
- Integration with existing Flask app
- Deployment options
- Code examples
- Migration path
- Production considerations

**LYRICS_SERVICE_IMPLEMENTATION_SUMMARY.md**
- High-level overview
- What was implemented
- Quick reference
- Next steps

### Tools & Scripts

**Makefile.lyrics**
- `make build` - Build images
- `make start` - Start services
- `make stop` - Stop services
- `make logs` - View logs
- `make test` - Run tests
- `make health` - Check health
- Many more convenience commands

**start-lyrics-service.sh**
- One-command startup
- Checks dependencies
- Creates .env file
- Builds and starts services
- Waits for health check
- Displays usage info

**test_lyrics_service.py**
- Complete testing script
- Health check test
- Job submission test
- Status polling
- Result display
- Command-line interface

**.env.lyrics.example**
- Template for all env variables
- Documented with comments
- Defaults for development
- Notes for production

## Module Dependencies

```
main.py
├── config (env vars)
├── worker.process_lyrics_extraction (job function)
├── redis (queue connection)
└── rq (job management)

worker.py
├── config (env vars)
└── pipeline.*
    ├── utils (ffmpeg, temp files)
    ├── separate (Demucs)
    ├── transcribe (faster-whisper)
    └── postprocess (cleaning)

pipeline modules are independent and can be tested separately
```

## Data Flow

```
1. Client uploads audio    →  main.py (POST /v1/lyrics)
2. Save to temp file       →  utils.py
3. Validate file           →  utils.py
4. Enqueue job             →  redis + rq
5. Worker picks up job     →  worker.py
6. Preprocess audio        →  utils.preprocess_audio_ffmpeg()
7. Separate vocals         →  separate.VocalSeparator()
8. Transcribe              →  transcribe.LyricsTranscriber()
9. Post-process            →  postprocess.postprocess_lyrics()
10. Store result in Redis  →  rq
11. Client polls           →  main.py (GET /v1/lyrics/{id})
12. Return result          →  JSON response
```

## Environment Setup

Development:
```bash
pip install -r requirements.lyrics.txt
redis-server
python -m uvicorn app.lyrics_service.main:app --reload
python -m app.lyrics_service.worker
```

Production (Docker):
```bash
docker compose -f docker-compose.lyrics.yml up -d
```

## Port Usage

- **8000**: FastAPI API server
- **6379**: Redis (internal)

## Volume Mounts

- `redis_data`: Redis persistence
- `lyrics_temp`: Temporary processing files
- `whisper_cache`: Whisper model cache (speeds up restarts)

## CPU vs GPU

**CPU** (docker-compose.lyrics.yml):
- `LYRICS_DEVICE=cpu`
- `LYRICS_COMPUTE_TYPE=int8`
- Slower but works everywhere
- No special hardware needed

**GPU** (docker-compose.lyrics-gpu.yml):
- `LYRICS_DEVICE=cuda`
- `LYRICS_COMPUTE_TYPE=float16`
- 5-10x faster
- Requires NVIDIA GPU + nvidia-docker

## Scaling

**Horizontal scaling:**
```bash
docker compose up --scale lyrics-worker=5
```

**Vertical scaling:**
- Increase memory/CPU limits in docker-compose.yml
- Use larger/smaller Whisper models
- Enable/disable vocal separation

## Testing Checklist

- [ ] Install dependencies: `pip install -r requirements.lyrics.txt`
- [ ] Start services: `bash start-lyrics-service.sh`
- [ ] Check health: `curl http://localhost:8000/healthz`
- [ ] Submit test job: `python test_lyrics_service.py test_audio.mp3`
- [ ] View API docs: Open http://localhost:8000/docs
- [ ] Check logs: `docker logs lyrics-worker`
- [ ] Test word timestamps: `--timestamps word`
- [ ] Test Vietnamese: `--language vi`

## Integration Checklist

- [ ] Deploy lyrics service (Docker)
- [ ] Update Flask app to call microservice API
- [ ] Add LYRICS_SERVICE_URL to Flask config
- [ ] Test end-to-end workflow
- [ ] Monitor queue depth and processing times
- [ ] Set up alerts for service health
- [ ] Document for your team

---

**All files created successfully!** The implementation is complete and ready for use. 🎉
