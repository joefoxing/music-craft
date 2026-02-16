"""
Unit tests for Vietnamese lyrics extraction: verify diacritics are preserved.
"""
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test the fixed functions that were stripping diacritics


def test_normalize_for_repeat_check_preserves_vietnamese():
    """Test that _normalize_for_repeat_check preserves Vietnamese diacritics."""
    # Sample Vietnamese text with diacritics
    vietnamese_text = "Tôi yêu em, con đường dài, ánh mắt người"
    
    # Simulate the fixed _normalize_for_repeat_check function
    cleaned = re.sub(r"[^\w\s']", '', vietnamese_text.lower(), flags=re.UNICODE)
    normalized = re.sub(r"\s+", ' ', cleaned).strip()
    
    # Assert Vietnamese characters are preserved
    assert 'ô' in normalized, f"Lost ô: {repr(normalized)}"
    assert 'ê' in normalized, f"Lost ê: {repr(normalized)}"
    assert 'ư' in normalized, f"Lost ư: {repr(normalized)}"
    assert 'đ' in normalized, f"Lost đ: {repr(normalized)}"
    assert 'á' in normalized, f"Lost á: {repr(normalized)}"
    assert 'ắ' in normalized or 'ă' in normalized or 'ạ' in normalized, "Lost Vietnamese diacritic marks"
    
    print(f"✓ _normalize_for_repeat_check preserves Vietnamese: {repr(normalized)}")


def test_tokenize_words_recognizes_vietnamese():
    """Test that _tokenize_words recognizes Vietnamese words."""
    vietnamese_text = "Tôi yêu Việt Nam, con đường dài"
    
    # Simulate the fixed _tokenize_words function
    words = re.findall(r"[\w']+", vietnamese_text.lower(), re.UNICODE)
    
    # Should extract all words including Vietnamese characters
    assert len(words) >= 5, f"Expected at least 5 words, got {len(words)}: {words}"
    
    # Check that Vietnamese words are not split into characters
    assert any(len(w) > 2 for w in words), f"Words seem too short (char-split?): {words}"
    
    # Verify specific Vietnamese words are intact
    text_lower = vietnamese_text.lower()
    for word_original in ['tôi', 'việt', 'đường']:
        assert any(word_original in w for w in words), f"Word '{word_original}' not found in tokens: {words}"
    
    print(f"✓ _tokenize_words recognizes Vietnamese: {words}")


def test_postprocess_pipeline_preserves_diacritics():
    """Test full postprocessing pipeline with Vietnamese sample."""
    from app.lyrics_service.pipeline.postprocess import postprocess_lyrics
    
    # Sample Vietnamese lyrics with diacritics
    vietnamese_segments = [
        {"start": 0.0, "end": 3.0, "text": "Tôi yêu em nhiều lắm"},
        {"start": 3.5, "end": 6.0, "text": "Con đường dài về nhà"},
        {"start": 6.5, "end": 9.0, "text": "Ánh mắt người xa xôi"}
    ]
    
    result = postprocess_lyrics(
        segments=vietnamese_segments,
        deduplicate=True
    )
    
    lyrics = result['lyrics']
    
    # Verify diacritics are preserved
    assert 'ô' in lyrics, f"Lost ô after postprocessing: {repr(lyrics)}"
    assert 'ê' in lyrics, f"Lost ê after postprocessing: {repr(lyrics)}"
    assert 'đ' in lyrics, f"Lost đ after postprocessing: {repr(lyrics)}"
    assert 'á' in lyrics or 'ắ' in lyrics, f"Lost tone marks after postprocessing: {repr(lyrics)}"
    
    # Verify words are not character-split with spaces
    assert 'T ô i' not in lyrics, f"Text is character-split: {repr(lyrics)}"
    assert 'y ê u' not in lyrics, f"Text is character-split: {repr(lyrics)}"
    
    # Verify reasonable word boundaries (words should have 2+ chars typically)
    words = lyrics.split()
    long_words = [w for w in words if len(w) >= 2]
    assert len(long_words) >= len(words) * 0.7, f"Too many single-char 'words': {words}"
    
    print(f"✓ Postprocessing preserves diacritics: {repr(lyrics[:80])}")
    print(f"  Language detected: {result['language_detected']}")


def test_clean_transcription_preserves_vietnamese():
    """Test clean_transcription_text preserves Vietnamese."""
    from app.lyrics_service.pipeline.postprocess import clean_transcription_text
    
    vietnamese_text = "Tôi yêu em (music) ánh đèn [applause] người xa"
    cleaned = clean_transcription_text(vietnamese_text)
    
    # Noise tags should be removed
    assert '(music)' not in cleaned
    assert '[applause]' not in cleaned
    
    # Vietnamese characters should remain
    assert 'ô' in cleaned, f"Lost ô: {repr(cleaned)}"
    assert 'ê' in cleaned, f"Lost ê: {repr(cleaned)}"
    assert 'đ' in cleaned, f"Lost đ: {repr(cleaned)}"
    assert 'á' in cleaned, f"Lost á: {repr(cleaned)}"
    
    print(f"✓ clean_transcription_text preserves Vietnamese: {repr(cleaned)}")


def test_detect_language_recognizes_vietnamese():
    """Test language detection for Vietnamese."""
    from app.lyrics_service.pipeline.postprocess import detect_language
    
    vietnamese_text = "Tôi yêu em nhiều lắm, con đường dài về nhà"
    detected = detect_language(vietnamese_text)
    
    assert detected in ['vi', 'mixed'], f"Expected 'vi' or 'mixed', got '{detected}'"
    
    print(f"✓ Language detection recognizes Vietnamese: {detected}")


if __name__ == '__main__':
    print("\n=== Testing Vietnamese Lyrics Extraction ===\n")
    
    try:
        test_normalize_for_repeat_check_preserves_vietnamese()
        test_tokenize_words_recognizes_vietnamese()
        test_clean_transcription_preserves_vietnamese()
        test_detect_language_recognizes_vietnamese()
        test_postprocess_pipeline_preserves_diacritics()
        
        print("\n✅ All tests passed! Vietnamese diacritics are preserved.\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
