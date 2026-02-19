# Tier 2 LRCLIB Implementation Summary

**Date**: February 17, 2026  
**Status**: ✅ COMPLETE AND DEPLOYED

## What Was Implemented

Automatic lyrics extraction using LRCLIB API (Tier 2) integrated into the cover-generator workflow.

## Key Components

### 1. Backend API Endpoints (Python/Flask)
**File**: `/app/routes/lyrics_search_api.py`

- `GET /api/lyrics-search/health` - Health check
- `POST /api/lyrics-search/extract-metadata` - Extract artist/title from audio file using mutagen
- `POST /api/lyrics-search/search` - Search LRCLIB API for lyrics (requires auth)
- `POST /api/lyrics-search/apply` - Apply selected lyrics to audio (requires auth)

### 2. Frontend JavaScript
**File**: `/app/static/js/components/lyricsSearchHandler.js`
- Added `autoExtractAndSearch(audioFile)` method
- Automatically extracts metadata after file upload
- Auto-searches LRCLIB if title found
- Opens results modal for user selection

**File**: `/app/static/js/utils/fileHandler.js`
- Added hook after successful upload to trigger Tier 2 extraction
- Calls `window.lyricsSearchHandler.autoExtractAndSearch(file)`

### 3. Configuration
**File**: `/app/config.py`
- Added `LYRICS_USE_LRCLIB` environment variable (defaults to true)

**File**: `/app/__init__.py`
- Registered `lyrics_search_bp` blueprint
- Added CSRF exemption for API endpoints

## Automatic Workflow

1. User uploads audio file → cover-generator page
2. File uploads to `/upload` endpoint
3. **[Tier 2]** Auto-extract metadata (artist, title) from ID3 tags
4. **[Tier 2]** Auto-search LRCLIB API if title found
5. **[Tier 2]** Display results modal if lyrics found
6. User selects & applies lyrics → populates prompt field
7. *Fallback*: If no metadata or no results → proceeds to Tier 3 (AI transcription)

## Deployment Details

### Docker Container
- Container: `app_staging-api-1`
- Port: 8001 (internal 8000)
- Image: ghcr.io/joefoxing/music-craft/api:sha-e9e74207fb7d

### File Locations
- Source: `/home/deploy/app/`
- Production: `/home/deploy/music-craft/`
- Container: Files copied via `docker cp` into running container

### Critical Discovery
The Docker container runs a pre-built image. Files needed to be copied directly into the container using `docker cp` since:
- Image is pulled from ghcr.io registry
- Only 2 files have volume mounts (`config.py`, `lyrics_extraction_service.py`)
- Routes file was baked into image from old build

### Deployment Steps
```bash
# Copy routes file with all endpoints
docker cp /home/deploy/app/app/routes/lyrics_search_api.py \
  app_staging-api-1:/app/app/routes/lyrics_search_api.py

# Copy JS files
docker cp /home/deploy/app/app/static/js/components/lyricsSearchHandler.js \
  app_staging-api-1:/app/app/static/js/components/lyricsSearchHandler.js

docker cp /home/deploy/app/app/static/js/utils/fileHandler.js \
  app_staging-api-1:/app/app/static/js/utils/fileHandler.js

# Copy HTML template
docker cp /home/deploy/app/app/templates/lyrics-extraction.html \
  app_staging-api-1:/app/app/templates/lyrics-extraction.html

# Restart container to reload Python modules
docker restart app_staging-api-1
```

## Testing

### Health Check
```bash
curl http://127.0.0.1:8001/api/lyrics-search/health
# Response: {"status":"ok","message":"lyrics-search endpoint is working"}
```

### Metadata Extraction
```bash
curl -X POST http://127.0.0.1:8001/api/lyrics-search/extract-metadata \
  -F "file=@/path/to/audio.mp3"
# Response: {"artist":"Artist Name","title":"Song Title"}
```

### Live Testing
1. Navigate to: `https://staging.joefoxing.com/cover-generator`
2. Upload audio file with ID3 tags
3. Watch browser console for `[Tier 2]` logs
4. Verify modal opens automatically with results
5. Click "Apply" to populate lyrics into prompt field

## Console Debugging
All Tier 2 operations log with `[Tier 2]` prefix:
- `[Tier 2] Auto-extracting metadata from: filename.mp3`
- `[Tier 2] Metadata extracted: {artist, title}`
- `[Tier 2] Auto-searching LRCLIB for: [title] [artist]`
- `[Tier 2] Found N lyrics result(s)`

## Key Features

✅ Non-blocking - errors don't interrupt normal flow  
✅ Silent fallback to Tier 3 if metadata/lyrics not found  
✅ Automatic - no user action required  
✅ Uses free LRCLIB API (no authentication needed)  
✅ Reads ID3, Vorbis, MP4/M4A metadata formats  
✅ Strips timestamps from synced lyrics  
✅ Clickable results with preview  

## Files Modified

### Python
- `/app/routes/lyrics_search_api.py` (NEW - 377 lines)
- `/app/__init__.py` (added blueprint registration)
- `/app/config.py` (added LYRICS_USE_LRCLIB config)

### JavaScript
- `/app/static/js/components/lyricsSearchHandler.js` (added autoExtractAndSearch)
- `/app/static/js/utils/fileHandler.js` (added Tier 2 trigger)

### Templates
- `/app/templates/lyrics-extraction.html` (standalone page, not used in main flow)
- Cover-generator page already had lyrics modal (no changes needed)

## Dependencies

### Python Packages (already installed)
- mutagen - Audio metadata extraction
- requests - LRCLIB API calls
- Flask - Web framework

### External API
- LRCLIB: https://lrclib.net/api/search
- Free, no authentication required
- Returns JSON with lyrics results

## Production Checklist

✅ All endpoints functional  
✅ Metadata extraction working  
✅ LRCLIB search working  
✅ Auto-trigger after upload working  
✅ Results modal working  
✅ Apply lyrics working  
✅ Files synced to all locations  
✅ Container updated  
✅ No restart required for static files  

## Future Improvements

1. Add persistent caching of LRCLIB results to database
2. Add user preference to enable/disable auto-search
3. Add confidence score/ranking for results
4. Add fallback to other lyrics APIs if LRCLIB fails
5. Add ability to edit/correct metadata before search
6. Store applied lyrics to audio_library table

## Notes

- Tier 1 = Embedded lyrics (not implemented yet)
- Tier 2 = LRCLIB automatic search (COMPLETE)
- Tier 3 = AI transcription (existing functionality)

The system tries each tier in order: embedded → LRCLIB → AI transcription.
