# Integration guide for existing Flask application

This document describes how to integrate the new lyrics extraction microservice with your existing Flask application.

## Overview

The lyrics extraction service runs as a separate microservice alongside your Flask app. Your Flask app can call the service via HTTP API.

## Architecture

```
┌──────────────────┐     HTTP API      ┌─────────────────────┐
│   Flask App      │ ───────────────→  │  Lyrics Service     │
│  (Main App)      │                   │  (FastAPI + Worker) │
└──────────────────┘                   └─────────────────────┘
        │                                        │
        │                                        │
        ↓                                        ↓
  ┌──────────┐                            ┌──────────┐
  │ App DB   │                            │  Redis   │
  └──────────┘                            └──────────┘
```

## Deployment Options

### Option 1: Separate Docker Compose (Recommended)

Run the lyrics service with its own docker-compose file:

```bash
# Start lyrics service
docker compose -f docker-compose.lyrics.yml up -d

# Your main app can call http://localhost:8000/v1/lyrics
```

### Option 2: Integrated Docker Compose

Add lyrics service to your main docker-compose file:

```yaml
# In your docker-compose.yml or docker-compose.prod.yml

services:
  # Your existing services...
  web:
    # ...
  
  # Add lyrics service
  lyrics-redis:
    image: redis:7-alpine
    volumes:
      - lyrics_redis_data:/data
  
  lyrics-api:
    build:
      context: .
      dockerfile: Dockerfile.lyrics
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=lyrics-redis
    depends_on:
      - lyrics-redis
  
  lyrics-worker:
    build:
      context: .
      dockerfile: Dockerfile.lyrics
    command: python -m app.lyrics_service.worker
    environment:
      - REDIS_HOST=lyrics-redis
    depends_on:
      - lyrics-redis

volumes:
  lyrics_redis_data:
```

## Integration in Flask Code

### Option A: Replace Existing Service

Update your existing `lyrics_extraction_service.py` to call the new microservice:

```python
# app/services/lyrics_extraction_service.py

import requests
import time
from typing import Optional, Tuple
from flask import current_app

class LyricsExtractionService:
    """Service for extracting lyrics via microservice API."""
    
    def __init__(self):
        self.api_base_url = current_app.config.get(
            'LYRICS_SERVICE_URL',
            'http://localhost:8000/v1'
        )
        self.poll_interval = 2  # seconds
        self.max_wait_time = 600  # 10 minutes
    
    def extract_lyrics(
        self,
        audio_url: Optional[str] = None,
        local_file_path: Optional[str] = None,
        whisper_language_override: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract lyrics from audio source.
        
        Returns:
            Tuple of (lyrics, source, error)
        """
        try:
            # Submit job
            if local_file_path:
                job_id = self._submit_job_from_file(
                    local_file_path,
                    whisper_language_override
                )
            elif audio_url:
                # Download first, then submit
                temp_file = self._download_file(audio_url)
                job_id = self._submit_job_from_file(
                    temp_file,
                    whisper_language_override
                )
            else:
                return None, None, 'No audio source provided'
            
            # Poll for result
            result = self._wait_for_result(job_id)
            
            if result['status'] == 'done':
                lyrics = result['result']['lyrics']
                return lyrics, 'microservice', None
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                return None, None, error_msg
        
        except Exception as e:
            current_app.logger.error(f"Lyrics extraction failed: {e}")
            return None, None, str(e)
    
    def _submit_job_from_file(self, file_path: str, language: Optional[str]) -> str:
        """Submit lyrics extraction job."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'language_hint': language or 'auto',
                'timestamps': 'none'
            }
            
            response = requests.post(
                f"{self.api_base_url}/lyrics",
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()['job_id']
    
    def _wait_for_result(self, job_id: str) -> dict:
        """Poll for job completion."""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.max_wait_time:
                raise TimeoutError("Lyrics extraction timed out")
            
            response = requests.get(
                f"{self.api_base_url}/lyrics/{job_id}",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result['status'] in ['done', 'error', 'not_found']:
                return result
            
            time.sleep(self.poll_interval)
    
    def _download_file(self, url: str) -> str:
        """Download audio file to temp location."""
        import tempfile
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        temp_file.close()
        
        return temp_file.name
```

### Option B: Async Job Storage

For better UX, store job IDs in your database and poll in background:

```python
# Add to your models.py
class LyricsExtractionJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='queued')
    lyrics = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# In your route
@app.route('/extract-lyrics', methods=['POST'])
def extract_lyrics():
    file = request.files['audio']
    
    # Submit to microservice
    response = requests.post(
        'http://localhost:8000/v1/lyrics',
        files={'file': file},
        data={'language_hint': 'auto'}
    )
    job_id = response.json()['job_id']
    
    # Store in DB
    job = LyricsExtractionJob(job_id=job_id, user_id=current_user.id)
    db.session.add(job)
    db.session.commit()
    
    return jsonify({'job_id': job_id, 'status': 'queued'})

# Background task to poll results
def poll_lyrics_jobs():
    pending_jobs = LyricsExtractionJob.query.filter(
        LyricsExtractionJob.status.in_(['queued', 'running'])
    ).all()
    
    for job in pending_jobs:
        response = requests.get(f'http://localhost:8000/v1/lyrics/{job.job_id}')
        result = response.json()
        
        if result['status'] == 'done':
            job.status = 'done'
            job.lyrics = result['result']['lyrics']
        elif result['status'] == 'error':
            job.status = 'error'
            job.error = result['error']['message']
        else:
            job.status = result['status']
        
        db.session.commit()
```

## Configuration

Add to your Flask config:

```python
# config.py or app/config.py

# Lyrics microservice URL
LYRICS_SERVICE_URL = os.getenv('LYRICS_SERVICE_URL', 'http://localhost:8000/v1')

# If using internal Docker network
# LYRICS_SERVICE_URL = os.getenv('LYRICS_SERVICE_URL', 'http://lyrics-api:8000/v1')
```

## Environment Variables

Add to your `.env` file:

```env
LYRICS_SERVICE_URL=http://localhost:8000/v1
```

For production (Docker internal network):

```env
LYRICS_SERVICE_URL=http://lyrics-api:8000/v1
```

## Testing Integration

Test that your Flask app can call the service:

```python
# test_lyrics_integration.py

import requests

def test_lyrics_service():
    # Health check
    response = requests.get('http://localhost:8000/healthz')
    assert response.status_code == 200
    
    # Submit job
    with open('test_audio.mp3', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/v1/lyrics',
            files={'file': f},
            data={'language_hint': 'en'}
        )
    assert response.status_code == 202
    job_id = response.json()['job_id']
    
    # Poll for result
    import time
    for _ in range(60):  # 2 minutes max
        response = requests.get(f'http://localhost:8000/v1/lyrics/{job_id}')
        result = response.json()
        
        if result['status'] == 'done':
            print("Lyrics:", result['result']['lyrics'])
            break
        
        time.sleep(2)
```

## Monitoring

Add health check to your monitoring:

```python
# In your Flask app
@app.route('/health')
def health():
    checks = {}
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        checks['database'] = 'ok'
    except:
        checks['database'] = 'error'
    
    # Check lyrics service
    try:
        response = requests.get('http://lyrics-api:8000/healthz', timeout=5)
        checks['lyrics_service'] = 'ok' if response.status_code == 200 else 'error'
    except:
        checks['lyrics_service'] = 'error'
    
    return jsonify(checks)
```

## Troubleshooting

**Issue: "Connection refused to localhost:8000"**

- Ensure lyrics service is running: `docker compose -f docker-compose.lyrics.yml ps`
- Check if port 8000 is accessible: `curl http://localhost:8000/healthz`

**Issue: "Service unreachable from Docker container"**

- Use Docker service name instead of localhost: `http://lyrics-api:8000`
- Ensure services are on same Docker network

**Issue: "Jobs taking too long"**

- Check worker logs: `docker logs lyrics-worker`
- Consider using GPU: Update to docker-compose.lyrics-gpu.yml
- Scale workers: `docker compose up -d --scale lyrics-worker=3`

## Production Considerations

1. **Separate Redis**: Use separate Redis instance for lyrics queue
2. **Multiple Workers**: Scale workers based on load
3. **Timeouts**: Set appropriate timeouts in your Flask app
4. **Retries**: Implement retry logic for failed microservice calls
5. **Circuit Breaker**: Use circuit breaker pattern to handle service outages
6. **Monitoring**: Monitor queue depth and processing times
7. **Security**: Use internal Docker network, don't expose lyrics API publicly

## Migration Path

### Phase 1: Parallel Running
- Deploy lyrics microservice alongside existing service
- Add feature flag to switch between implementations
- Test with subset of users

### Phase 2: Full Migration
- Switch all traffic to new microservice
- Keep old service as fallback
- Monitor for issues

### Phase 3: Cleanup
- Remove old lyrics extraction code
- Update documentation
- Archive old service

## Example Feature Flag

```python
# In your Flask app
LYRICS_USE_MICROSERVICE = os.getenv('LYRICS_USE_MICROSERVICE', 'false').lower() == 'true'

def get_lyrics_service():
    if LYRICS_USE_MICROSERVICE:
        return LyricsExtractionServiceMicroservice()
    else:
        return LyricsExtractionServiceOld()
```

This allows gradual rollout and easy rollback if issues arise.
