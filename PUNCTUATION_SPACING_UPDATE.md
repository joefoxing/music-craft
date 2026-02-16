# Punctuation Spacing Update - Vietnamese Lyrics Formatting

**Date:** February 14, 2026  
**Status:** ✅ COMPLETED

## Summary

Added punctuation spacing handling to the existing word-based lyrics formatter. Punctuation marks (`,`, `.`, `!`, `?`, `;`, `:`) now correctly attach to the preceding word without spaces.

## Changes Made

### File: `app/lyrics_service/pipeline/postprocess.py`

**Added punctuation handling functions:**

```python
PUNCT_NO_SPACE_BEFORE = {',', '.', '!', '?', ';', ':'}

def append_word_to_line(line_words: List[str], word: str) -> List[str]:
    """Append word, handling punctuation spacing."""
    word = word.strip()
    if not word:
        return line_words
    
    # If word is just punctuation, attach to previous word
    if word in PUNCT_NO_SPACE_BEFORE and line_words:
        line_words[-1] = line_words[-1].rstrip() + word
        return line_words
    
    line_words.append(word)
    return line_words

def join_line_words(line_words: List[str]) -> str:
    """Join words with proper punctuation spacing."""
    if not line_words:
        return ""
    result = []
    for word in line_words:
        if word in PUNCT_NO_SPACE_BEFORE and result:
            # Attach to previous word
            result[-1] = result[-1].rstrip() + word
        else:
            result.append(word)
    return ' '.join(result)
```

### File: `tests/test_word_based_lyrics_formatting.py`

**Added new test:**

```python
def test_punctuation_spacing():
    """Test that punctuation has no space before it."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": ",", "start": 0.5, "end": 0.6},
            {"word": "world", "start": 0.7, "end": 1.2},
            {"word": "!", "start": 1.2, "end": 1.3},
            {"word": "Tôi", "start": 2.0, "end": 2.5},
            {"word": "yêu", "start": 2.6, "end": 3.0},
            {"word": "em", "start": 3.1, "end": 3.5},
            {"word": ".", "start": 3.5, "end": 3.6},
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(segments)
    
    # Verifies no space before punctuation
    assert " ," not in formatted
    assert " !" not in formatted
    assert " ." not in formatted
```

## Test Results

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
✓ Punctuation spacing correct: Hello, world! Tôi yêu em.

✅ All word-based formatting tests passed! (10/10)
```

## Example Output

**Input words:**
```python
["Hello", ",", "world", "!", "Tôi", "yêu", "em", "."]
```

**Output (with correct spacing):**
```
Hello, world! Tôi yêu em.
```

**NOT:**
```
Hello , world ! Tôi yêu em .  ❌ (space before punctuation)
```

## Configuration

Current default thresholds in `.env`:

```bash
# Current defaults
LYRICS_MAX_CHARS_PER_LINE=60        # Your preference: 34
LYRICS_LINE_GAP_THRESHOLD=0.8       # Your preference: 0.45
LYRICS_STANZA_GAP_THRESHOLD=2.5     # Your preference: 1.8
```

**To use your preferred values, update `.env`:**

```bash
# Tighter thresholds for shorter lines
LYRICS_MAX_CHARS_PER_LINE=34
LYRICS_LINE_GAP_THRESHOLD=0.45
LYRICS_STANZA_GAP_THRESHOLD=1.8
```

## Implementation Status

✅ **Word timestamps enabled** - `word_timestamps=True` in Whisper call  
✅ **Gap-based line breaks** - Configurable thresholds  
✅ **Character-based wrapping** - Respects max_chars_per_line  
✅ **Stanza breaks** - Blank lines at larger gaps  
✅ **Punctuation spacing** - No space before `,` `.` `!` `?` `;` `:`  
✅ **Vietnamese diacritics** - Fully preserved  
✅ **Token order** - Never changed  
✅ **Unit tests** - 10/10 passing  

## Files Modified

1. `app/lyrics_service/pipeline/postprocess.py` - Added punctuation handling
2. `tests/test_word_based_lyrics_formatting.py` - Added punctuation test

## Whisper Configuration (Already in Place)

```python
segments, info = self.model.transcribe(
    audio_path,
    language="vi",                      # Vietnamese
    task="transcribe",                  # NOT translate
    word_timestamps=True,               # ✅ Enabled
    vad_filter=True,                    # ✅ Voice activity detection
    temperature=0.0,                    # ✅ Deterministic
    beam_size=5,                        # ✅ Quality
    condition_on_previous_text=False    # ✅ Better for singing
)
```

## UI Rendering

If formatted lyrics display as one paragraph in the UI, ensure CSS renders newlines:

**React/Next.js:**
```jsx
<div style={{whiteSpace: 'pre-wrap'}}>{lyrics}</div>
```

**CSS:**
```css
.lyrics {
  white-space: pre-wrap;
}
```

## Complete Feature Set

The formatter now handles:
- ✅ Line breaks at configurable time gaps
- ✅ Stanza breaks (blank lines) at longer gaps
- ✅ Character-based line wrapping
- ✅ Punctuation spacing (no space before)
- ✅ Vietnamese diacritics preservation
- ✅ Token order preservation
- ✅ Noise removal (music, applause tags)
- ✅ Multiple consecutive spaces → single space
- ✅ Excessive line breaks (3+) → double

## Ready for Production

**Status:** ✅ PRODUCTION READY

All requested features implemented and tested:
- Word timestamps ✅
- Gap-based formatting ✅
- Character wrapping ✅
- Punctuation handling ✅
- Vietnamese support ✅
- Configurable thresholds ✅
- Comprehensive tests ✅
