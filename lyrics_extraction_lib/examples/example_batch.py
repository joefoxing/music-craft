"""
Example 3: Batch Processing
Process multiple audio files and save results
"""
from lyrics_extraction import LyricsExtractor
from pathlib import Path
import json
from datetime import datetime

def batch_processing():
    """Process all MP3 files in a directory."""
    
    # Initialize extractor once (reuse for multiple files)
    extractor = LyricsExtractor(
        model_size="base",  # Smaller model for speed
        device="cuda"  # Use GPU if available
    )
    
    # Configure paths
    audio_dir = Path("./music")
    output_dir = Path("./lyrics_output")
    output_dir.mkdir(exist_ok=True)
    
    results_summary = []
    
    # Process each audio file
    for audio_file in audio_dir.glob("**/*.mp3"):
        print(f"\n{'='*60}")
        print(f"Processing: {audio_file.name}")
        print(f"{'='*60}")
        
        try:
            # Extract lyrics
            result = extractor.extract(
                str(audio_file),
                language="auto",
                include_timestamps=False
            )
            
            # Save lyrics as text file
            lyrics_file = output_dir / audio_file.stem / "lyrics.txt"
            lyrics_file.parent.mkdir(exist_ok=True)
            lyrics_file.write_text(result['lyrics'], encoding='utf-8')
            
            # Save metadata as JSON
            metadata_file = output_dir / audio_file.stem / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(result['metadata'], f, indent=2)
            
            # Track results
            summary = {
                'file': audio_file.name,
                'status': 'success',
                'language': result['language'],
                'lyrics_length': len(result['lyrics']),
                'duration_seconds': result['metadata']['duration_seconds'],
                'timestamp': datetime.now().isoformat()
            }
            results_summary.append(summary)
            
            print(f"✓ Success")
            print(f"  Language: {result['language']}")
            print(f"  Lyrics: {len(result['lyrics'])} characters")
            print(f"  Duration: {result['metadata']['duration_seconds']:.1f}s")
            
        except Exception as e:
            summary = {
                'file': audio_file.name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            results_summary.append(summary)
            
            print(f"✗ Failed: {e}")
    
    # Save summary report
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Batch Processing Complete")
    print(f"{'='*60}")
    print(f"Total files: {len(results_summary)}")
    print(f"Successful: {sum(1 for r in results_summary if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results_summary if r['status'] == 'failed')}")
    print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    batch_processing()
