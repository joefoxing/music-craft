"""
Unit tests for word-based lyrics formatting with Vietnamese support.
Tests format_lyrics_from_words() function.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.lyrics_service.pipeline.postprocess import format_lyrics_from_words


def test_line_break_at_gap_threshold():
    """Test that line breaks occur at line_gap_threshold."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Tôi", "start": 0.0, "end": 0.5},
            {"word": "yêu", "start": 0.6, "end": 1.0},
            {"word": "em", "start": 1.1, "end": 1.5},
            # Gap of 1.0 seconds (> 0.8 default threshold)
            {"word": "Con", "start": 2.5, "end": 3.0},
            {"word": "đường", "start": 3.1, "end": 3.6},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(
        segments,
        line_gap_threshold=0.8
    )
    
    lines = formatted.split('\n')
    
    # Should have 2 lines due to gap
    assert len(lines) >= 2, f"Expected at least 2 lines, got {len(lines)}: {lines}"
    
    # First line should contain first 3 words
    assert "Tôi yêu em" in formatted, f"Expected 'Tôi yêu em' in first line: {formatted}"
    
    # Second line should contain last 2 words
    assert "Con đường" in formatted, f"Expected 'Con đường' in second line: {formatted}"
    
    # Verify word order is preserved
    assert formatted.replace('\n', ' ').strip() == "Tôi yêu em Con đường"
    
    print(f"✓ Line break at gap threshold:\n{formatted}\n")


def test_stanza_break_at_gap_threshold():
    """Test that stanza breaks (blank lines) occur at stanza_gap_threshold."""
    segments = [{
        "start": 0.0,
        "end": 10.0,
        "words": [
            {"word": "Verse", "start": 0.0, "end": 0.5},
            {"word": "one", "start": 0.6, "end": 1.0},
            # Gap of 3.0 seconds (> 2.5 default threshold)
            {"word": "Verse", "start": 4.0, "end": 4.5},
            {"word": "two", "start": 4.6, "end": 5.0},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(
        segments,
        stanza_gap_threshold=2.5
    )
    
    # Should have blank line between stanzas
    assert '\n\n' in formatted, f"Expected blank line for stanza break: {repr(formatted)}"
    
    lines = [line for line in formatted.split('\n') if line.strip()]
    assert len(lines) == 2, f"Expected 2 non-empty lines: {lines}"
    
    print(f"✓ Stanza break at gap threshold:\n{formatted}\n")


def test_line_wrapping_at_max_chars():
    """Test that lines wrap when exceeding max_chars_per_line."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "This", "start": 0.0, "end": 0.2},
            {"word": "is", "start": 0.3, "end": 0.4},
            {"word": "a", "start": 0.5, "end": 0.6},
            {"word": "very", "start": 0.7, "end": 0.9},
            {"word": "long", "start": 1.0, "end": 1.2},
            {"word": "line", "start": 1.3, "end": 1.5},
            {"word": "that", "start": 1.6, "end": 1.8},
            {"word": "should", "start": 1.9, "end": 2.1},
            {"word": "wrap", "start": 2.2, "end": 2.4},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(
        segments,
        max_chars_per_line=20,  # Short limit to force wrapping
        line_gap_threshold=5.0  # High threshold so gaps don't trigger breaks
    )
    
    lines = formatted.split('\n')
    
    # Should have multiple lines due to character limit
    assert len(lines) >= 2, f"Expected multiple lines due to char limit: {lines}"
    
    # Each line should be roughly under max_chars (soft limit)
    for line in lines:
        if line.strip():
            # Allow some flexibility (max_chars + word length)
            assert len(line) <= 35, f"Line too long ({len(line)} chars): {line}"
    
    print(f"✓ Line wrapping at max chars ({len(lines)} lines):\n{formatted}\n")


def test_vietnamese_diacritics_preserved():
    """Test that Vietnamese diacritics are preserved in formatted output."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Tôi", "start": 0.0, "end": 0.5},
            {"word": "yêu", "start": 0.6, "end": 1.0},
            {"word": "em", "start": 1.1, "end": 1.5},
            {"word": "Ánh", "start": 2.0, "end": 2.5},
            {"word": "mắt", "start": 2.6, "end": 3.0},
            {"word": "đẹp", "start": 3.1, "end": 3.5},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(segments)
    
    # Check Vietnamese characters are preserved
    assert 'ô' in formatted, f"Lost ô: {repr(formatted)}"
    assert 'ê' in formatted, f"Lost ê: {repr(formatted)}"
    assert 'á' in formatted or 'Á' in formatted, f"Lost á: {repr(formatted)}"
    assert 'ắ' in formatted or 'ă' in formatted or 'ạ' in formatted or 'ắ' in formatted or 'ặ' in formatted or 'mắt' in formatted, f"Lost Vietnamese tone marks: {repr(formatted)}"
    assert 'đ' in formatted, f"Lost đ: {repr(formatted)}"
    assert 'ẹ' in formatted or 'ẻ' in formatted or 'ẽ' in formatted or 'ề' in formatted or 'ể' in formatted or 'ễ' in formatted or 'ệ' in formatted or 'ế' in formatted or 'ề' in formatted or 'ể' in formatted or 'đẹp' in formatted, f"Lost Vietnamese characters: {repr(formatted)}"
    
    # Verify no character-level spacing
    assert 'T ô i' not in formatted
    assert 'y ê u' not in formatted
    
    print(f"✓ Vietnamese diacritics preserved:\n{formatted}\n")


def test_token_order_preserved():
    """Test that word order is always preserved regardless of formatting."""
    segments = [{
        "start": 0.0,
        "end": 10.0,
        "words": [
            {"word": "One", "start": 0.0, "end": 0.5},
            {"word": "Two", "start": 1.0, "end": 1.5},
            {"word": "Three", "start": 4.0, "end": 4.5},  # Large gap
            {"word": "Four", "start": 4.6, "end": 5.0},
            {"word": "Five", "start": 5.1, "end": 5.5},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(segments)
    
    # Remove all line breaks and check order
    flat_text = ' '.join(formatted.split())
    expected_order = "One Two Three Four Five"
    
    assert flat_text == expected_order, f"Word order not preserved: {flat_text} != {expected_order}"
    
    # Check word timestamps list preserves order
    word_list = [w['word'] for w in words]
    assert word_list == ["One", "Two", "Three", "Four", "Five"], f"Timestamp order not preserved: {word_list}"
    
    print(f"✓ Token order preserved:\n{formatted}\n")


def test_empty_segments():
    """Test handling of empty segments."""
    segments = []
    
    formatted, words = format_lyrics_from_words(segments)
    
    assert formatted == "", f"Expected empty string for empty segments: {repr(formatted)}"
    assert words == [], f"Expected empty word list: {words}"
    
    print("✓ Empty segments handled correctly\n")


def test_segments_without_words():
    """Test handling of segments without word-level data."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "text": "This segment has no words array"
    }]
    
    formatted, words = format_lyrics_from_words(segments)
    
    assert formatted == "", f"Expected empty when no words: {repr(formatted)}"
    assert words == [], f"Expected empty word list: {words}"
    
    print("✓ Segments without words handled correctly\n")


def test_mixed_gaps_complex_formatting():
    """Test complex scenario with mixed timing gaps."""
    segments = [{
        "start": 0.0,
        "end": 20.0,
        "words": [
            # First line (tight spacing)
            {"word": "Tôi", "start": 0.0, "end": 0.3},
            {"word": "yêu", "start": 0.4, "end": 0.7},
            {"word": "em", "start": 0.8, "end": 1.1},
            # Gap 0.9s -> new line
            {"word": "Từng", "start": 2.0, "end": 2.3},
            {"word": "ngày", "start": 2.4, "end": 2.7},
            {"word": "qua", "start": 2.8, "end": 3.1},
            # Gap 3.0s -> stanza break
            {"word": "Ánh", "start": 6.1, "end": 6.4},
            {"word": "mắt", "start": 6.5, "end": 6.8},
            {"word": "người", "start": 6.9, "end": 7.2},
            # Gap 0.9s -> new line
            {"word": "Xa", "start": 8.1, "end": 8.3},
            {"word": "xôi", "start": 8.4, "end": 8.7},
        ]
    }]
    
    formatted, words = format_lyrics_from_words(
        segments,
        line_gap_threshold=0.8,
        stanza_gap_threshold=2.5
    )
    
    lines = formatted.split('\n')
    
    # Should have 4 non-empty lines (2 stanzas of 2 lines each)
    non_empty_lines = [line for line in lines if line.strip()]
    assert len(non_empty_lines) == 4, f"Expected 4 lines, got {len(non_empty_lines)}: {non_empty_lines}"
    
    # Should have 1 blank line (stanza separator)
    blank_lines = [line for line in lines if not line.strip()]
    assert len(blank_lines) == 1, f"Expected 1 blank line, got {len(blank_lines)}"
    
    # Verify content
    assert "Tôi yêu em" in formatted
    assert "Từng ngày qua" in formatted
    assert "Ánh mắt người" in formatted
    assert "Xa xôi" in formatted
    
    print(f"✓ Complex mixed gaps formatting:\n{formatted}\n")


def test_configurable_thresholds():
    """Test that gap thresholds are configurable."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Word1", "start": 0.0, "end": 0.5},
            {"word": "Word2", "start": 1.0, "end": 1.5},  # 0.5s gap
            {"word": "Word3", "start": 2.0, "end": 2.5},  # 0.5s gap
        ]
    }]
    
    # With high threshold: all on one line
    formatted_high, _ = format_lyrics_from_words(
        segments,
        line_gap_threshold=1.0
    )
    assert '\n' not in formatted_high.strip(), f"Should be one line: {repr(formatted_high)}"
    
    # With low threshold: each word on separate line
    formatted_low, _ = format_lyrics_from_words(
        segments,
        line_gap_threshold=0.3
    )
    lines = [line for line in formatted_low.split('\n') if line.strip()]
    assert len(lines) == 3, f"Should have 3 lines with low threshold: {lines}"
    
    print(f"✓ Configurable thresholds work correctly\n")


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
    
    # Should NOT have space before punctuation
    assert " ," not in formatted, f"Space before comma: {repr(formatted)}"
    assert " !" not in formatted, f"Space before exclamation: {repr(formatted)}"
    assert " ." not in formatted, f"Space before period: {repr(formatted)}"
    
    # Should have proper format
    assert "Hello," in formatted or "Hello ," not in formatted, f"Comma should attach: {repr(formatted)}"
    assert "world!" in formatted or "world !" not in formatted, f"Exclamation should attach: {repr(formatted)}"
    assert "em." in formatted or "em ." not in formatted, f"Period should attach: {repr(formatted)}"
    
    print(f"✓ Punctuation spacing correct:\n{formatted}\n")


if __name__ == '__main__':
    print("\n=== Testing Word-Based Lyrics Formatting ===\n")
    
    try:
        test_line_break_at_gap_threshold()
        test_stanza_break_at_gap_threshold()
        test_line_wrapping_at_max_chars()
        test_vietnamese_diacritics_preserved()
        test_token_order_preserved()
        test_empty_segments()
        test_segments_without_words()
        test_mixed_gaps_complex_formatting()
        test_configurable_thresholds()
        test_punctuation_spacing()
        
        print("✅ All word-based formatting tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
