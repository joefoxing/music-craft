"""
Example 2: Advanced Extraction with Timestamps
Extract lyrics with word-level timestamps for karaoke/sync
"""
from lyrics_extraction import LyricsExtractor
import json

def advanced_extraction():
    """Extract with timestamps and save as JSON."""
    
    extractor = LyricsExtractor(
        model_size="large-v3",
        device="cpu",  # Use "cuda" for GPU
        enable_vocal_separation=True,
        preprocess_audio=True
    )
    
    result = extractor.extract(
        audio_path="sample_song.mp3",
        language="auto",
        include_timestamps=True
    )
    
    # Print lyrics
    print("=== Extracted Lyrics ===")
    print(result['lyrics'])
    
    # Save as JSON with timing
    data = {
        'lyrics': result['lyrics'],
        'language': result['language'],
        'metadata': result['metadata'],
        'words': result['words'][:10] if result['words'] else None  # First 10 words
    }
    
    with open('lyrics_output.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to lyrics_output.json")
    
    # Print sample timestamps
    if result['words']:
        print("\n=== First 5 Words with Timestamps ===")
        for word in result['words'][:5]:
            print(f"  {word['word']:15} {word['start']:6.2f}s - {word['end']:6.2f}s")


if __name__ == "__main__":
    advanced_extraction()
