"""
Example 1: Basic Lyrics Extraction
Extract lyrics from a single audio file
"""
from lyrics_extraction import extract_lyrics

def basic_extraction():
    """Simple one-liner extraction."""
    result = extract_lyrics("sample_song.mp3")
    
    print("=== Extracted Lyrics ===")
    print(result['lyrics'])
    print(f"\nLanguage: {result['language']}")
    print(f"Duration: {result['metadata']['duration_seconds']:.1f} seconds")


if __name__ == "__main__":
    basic_extraction()
