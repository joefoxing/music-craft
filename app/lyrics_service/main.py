"""
FastAPI application for lyrics extraction service.
Provides async job-based API for extracting lyrics from audio.
"""
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Literal

import redis
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rq import Queue
from rq.job import Job

from app.lyrics_service import config
from app.lyrics_service.worker import process_lyrics_extraction

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Lyrics Extraction Service",
    description="Extract lyrics from audio using vocal separation and ASR",
    version=config.SERVICE_VERSION
)

# Redis connection
redis_conn = redis.from_url(config.get_redis_url())
queue = Queue(config.QUEUE_NAME, connection=redis_conn)

# Ensure temp directory exists
os.makedirs(config.TEMP_DIR, exist_ok=True)


# Pydantic models
class JobResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: Literal["queued", "running", "done", "error", "not_found"]
    result: Optional[dict] = None
    meta: Optional[dict] = None
    error: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    redis_connected: bool
    queue_size: int


# API Routes

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        redis_conn.ping()
        redis_connected = True
        queue_size = len(queue)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        redis_connected = False
        queue_size = -1
    
    return HealthResponse(
        status="healthy" if redis_connected else "unhealthy",
        service=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        redis_connected=redis_connected,
        queue_size=queue_size
    )


@app.post(f"{config.API_PREFIX}/lyrics", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_lyrics_extraction_job(
    file: UploadFile = File(..., description="Audio file to extract lyrics from"),
    language_hint: Optional[str] = Form("auto", description="Language hint: 'en', 'vi', or 'auto'"),
    timestamps: Optional[str] = Form("none", description="Timestamp mode: 'none' or 'word'"),
    diarize: Optional[bool] = Form(False, description="Speaker diarization (currently unsupported)")
):
    """
    Create a new lyrics extraction job.
    
    The job is queued and processed asynchronously.
    Use the returned job_id to check status with GET /v1/lyrics/{job_id}.
    """
    # Validate language hint
    if language_hint not in ["en", "vi", "auto"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="language_hint must be 'en', 'vi', or 'auto'"
        )
    
    # Validate timestamps
    if timestamps not in ["none", "word"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timestamps must be 'none' or 'word'"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file temporarily
    temp_file_path = os.path.join(config.TEMP_DIR, f"{job_id}{file_ext}")
    
    try:
        # Check file size while uploading
        total_size = 0
        with open(temp_file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                total_size += len(chunk)
                
                if total_size > config.MAX_UPLOAD_SIZE_BYTES:
                    # Cleanup and reject
                    f.close()
                    os.remove(temp_file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds {config.MAX_UPLOAD_SIZE_MB}MB limit"
                    )
                
                f.write(chunk)
        
        logger.info(f"[{job_id}] Uploaded file saved: {temp_file_path} ({total_size} bytes)")
        
        # Enqueue job
        job = queue.enqueue(
            process_lyrics_extraction,
            job_id,
            temp_file_path,
            language_hint,
            timestamps,
            job_timeout=config.QUEUE_TIMEOUT,
            result_ttl=config.RESULT_TTL,
            job_id=job_id
        )
        
        logger.info(f"[{job_id}] Job enqueued: {job.id}")
        
        return JobResponse(
            job_id=job_id,
            status="queued",
            meta={
                "queue_position": len(queue),
                "language_hint": language_hint,
                "timestamps": timestamps
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        logger.error(f"[{job_id}] Failed to create job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@app.get(f"{config.API_PREFIX}/lyrics/{{job_id}}", response_model=JobResponse)
async def get_lyrics_job_status(job_id: str):
    """
    Get the status and result of a lyrics extraction job.
    
    Status values:
    - queued: Job is waiting to be processed
    - running: Job is currently being processed
    - done: Job completed successfully (result available)
    - error: Job failed (error details available)
    - not_found: Job ID not found or expired
    """
    try:
        # Fetch job from RQ
        job = Job.fetch(job_id, connection=redis_conn)
        
        # Map RQ status to our status
        rq_status = job.get_status()
        
        if rq_status == "queued":
            return JobResponse(
                job_id=job_id,
                status="queued",
                meta={"queue_position": queue.job_ids.index(job_id) + 1 if job_id in queue.job_ids else None}
            )
        
        elif rq_status == "started":
            return JobResponse(
                job_id=job_id,
                status="running"
            )
        
        elif rq_status == "finished":
            result = job.result
            
            if result and isinstance(result, dict):
                # Return the full result from worker
                return JobResponse(
                    job_id=job_id,
                    status=result.get("status", "done"),
                    result=result.get("result"),
                    meta=result.get("meta"),
                    error=result.get("error")
                )
            else:
                # Unexpected result format
                return JobResponse(
                    job_id=job_id,
                    status="error",
                    error={
                        "code": "invalid_result",
                        "message": "Job completed but result format is invalid"
                    }
                )
        
        elif rq_status == "failed":
            exc_info = job.exc_info
            return JobResponse(
                job_id=job_id,
                status="error",
                error={
                    "code": "job_failed",
                    "message": str(exc_info) if exc_info else "Job failed with unknown error"
                }
            )
        
        else:
            # Unknown status
            return JobResponse(
                job_id=job_id,
                status="error",
                error={
                    "code": "unknown_status",
                    "message": f"Unknown job status: {rq_status}"
                }
            )
    
    except Exception as e:
        logger.warning(f"Job {job_id} not found or error: {e}")
        return JobResponse(
            job_id=job_id,
            status="not_found",
            error={
                "code": "not_found",
                "message": "Job not found or expired"
            }
        )


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "api_docs": "/docs",
        "health": "/healthz"
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
