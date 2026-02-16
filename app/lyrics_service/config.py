"""
Configuration for lyrics extraction service.
Loads settings from environment variables.
"""
import os
from typing import Literal

# Service settings
SERVICE_NAME = os.getenv("LYRICS_SERVICE_NAME", "lyrics-extraction-service")
SERVICE_VERSION = os.getenv("LYRICS_SERVICE_VERSION", "1.0.0")
API_PREFIX = os.getenv("LYRICS_API_PREFIX", "/v1")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# RQ Queue settings
QUEUE_NAME = os.getenv("LYRICS_QUEUE_NAME", "lyrics_extraction")
QUEUE_TIMEOUT = int(os.getenv("LYRICS_QUEUE_TIMEOUT", "900"))  # 15 minutes
RESULT_TTL = int(os.getenv("LYRICS_RESULT_TTL", "3600"))  # 1 hour

# Upload settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("LYRICS_MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"}

# Model settings
WHISPER_MODEL_SIZE = os.getenv("LYRICS_WHISPER_MODEL", "large-v3")
DEMUCS_MODEL = os.getenv("LYRICS_DEMUCS_MODEL", "htdemucs")

# Device settings
DEVICE = os.getenv("LYRICS_DEVICE", "cpu")  # 'cpu' or 'cuda'
COMPUTE_TYPE = os.getenv("LYRICS_COMPUTE_TYPE", "int8" if DEVICE == "cpu" else "float16")

# Processing settings
ENABLE_VOCAL_SEPARATION = os.getenv("LYRICS_ENABLE_SEPARATION", "true").lower() == "true"
PREPROCESS_AUDIO = os.getenv("LYRICS_PREPROCESS_AUDIO", "true").lower() == "true"
VAD_FILTER = os.getenv("LYRICS_VAD_FILTER", "true").lower() == "true"
BEAM_SIZE = int(os.getenv("LYRICS_BEAM_SIZE", "5"))
TEMPERATURE = float(os.getenv("LYRICS_TEMPERATURE", "0.0"))

# Word-level timestamps and formatting
ENABLE_WORD_TIMESTAMPS = os.getenv("LYRICS_ENABLE_WORD_TIMESTAMPS", "true").lower() == "true"
MAX_CHARS_PER_LINE = int(os.getenv("LYRICS_MAX_CHARS_PER_LINE", "60"))
# Adjusted for singing: shorter gaps are needed for sung phrases
LINE_GAP_THRESHOLD = float(os.getenv("LYRICS_LINE_GAP_THRESHOLD", "0.3"))
STANZA_GAP_THRESHOLD = float(os.getenv("LYRICS_STANZA_GAP_THRESHOLD", "1.0"))

# Uppercase-based line breaking (fallback when timing gaps don't produce breaks)
ENABLE_UPPERCASE_BREAKS = os.getenv("LYRICS_ENABLE_UPPERCASE_BREAKS", "true").lower() == "true"
MIN_CHARS_BEFORE_UPPER_BREAK = int(os.getenv("LYRICS_MIN_CHARS_BEFORE_UPPER_BREAK", "18"))
MIN_WORDS_BEFORE_UPPER_BREAK = int(os.getenv("LYRICS_MIN_WORDS_BEFORE_UPPER_BREAK", "4"))

# Concurrency
MAX_CONCURRENT_JOBS = int(os.getenv("LYRICS_MAX_CONCURRENT_JOBS", "1"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Temporary files
TEMP_DIR = os.getenv("LYRICS_TEMP_DIR", "/tmp/lyrics_extraction")


def get_redis_url() -> str:
    """Get Redis connection URL."""
    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
