"""
Unit tests for uppercase-based line breaking in word-based lyrics formatting.
Tests that uppercase words trigger line breaks when thresholds are met.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lyrics_service.pipeline.postprocess import format_lyrics_from_words


def test_uppercase_break_basic():
    """Test basic uppercase line break with Vietnamese words."""
    segments = [{
        "start": 0.0,
        "end": 10.0,
        "words": [
            {"word": "Một", "start": 0.0, "end": 0.5},
            {"word": "ngày", "start": 0.6, "end": 1.0},
            {"word": "nắng", "start": 1.1, "end": 1.5},
            {"word": "nhẹ", "start": 1.6, "end": 2.0},  # 4 words
            {"word": "Để", "start": 2.1, "end": 2.5},   # Uppercase, should break
            {"word": "tôi", "start": 2.6, "end": 3.0},
            {"word": "đi", "start": 3.1, "end": 3.5},
            {"word": "về", "start": 3.6, "end": 4.0},
            {"word": "Một", "start": 4.1, "end": 4.5},  # Uppercase, should break
            {"word": "chiều", "start": 4.6, "end": 5.0},
            {"word": "mưa", "start": 5.1, "end": 5.5},
        ]
    }]
    
    # Enable uppercase breaks with thresholds
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,  # Don't trigger char limit
        line_gap_threshold=10.0,  # Don't trigger gap break
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=18,
        min_words_before_upper_break=4
    )
    
    lines = formatted.split('\n')
    
    # Should have 3 lines (break before "Để" and "Một")
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}: {lines}"
    assert "Một ngày nắng nhẹ" in lines[0]
    assert "Để tôi đi về" in lines[1]
    assert "Một chiều mưa" in lines[2]
    
    print(f"✓ Basic uppercase break: {lines}")


def test_uppercase_break_min_chars():
    """Test that uppercase break respects min_chars threshold."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Tôi", "start": 0.0, "end": 0.5},
            {"word": "yêu", "start": 0.6, "end": 1.0},
            {"word": "Em", "start": 1.1, "end": 1.5},  # Uppercase but only 8 chars before
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=18,  # "Tôi yêu" is only 7 chars
        min_words_before_upper_break=10   # Need 10 words
    )
    
    lines = formatted.split('\n')
    
    # Should be single line (doesn't meet either threshold)
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {lines}"
    assert "Tôi yêu Em" in lines[0]
    
    print(f"✓ Min chars threshold respected: {lines[0]}")


def test_uppercase_break_min_words():
    """Test that uppercase break respects min_words threshold."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Một", "start": 0.0, "end": 0.5},
            {"word": "ngày", "start": 0.6, "end": 1.0},
            {"word": "nắng", "start": 1.1, "end": 1.5},
            {"word": "Để", "start": 1.6, "end": 2.0},  # Uppercase, 3 words before
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=100,  # Very high char threshold
        min_words_before_upper_break=3    # Only 3 words needed
    )
    
    lines = formatted.split('\n')
    
    # Should break (meets word threshold)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}: {lines}"
    assert "Một ngày nắng" in lines[0]
    assert "Để" in lines[1]
    
    print(f"✓ Min words threshold respected: {lines}")


def test_uppercase_break_disabled():
    """Test that uppercase break can be disabled."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Một", "start": 0.0, "end": 0.5},
            {"word": "ngày", "start": 0.6, "end": 1.0},
            {"word": "nắng", "start": 1.1, "end": 1.5},
            {"word": "nhẹ", "start": 1.6, "end": 2.0},
            {"word": "Để", "start": 2.1, "end": 2.5},  # Uppercase (would break if enabled)
            {"word": "tôi", "start": 2.6, "end": 3.0},
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=False  # Disabled
    )
    
    lines = formatted.split('\n')
    
    # Should be single line (uppercase break disabled)
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}: {lines}"
    
    print(f"✓ Uppercase break disabled: {lines[0]}")


def test_uppercase_break_with_punctuation():
    """Test uppercase break with punctuation tokens."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": ",", "start": 0.5, "end": 0.6},
            {"word": "world", "start": 0.7, "end": 1.2},
            {"word": "!", "start": 1.2, "end": 1.3},  # Punctuation doesn't count toward word count
            {"word": "Tôi", "start": 2.0, "end": 2.5},
            {"word": "yêu", "start": 2.6, "end": 3.0},
            {"word": "em", "start": 3.1, "end": 3.5},
            {"word": ".", "start": 3.5, "end": 3.6},
            {"word": "Một", "start": 4.0, "end": 4.5},  # Uppercase
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=18,
        min_words_before_upper_break=4  # Have 5 non-punct words
    )
    
    lines = formatted.split('\n')
    
    # Should break before "Một" (have 5 words: Hello, world, Tôi, yêu, em)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}: {lines}"
    assert "Hello, world! Tôi yêu em." in lines[0]
    assert "Một" in lines[1]
    
    print(f"✓ Uppercase break with punctuation: {lines}")


def test_uppercase_break_combined_with_gap():
    """Test that uppercase break works alongside timing gap breaks."""
    segments = [{
        "start": 0.0,
        "end": 10.0,
        "words": [
            {"word": "First", "start": 0.0, "end": 0.5},
            {"word": "line", "start": 0.6, "end": 1.0},
            {"word": "here", "start": 1.1, "end": 1.5},
            # Large gap - should trigger gap break
            {"word": "Second", "start": 3.0, "end": 3.5},  # Gap = 1.5s
            {"word": "line", "start": 3.6, "end": 4.0},
            {"word": "here", "start": 4.1, "end": 4.5},
            {"word": "now", "start": 4.6, "end": 5.0},
            {"word": "Third", "start": 5.1, "end": 5.5},  # Uppercase, should break
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=1.0,  # Gap threshold
        stanza_gap_threshold=5.0,
        uppercase_break=True,
        min_chars_before_upper_break=15,
        min_words_before_upper_break=3
    )
    
    lines = formatted.split('\n')
    
    # Should have 3 lines (gap break after "here", uppercase break before "Third")
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}: {lines}"
    assert "First line here" in lines[0]
    assert "Second line here now" in lines[1]
    assert "Third" in lines[2]
    
    print(f"✓ Combined uppercase and gap breaks: {lines}")


def test_newline_count_long_input():
    """Test that long input produces multiple newlines."""
    # Create a long sequence with many uppercase words
    words = []
    time_offset = 0.0
    for i in range(20):
        words.extend([
            {"word": f"Word{i}", "start": time_offset, "end": time_offset + 0.3},
            {"word": "test", "start": time_offset + 0.3, "end": time_offset + 0.6},
            {"word": "here", "start": time_offset + 0.6, "end": time_offset + 0.9},
            {"word": "Uppercase", "start": time_offset + 1.0, "end": time_offset + 1.3},  # Uppercase
        ])
        time_offset += 1.5
    
    segments = [{"start": 0.0, "end": time_offset, "words": words}]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=0,  # Always break on uppercase
        min_words_before_upper_break=0
    )
    
    newline_count = formatted.count('\n')
    
    # Should have many newlines (break before each "Uppercase")
    assert newline_count > 10, f"Expected >10 newlines, got {newline_count}"
    assert len(formatted) > 100, f"Expected long output, got {len(formatted)} chars"
    
    print(f"✓ Long input produces {newline_count} newlines: repr={repr(formatted[:100])}")


def test_uppercase_break_english_and_vietnamese():
    """Test uppercase detection works for both English and Vietnamese."""
    segments = [{
        "start": 0.0,
        "end": 5.0,
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.6, "end": 1.0},
            {"word": "Ánh", "start": 1.1, "end": 1.5},  # Vietnamese uppercase
            {"word": "mắt", "start": 1.6, "end": 2.0},
            {"word": "Đẹp", "start": 2.1, "end": 2.5},  # Vietnamese uppercase
        ]
    }]
    
    formatted, _ = format_lyrics_from_words(
        segments,
        max_chars_per_line=100,
        line_gap_threshold=10.0,
        stanza_gap_threshold=20.0,
        uppercase_break=True,
        min_chars_before_upper_break=0,
        min_words_before_upper_break=1
    )
    
    lines = formatted.split('\n')
    
    # Should break before "Ánh" and "Đẹp"
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}: {lines}"
    
    print(f"✓ English and Vietnamese uppercase: {lines}")


if __name__ == "__main__":
    print("=== Testing Uppercase-Based Line Breaking ===\n")
    
    test_uppercase_break_basic()
    test_uppercase_break_min_chars()
    test_uppercase_break_min_words()
    test_uppercase_break_disabled()
    test_uppercase_break_with_punctuation()
    test_uppercase_break_combined_with_gap()
    test_newline_count_long_input()
    test_uppercase_break_english_and_vietnamese()
    
    print("\n✅ All uppercase line break tests passed!")
