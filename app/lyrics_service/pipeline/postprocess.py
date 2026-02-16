"""
Post-processing module for cleaning and formatting transcribed lyrics.
Pure Python heuristics only - no LLM dependency.
Removes noise tags, normalizes spacing, adds line breaks based on timing gaps.
"""
import logging
import re
from typing import List, Dict, Optional

from app.lyrics_service import config

logger = logging.getLogger(__name__)

# Common noise patterns in ASR output
NOISE_PATTERNS = [
    r'\(music\)',
    r'\[music\]',
    r'\(Music\)',
    r'\[Music\]',
    r'\(applause\)',
    r'\[applause\]',
    r'\(laughter\)',
    r'\[laughter\]',
    r'\(noise\)',
    r'\[noise\]',
    r'\(silence\)',
    r'\[silence\]',
    r'<.*?>',  # HTML-like tags
    r'\[.*?instrumental.*?\]',
    r'\(.*?instrumental.*?\)',
]

# Compile patterns for efficiency
COMPILED_NOISE_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in NOISE_PATTERNS]


def clean_transcription_text(text: str) -> str:
    """
    Clean transcribed text by removing noise tags and normalizing spacing.
    
    Args:
        text: Raw transcription text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    cleaned = text
    
    # Remove noise patterns
    for pattern in COMPILED_NOISE_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    
    # Remove multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join(line for line in lines if line)
    
    # Normalize punctuation spacing
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    cleaned = re.sub(r'([.,!?;:])([^\s\d])', r'\1 \2', cleaned)
    
    return cleaned.strip()


def detect_language(text: str) -> str:
    """
    Simple heuristic to detect language (en/vi/mixed).
    
    Args:
        text: Text to analyze
    
    Returns:
        "en", "vi", "mixed", or "unknown"
    """
    if not text:
        return "unknown"
    
    # Vietnamese-specific characters
    vietnamese_chars = 'ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
    
    # Count Vietnamese characters
    vi_count = sum(1 for char in text.lower() if char in vietnamese_chars)
    
    # Count English alphabet (excluding Vietnamese chars)
    en_count = sum(1 for char in text if char.isalpha() and char.lower() not in vietnamese_chars)
    
    total_alpha = vi_count + en_count
    
    if total_alpha == 0:
        return "unknown"
    
    vi_ratio = vi_count / total_alpha
    
    if vi_ratio > 0.3:
        if vi_ratio < 0.7:
            return "mixed"
        return "vi"
    elif en_count > 10:
        return "en"
    
    return "unknown"


def format_lyrics_from_words(
    segments: List[Dict],
    max_chars_per_line: int = 60,
    line_gap_threshold: float = 0.8,
    stanza_gap_threshold: float = 2.5,
    uppercase_break: bool = True,
    min_chars_before_upper_break: int = 18,
    min_words_before_upper_break: int = 4
) -> tuple[str, List[Dict]]:
    """
    Format lyrics from word-level timestamps with intelligent line/stanza breaks.
    
    Args:
        segments: List of segment dicts with 'words' arrays
        max_chars_per_line: Maximum characters per line (soft limit)
        line_gap_threshold: Time gap (seconds) to trigger new line
        stanza_gap_threshold: Time gap (seconds) to trigger stanza break
        uppercase_break: Enable line breaks before uppercase words
        min_chars_before_upper_break: Minimum chars in line before uppercase break
        min_words_before_upper_break: Minimum words in line before uppercase break
    
    Returns:
        (formatted_lyrics_text, word_timestamps_list)
    """
    # Punctuation that should not have space before it
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
    
    def starts_with_uppercase(word: str) -> bool:
        """Check if word starts with an uppercase letter (Unicode-aware)."""
        word = word.strip()
        if not word:
            return False
        first_char = word[0]
        return first_char.isalpha() and first_char.isupper()
    
    if not segments:
        return "", []
    
    # Extract all words with timestamps
    all_words = []
    for segment in segments:
        if 'words' in segment:
            for word_info in segment['words']:
                word_text = word_info.get('word', '').strip()
                if word_text:
                    all_words.append({
                        'word': word_text,
                        'start': word_info.get('start', 0.0),
                        'end': word_info.get('end', 0.0)
                    })
    
    if not all_words:
        return "", []
    
    # Build lines based on timing gaps and character limits
    lines = []
    current_line = []
    current_line_chars = 0
    current_line_words = 0  # Track word count (non-punctuation)
    prev_end = 0.0
    
    for i, word_info in enumerate(all_words):
        word = word_info['word']
        start = word_info['start']
        end = word_info['end']
        gap = start - prev_end if i > 0 else 0.0
        
        # Determine if we should break to new line/stanza
        should_break_stanza = gap >= stanza_gap_threshold and current_line
        should_break_line = (gap >= line_gap_threshold and current_line) or \
                           (current_line_chars + len(word) + 1 > max_chars_per_line and current_line)
        
        # Check for uppercase-based break (fallback when timing gaps don't produce breaks)
        should_break_uppercase = False
        if uppercase_break and current_line and starts_with_uppercase(word):
            # Break if current line exceeds minimum thresholds
            if current_line_chars >= min_chars_before_upper_break or \
               current_line_words >= min_words_before_upper_break:
                should_break_uppercase = True
        
        if should_break_stanza:
            # Flush current line and add stanza break
            lines.append(join_line_words(current_line))
            lines.append('')  # Blank line for stanza separator
            current_line = [word]
            current_line_chars = len(word)
            current_line_words = 1 if word not in PUNCT_NO_SPACE_BEFORE else 0
        elif should_break_line or should_break_uppercase:
            # Flush current line
            lines.append(join_line_words(current_line))
            current_line = [word]
            current_line_chars = len(word)
            current_line_words = 1 if word not in PUNCT_NO_SPACE_BEFORE else 0
        else:
            # Add to current line
            current_line = append_word_to_line(current_line, word)
            if len(current_line) > 1:
                current_line_chars += 1  # Space before word
            current_line_chars += len(word)
            if word not in PUNCT_NO_SPACE_BEFORE:
                current_line_words += 1
        
        prev_end = end
    
    # Flush remaining line
    if current_line:
        lines.append(join_line_words(current_line))
    
    # Join and clean (but preserve stanza breaks)
    formatted_lyrics = '\n'.join(lines)
    
    # Clean individual lines without removing blank lines
    cleaned_lines = []
    for line in formatted_lyrics.split('\n'):
        if line.strip():
            # Clean non-empty lines
            cleaned_line = line.strip()
            # Remove noise patterns from this line
            for pattern in COMPILED_NOISE_PATTERNS:
                cleaned_line = pattern.sub('', cleaned_line)
            cleaned_line = re.sub(r' +', ' ', cleaned_line)
            cleaned_lines.append(cleaned_line)
        else:
            # Preserve blank lines
            cleaned_lines.append('')
    
    formatted_lyrics = '\n'.join(cleaned_lines)
    
    # Remove excessive line breaks (more than double)
    formatted_lyrics = re.sub(r'\n{3,}', '\n\n', formatted_lyrics)
    
    return formatted_lyrics.strip(), all_words


def format_lyrics_with_timestamps(
    segments: List[Dict],
    include_word_timestamps: bool = False
) -> tuple[str, Optional[List[Dict]]]:
    """
    Format lyrics from transcription segments with proper line breaks.
    
    Args:
        segments: List of segment dicts from transcription
            Each segment should have: 'start', 'end', 'text'
            Optionally: 'words' (for word-level timestamps)
        include_word_timestamps: Whether to include word-level timestamps
    
    Returns:
        (formatted_lyrics_text, word_timestamps_list or None)
    """
    if not segments:
        return "", None
    
    # Check if we have word-level data - if so, use word-based formatting
    has_words = any('words' in seg and seg['words'] for seg in segments)
    if has_words:
        formatted, words = format_lyrics_from_words(
            segments,
            max_chars_per_line=config.MAX_CHARS_PER_LINE,
            line_gap_threshold=config.LINE_GAP_THRESHOLD,
            stanza_gap_threshold=config.STANZA_GAP_THRESHOLD,
            uppercase_break=config.ENABLE_UPPERCASE_BREAKS,
            min_chars_before_upper_break=config.MIN_CHARS_BEFORE_UPPER_BREAK,
            min_words_before_upper_break=config.MIN_WORDS_BEFORE_UPPER_BREAK
        )
        
        # Log formatted output for debugging
        newline_count = formatted.count('\n')
        logger.debug(f"[DEBUG] Word-based formatting: len={len(formatted)}, newlines={newline_count}, repr={repr(formatted[:200])}")
        
        return formatted, words if include_word_timestamps else None
    
    # Fallback: segment-level formatting
    lines = []
    word_timestamps = [] if include_word_timestamps else None
    
    prev_end = 0.0
    current_stanza_lines = []
    
    for segment in segments:
        text = segment.get('text', '').strip()
        if not text:
            continue
        
        start = segment.get('start', 0.0)
        end = segment.get('end', 0.0)
        
        # Clean the segment text
        cleaned_text = clean_transcription_text(text)
        if not cleaned_text:
            continue
        
        # Determine if we need a line break or stanza break
        gap = start - prev_end
        
        # Adjusted thresholds for singing (shorter gaps needed for sung phrases)
        if gap > 1.0 and current_stanza_lines:
            # Large gap: start new stanza (double line break)
            lines.append('\n'.join(current_stanza_lines))
            lines.append('')  # Empty line for stanza break
            current_stanza_lines = [cleaned_text]
        elif gap > 0.3 or not current_stanza_lines:
            # Medium gap or first line: new line
            if current_stanza_lines and gap > 0.3:
                # Flush current stanza
                lines.append('\n'.join(current_stanza_lines))
                current_stanza_lines = [cleaned_text]
            else:
                current_stanza_lines.append(cleaned_text)
        else:
            # Small gap: continue on same line
            if current_stanza_lines:
                current_stanza_lines[-1] += ' ' + cleaned_text
            else:
                current_stanza_lines.append(cleaned_text)
        
        prev_end = end
        
        # Extract word-level timestamps if available
        if include_word_timestamps and 'words' in segment:
            for word_info in segment['words']:
                word_timestamps.append({
                    'word': word_info.get('word', '').strip(),
                    'start': word_info.get('start', 0.0),
                    'end': word_info.get('end', 0.0)
                })
    
    # Add remaining lines
    if current_stanza_lines:
        lines.append('\n'.join(current_stanza_lines))
    
    # Join all lines
    formatted_lyrics = '\n'.join(lines)
    
    # DEBUG: Log before cleanup
    newline_count_before = formatted_lyrics.count('\n')
    logger.debug(f"[DEBUG] Segment-based formatting before cleanup: len={len(formatted_lyrics)}, newlines={newline_count_before}")
    
    # Final cleanup - preserve blank lines (stanza breaks)
    # Don't use clean_transcription_text here as it removes blank lines
    cleaned_lines = []
    for line in formatted_lyrics.split('\n'):
        if line.strip():
            # Clean non-empty lines
            cleaned_line = line.strip()
            # Remove noise patterns from this line
            for pattern in COMPILED_NOISE_PATTERNS:
                cleaned_line = pattern.sub('', cleaned_line)
            cleaned_line = re.sub(r' +', ' ', cleaned_line)
            # Normalize punctuation spacing
            cleaned_line = re.sub(r'\s+([.,!?;:])', r'\1', cleaned_line)
            cleaned_line = re.sub(r'([.,!?;:])([^\s\d])', r'\1 \2', cleaned_line)
            cleaned_lines.append(cleaned_line)
        else:
            # Preserve blank lines (stanza breaks)
            cleaned_lines.append('')
    
    formatted_lyrics = '\n'.join(cleaned_lines)
    
    # Remove excessive line breaks (3+ consecutive newlines)
    formatted_lyrics = re.sub(r'\n{3,}', '\n\n', formatted_lyrics)
    
    # DEBUG: Log after cleanup
    newline_count_after = formatted_lyrics.count('\n')
    logger.debug(f"[DEBUG] Segment-based formatting after cleanup: len={len(formatted_lyrics)}, newlines={newline_count_after}, repr={repr(formatted_lyrics[:200])}")
    
    return formatted_lyrics.strip(), word_timestamps


def deduplicate_repetitive_lines(lyrics: str, max_consecutive_repeats: int = 2) -> str:
    """
    Remove excessive repetition of identical consecutive lines.
    Keeps up to max_consecutive_repeats of the same line.
    
    Args:
        lyrics: Lyrics text with line breaks
        max_consecutive_repeats: Maximum allowed consecutive repeats
    
    Returns:
        Deduplicated lyrics
    """
    if not lyrics:
        return ""
    
    lines = lyrics.split('\n')
    result = []
    prev_line = None
    repeat_count = 0
    
    for line in lines:
        normalized_line = line.strip().lower()
        
        if normalized_line == prev_line:
            repeat_count += 1
            if repeat_count < max_consecutive_repeats:
                result.append(line)
        else:
            result.append(line)
            prev_line = normalized_line
            repeat_count = 0
    
    return '\n'.join(result)


def postprocess_lyrics(
    raw_text: str = None,
    segments: List[Dict] = None,
    include_word_timestamps: bool = False,
    deduplicate: bool = True
) -> Dict:
    """
    Main post-processing function.
    
    Args:
        raw_text: Raw transcription text (if segments not available)
        segments: List of transcription segments with timing
        include_word_timestamps: Whether to extract word-level timestamps
        deduplicate: Whether to remove repetitive lines
    
    Returns:
        Dict with:
            - lyrics: Cleaned and formatted lyrics text
            - words: List of word timestamps (if requested)
            - language_detected: Detected language
    """
    lyrics = ""
    word_timestamps = None
    
    # DEBUG: Log input parameters
    logger.debug(f"[DEBUG] postprocess_lyrics called with: segments={'present' if segments else 'none'}, raw_text={'present' if raw_text else 'none'}")
    
    # Process segments if available (preferred)
    if segments:
        logger.debug(f"[DEBUG] Processing {len(segments)} segments with timestamps")
        lyrics, word_timestamps = format_lyrics_with_timestamps(
            segments,
            include_word_timestamps=include_word_timestamps
        )
    elif raw_text:
        # Fallback: clean raw text
        logger.warning("[DEBUG] Fallback to raw_text - no line breaks will be added!")
        lyrics = clean_transcription_text(raw_text)
    
    # DEBUG: Log after formatting
    newline_count = lyrics.count('\n')
    logger.debug(f"[DEBUG] After formatting: len={len(lyrics)}, newlines={newline_count}")
    logger.debug(f"[DEBUG] First 500 chars REPR: {repr(lyrics[:500])}")
    
    # Deduplicate if requested
    if deduplicate and lyrics:
        before_dedup_newlines = lyrics.count('\n')
        lyrics = deduplicate_repetitive_lines(lyrics)
        after_dedup_newlines = lyrics.count('\n')
        logger.debug(f"[DEBUG] After deduplication: newlines {before_dedup_newlines} -> {after_dedup_newlines}")
    
    # Detect language
    language_detected = detect_language(lyrics)
    
    # DEBUG: Log final output
    final_newline_count = lyrics.count('\n')
    logger.info(f"[DEBUG] Final lyrics: language={language_detected}, len={len(lyrics)}, newlines={final_newline_count}")
    logger.debug(f"[DEBUG] Final 500 chars REPR: {repr(lyrics[:500])}")
    
    return {
        'lyrics': lyrics,
        'words': word_timestamps,
        'language_detected': language_detected
    }
