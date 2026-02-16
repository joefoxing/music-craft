# Word-Based Line-by-Line Lyrics Formatting - Implementation Report

**Date:** February 14, 2026  
**Status:** ✅ IMPLEMENTED AND TESTED

## Summary

Upgraded faster-whisper Vietnamese lyrics extraction to produce line-by-line formatted lyrics using word-level timestamps with intelligent line/stanza breaks based on timing gaps.

## Changes Implemented

### 1. New Formatter: `format_lyrics_from_words()`

**File:** [`app/lyrics_service/pipeline/postprocess.py`](app/lyrics_service/pipeline/postprocess.py)

**New Function:**
```python
def format_lyrics_from_words(
    segments: List[Dict],
    max_chars_per_line: int = 60,
    line_gap_threshold: float = 0.8,
    stanza_gap_threshold: float = 2.5
) -> tuple[str, List[Dict]]:
```

**Features:**
- ✅ **Word-level timing analysis**: Uses gaps between individual words instead of segments
- ✅ **Line breaks at `line_gap_threshold`**: Default 0.8 seconds
- ✅ **Stanza breaks at `stanza_gap_threshold`**: Default 2.5 seconds (adds blank line)
- ✅ **Smart line wrapping**: Respects `max_chars_per_line` (soft limit of 60 chars)
- ✅ **preserves**: Vietnamese diacritics, word order, token boundaries
- ✅ **Returns**: Both formatted lyrics and word timestamps list

**Algorithm:**
1. Extract all words with timestamps from segments
2. Iterate through words, calculate gaps between consecutive words
3. Apply gap-based decisions:
   - Gap ≥ stanza_gap_threshold → flush line + blank line + new line
   - Gap ≥ line_gap_threshold → flush line + new line
   - Line length > max_chars → wrap to new line
   - Otherwise → append word to current line
4. Clean noise patterns while preserving blank lines (stanza separators)
5. Remove excessive line breaks (3+ → 2)

### 2. Enhanced `format_lyrics_with_timestamps()`

**File:** [`app/lyrics_service/pipeline/postprocess.py`](app/lyrics_service/pipeline/postprocess.py)

**Enhancement:**
```python
# Check if we have word-level data - if so, use word-based formatting
has_words = any('words' in seg and seg['words'] for seg in segments)
if has_words:
    formatted, words = format_lyrics_from_words(segments)
    return formatted, words if include_word_timestamps else None

# Fallback: segment-level formatting (original behavior)
```

**Behavior:**
- Automatically detects word-level timestamps in segments
- Uses new word-based formatter when available
- Falls back to segment-based formatting for backward compatibility

### 3. Configuration Updates

**File:** [`app/lyrics_service/config.py`](app/lyrics_service/config.py)

**New Settings:**
```python
# Word-level timestamps and formatting
ENABLE_WORD_TIMESTAMPS = os.getenv("LYRICS_ENABLE_WORD_TIMESTAMPS", "true").lower() == "true"
MAX_CHARS_PER_LINE = int(os.getenv("LYRICS_MAX_CHARS_PER_LINE", "60"))
LINE_GAP_THRESHOLD = float(os.getenv("LYRICS_LINE_GAP_THRESHOLD", "0.8"))
STANZA_GAP_THRESHOLD = float(os.getenv("LYRICS_STANZA_GAP_THRESHOLD", "2.5"))
```

**Defaults:**
- `ENABLE_WORD_TIMESTAMPS=true` - Word timestamps enabled by default
- `MAX_CHARS_PER_LINE=60` - Soft line length limit
- `LINE_GAP_THRESHOLD=0.8` - 0.8 seconds for new line
- `STANZA_GAP_THRESHOLD=2.5` - 2.5 seconds for stanza break

### 4. Worker Pipeline Updates

**File:** [`app/lyrics_service/worker.py`](app/lyrics_service/worker.py)

**Changes:**

**Enable word timestamps by default:**
```python
# Enable word timestamps by default for better formatting (unless explicitly disabled)
word_timestamps = config.ENABLE_WORD_TIMESTAMPS if include_timestamps != "none" else (include_timestamps == "word")
```

**Ensure Vietnamese configuration:**
```python
# Ensure Vietnamese settings for better accuracy
transcribe_language = language_hint if language_hint != "auto" else None

transcription_result = transcriber.transcribe(
    audio_path=transcription_input,
    language=transcribe_language,  # Pass 'vi' for Vietnamese
    word_timestamps=word_timestamps,
    vad_filter=config.VAD_FILTER,
    beam_size=config.BEAM_SIZE,
    temperature=config.TEMPERATURE  # 0.0 = deterministic
)
```

**Return both raw and formatted:**
```python
result["result"] = {
    "lyrics": processed["lyrics"],        # Formatted line-by-line
    "raw_transcript": transcription_result.get("text", ""),  # Raw joined text
}
```

### 5. Comprehensive Unit Tests

**File:** [`tests/test_word_based_lyrics_formatting.py`](tests/test_word_based_lyrics_formatting.py) (NEW)

**Test Coverage:**
1. ✅ `test_line_break_at_gap_threshold()` - Verifies line breaks at 0.8s gap
2. ✅ `test_stanza_break_at_gap_threshold()` - Verifies blank lines at 2.5s gap
3. ✅ `test_line_wrapping_at_max_chars()` - Verifies wrapping at character limit
4. ✅ `test_vietnamese_diacritics_preserved()` - Verifies ô, ê, đ, á, ắ, etc. preserved
5. ✅ `test_token_order_preserved()` - Verifies word order never changes
6. ✅ `test_empty_segments()` - Handles empty input gracefully
7. ✅ `test_segments_without_words()` - Handles segments without word timestamps
8. ✅ `test_mixed_gaps_complex_formatting()` - Complex real-world scenario
9. ✅ `test_configurable_thresholds()` - Verifies threshold parameters work

**Test Results:**
```
=== Testing Word-Based Lyrics Formatting ===

✓ Line break at gap threshold
✓ Stanza break at gap threshold
✓ Line wrapping at max chars (3 lines)
✓ Vietnamese diacritics preserved
✓ Token order preserved
✓ Empty segments handled correctly
✓ Segments without words handled correctly
✓ Complex mixed gaps formatting
✓ Configurable thresholds work correctly

✅ All word-based formatting tests passed!
```

## Whisper Configuration Verified

### faster-whisper Parameters (Confirmed in Code)

**File:** [`app/lyrics_service/pipeline/transcribe.py`](app/lyrics_service/pipeline/transcribe.py)

```python
transcribe_kwargs = {
    "word_timestamps": word_timestamps,      # ✅ Enabled
    "vad_filter": vad_filter,               # ✅ True (filters silence)
    "beam_size": beam_size,                 # ✅ 5 (default)
    "temperature": temperature,             # ✅ 0.0 (deterministic)
    "condition_on_previous_text": False,    # ✅ Better for singing
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "no_speech_threshold": 0.6,
}

# Set language if not auto
if language and language != "auto":
    transcribe_kwargs["language"] = language  # ✅ Supports 'vi'
```

**For Vietnamese:**
- Set `language_hint='vi'` in API request, OR
- Set `LYRICS_WHISPER_LANGUAGE=vi` in `.env`
- Task is always `transcribe` (not `translate`)
- UTF-8 encoding preserved end-to-end

## Example Output

### Before (Segment-based):
```
Tôi yêu em nhiều lắm Con đường dài về nhà Ánh mắt người xa xôi
```

### After (Word-based with timing):
```
Tôi yêu em nhiều lắm
Con đường dài về nhà

Ánh mắt người xa xôi
```

**Improvements:**
- ✅ Line breaks at natural pauses (0.8s gap)
- ✅ Stanza breaks at longer pauses (2.5s gap with blank line)
- ✅ More readable, song-like structure
- ✅ Better matches actual singing rhythm

## API Response Structure

### New Response Format:
```json
{
  "status": "done",
  "result": {
    "lyrics": "Tôi yêu em nhiều lắm\nCon đường dài về nhà\n\nÁnh mắt người xa xôi",
    "raw_transcript": "Tôi yêu em nhiều lắm Con đường dài về nhà Ánh mắt người xa xôi",
    "words": [
      {"word": "Tôi", "start": 0.0, "end": 0.5},
      {"word": "yêu", "start": 0.6, "end": 1.0},
      ...
    ]
  },
  "meta": {
    "duration_sec": 10.5,
    "language_detected": "vi",
    "model": {
      "separator": null,
      "asr": "faster-whisper large-v3"
    }
  }
}
```

**Fields:**
- `lyrics` - Formatted line-by-line (NEW: word-based)
- `raw_transcript` - Raw joined text (NEW)
- `words` - Word timestamps array (if requested)
- `language_detected` - Auto-detected language

## Configuration Guide

### Environment Variables

Add to [`.env`](.env) or set via environment:

```bash
# Enable word timestamps (recommended for better formatting)
LYRICS_ENABLE_WORD_TIMESTAMPS=true

# Line/stanza formatting thresholds (seconds)
LYRICS_LINE_GAP_THRESHOLD=0.8      # New line after 0.8s pause
LYRICS_STANZA_GAP_THRESHOLD=2.5    # Blank line after 2.5s pause

# Line length limit (soft, can go over by one word)
LYRICS_MAX_CHARS_PER_LINE=60

# Vietnamese language (optional, can also pass per-request)
LYRICS_WHISPER_LANGUAGE=vi

# Whisper quality settings
LYRICS_WHISPER_MODEL=large-v3      # large-v3 best for Vietnamese
LYRICS_TEMPERATURE=0.0             # Deterministic
LYRICS_BEAM_SIZE=5                 # Balance speed/quality
LYRICS_VAD_FILTER=true             # Filter silence
```

### Tuning Recommendations

**For Vietnamese Songs:**
- `LINE_GAP_THRESHOLD=0.8` - Good for normal singing pace
- `STANZA_GAP_THRESHOLD=2.5` - Catches chorus/verse breaks
- `MAX_CHARS_PER_LINE=60` - Good for display on most screens

**For Rap/Fast Speech:**
- `LINE_GAP_THRESHOLD=0.5` - Shorter gaps
- `MAX_CHARS_PER_LINE=80` - Longer lines

**For Ballads/Slow Songs:**
- `LINE_GAP_THRESHOLD=1.2` - Longer gaps
- `STANZA_GAP_THRESHOLD=3.5` - More dramatic breaks

## Testing Performed

### Unit Tests: ✅ PASSED
- Word-based formatting: 9/9 tests passed
- Vietnamese diacritics: 5/5 tests passed
- **Total: 14/14 tests passing**

### Test Execution:
```powershell
# Word-based formatter tests
python tests\test_word_based_lyrics_formatting.py
✅ All word-based formatting tests passed!

# Vietnamese diacritics tests
python tests\test_vietnamese_lyrics.py
✅ All tests passed! Vietnamese diacritics are preserved.
```

### Manual Testing Checklist:
- ✅ Line breaks occur at timing gaps
- ✅ Stanza breaks create blank lines
- ✅ Lines wrap at character limit
- ✅ Vietnamese diacritics preserved
- ✅ Word order never changes
- ✅ Empty/missing data handled gracefully
- ✅ Raw transcript included in response
- ✅ Configuration parameters work
- ✅ Backward compatible (segment-based fallback)

## Files Modified

1. **[app/lyrics_service/pipeline/postprocess.py](app/lyrics_service/pipeline/postprocess.py)**
   - Added `format_lyrics_from_words()` function
   - Enhanced `format_lyrics_with_timestamps()` with auto-detection
   - Modified cleaning to preserve blank lines

2. **[app/lyrics_service/config.py](app/lyrics_service/config.py)**
   - Added 4 new configuration variables

3. **[app/lyrics_service/worker.py](app/lyrics_service/worker.py)**
   - Updated word_timestamps logic
   - Added raw_transcript to result
   - Added logging for word count

4. **[tests/test_word_based_lyrics_formatting.py](tests/test_word_based_lyrics_formatting.py)** (NEW)
   - 9 comprehensive unit tests
   - Vietnamese and English test cases
   - Edge cases covered

## Backward Compatibility

✅ **Fully backward compatible**

- If segments don't have word-level data, falls back to segment-based formatting
- Old API requests still work (word timestamps optional)
- Configuration has sensible defaults
- No breaking changes to existing functionality

## Performance Impact

**Minimal:**
- Word-based formatting is O(n) where n = number of words
- Typically 50-200 words per song = negligible overhead
- Most time spent in Whisper transcription (unchanged)

**Trade-off:**
- **+** Better formatting quality
- **+** More natural line breaks
- **-** Slightly larger response (includes raw_transcript)
- **=** No change in transcription speed

## Known Limitations

1. **Word timestamps require faster-whisper** - Legacy openai-whisper may not support word timestamps
2. **Soft character limit** - Can exceed max_chars_per_line by one word to avoid splitting
3. **Gap-based only** - No semantic analysis (future enhancement)
4. **Single language** - Doesn't handle code-switching within words

## Future Enhancements

1. **Semantic line breaks** - Use LLM to identify sentence/phrase boundaries
2. **Punctuation restoration** - Add commas, periods based on prosody
3. **Rhyme detection** - Group lines that rhyme together
4. **Confidence filtering** - Hide/italicize low-confidence words
5. **Multi-language support** - Better handling of mixed-language songs

## Usage Examples

### API Request (Vietnamese):
```bash
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@vietnamese_song.mp3" \
  -F "language_hint=vi" \
  -F "timestamps=word"
```

### API Request (Auto-detect):
```bash
curl -X POST http://localhost:8000/v1/lyrics \
  -F "file=@song.mp3" \
  -F "language_hint=auto"
```

### Check Word Timestamps:
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/lyrics",
    files={"file": open("song.mp3", "rb")},
    data={"language_hint": "vi", "timestamps": "word"}
)

result = response.json()["result"]
print("Formatted lyrics:")
print(result["lyrics"])
print("\nRaw transcript:")
print(result["raw_transcript"])
print(f"\nWord count: {len(result.get('words', []))}")
```

## Conclusion

✅ **Word-based line-by-line lyrics formatting successfully implemented**  
✅ **Vietnamese diacritics preserved throughout**  
✅ **Comprehensive test coverage (14/14 tests passing)**  
✅ **Configurable timing thresholds**  
✅ **Backward compatible**  
✅ **Production-ready**

The upgrade provides significant improvement in lyrics readability while maintaining all existing functionality and Vietnamese language support.

---

**Implementation completed:** February 14, 2026  
**Tests passing:** 14/14 (100%)  
**Ready for deployment:** ✅ YES
