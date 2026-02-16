# Vietnamese Lyrics Fix - Executive Summary

## ✅ FIXED: Vietnamese Diacritics Now Preserved

### Root Cause
Two regex patterns in `lyrics_extraction_service.py` were ASCII-only and stripped Vietnamese diacritics:
1. **`_normalize_for_repeat_check()`** - Used `[^a-zA-Z0-9' ]` (removed all non-ASCII)
2. **`_tokenize_words()`** - Used `[a-zA-Z']+` (only matched English letters)

### Solution
Changed to Unicode-aware patterns:
```python
# BEFORE: ASCII-only
re.findall(r"[a-zA-Z']+", text.lower())              # Strips Vietnamese
re.sub(r"[^a-zA-Z0-9' ]", '', text.lower())          # Strips Vietnamese

# AFTER: Unicode-aware
re.findall(r"[\w']+", text.lower(), re.UNICODE)      # Keeps Vietnamese ✓
re.sub(r"[^\w\s']", '', text.lower(), flags=re.UNICODE)  # Keeps Vietnamese ✓
```

### Files Modified
1. `app/services/lyrics_extraction_service.py` - Fixed 2 functions, added debug logs
2. `app/lyrics_service/pipeline/transcribe.py` - Added debug logs
3. `app/lyrics_service/pipeline/postprocess.py` - Added debug logs
4. `tests/test_vietnamese_lyrics.py` - NEW: Comprehensive test suite

### Test Results
```
✅ All tests passed! Vietnamese diacritics are preserved.
```

### Usage
For Vietnamese lyrics, set language in `.env` or pass per request:
```env
LYRICS_WHISPER_LANGUAGE=vi
```
Or via API:
```bash
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@song.mp3" \
  -F "language_hint=vi"
```

### Debug Output
Logs now show text at each stage:
```
[DEBUG] Raw Whisper output: len=245, repr='Tôi yêu em nhiều lắm...'
[DEBUG] After postprocess: len=240, repr='Tôi yêu em nhiều lắm...'
[DEBUG] Final lyrics: len=240, repr='Tôi yêu em nhiều lắm...'
```

### Deliverables
- ✅ Code fixes applied and tested
- ✅ Debug logging added throughout pipeline
- ✅ Unit tests with 100% pass rate
- ✅ Comprehensive documentation: `VIETNAMESE_LYRICS_FIX_REPORT.md`
- ✅ Unified diff patch: `vietnamese_lyrics_fix.patch`
