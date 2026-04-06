"""
Example 5: Error Handling
Proper error handling for production use
"""
from lyrics_extraction import extract_lyrics, LyricsExtractor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def error_handling_example():
    """Demonstrate error handling."""
    
    test_files = [
        "valid_song.mp3",  # Good file
        "nonexistent.mp3",  # Doesn't exist
        "corrupted.mp3",  # Not valid audio
        "too_large.mp3"  # Exceeds size limit
    ]
    
    for audio_file in test_files:
        print(f"\nProcessing: {audio_file}")
        print("-" * 40)
        
        try:
            result = extract_lyrics(
                audio_file,
                model_size="base",
                device="cpu"
            )
            
            print(f"✓ Success")
            print(f"  Language: {result['language']}")
            print(f"  Lyrics: {len(result['lyrics'])} chars")
            
        except FileNotFoundError as e:
            logger.error(f"✗ File not found: {e}")
            continue
        
        except ValueError as e:
            logger.error(f"✗ Invalid audio: {e}")
            # Could retry with different extraction settings
            continue
        
        except RuntimeError as e:
            if "CUDA" in str(e):
                logger.error(f"✗ GPU error: {e}")
                logger.info("  Retrying with CPU...")
                try:
                    result = extract_lyrics(audio_file, device="cpu")
                    print(f"✓ Success (CPU fallback)")
                except Exception as e2:
                    logger.error(f"✗ Still failed: {e2}")
            else:
                logger.error(f"✗ Runtime error: {e}")
        
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            logger.debug(f"Exception type: {type(e).__name__}")


def advanced_error_handling():
    """Advanced error handling with retries."""
    
    extractor = LyricsExtractor(device="cuda")
    audio_file = "song.mp3"
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = extractor.extract(audio_file)
            print(f"✓ Success on attempt {retry_count + 1}")
            return result
        
        except RuntimeError as e:
            if "CUDA" in str(e) and retry_count < max_retries - 1:
                retry_count += 1
                logger.warning(f"CUDA error, retrying with CPU (attempt {retry_count})...")
                # Reinitialize with CPU
                extractor = LyricsExtractor(device="cpu")
                continue
            else:
                raise
        
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Error on attempt {retry_count}, retrying...")
            else:
                logger.error(f"Failed after {max_retries} attempts")
                raise


if __name__ == "__main__":
    print("=== Basic Error Handling ===")
    error_handling_example()
    
    print("\n\n=== Advanced Error Handling ===")
    try:
        result = advanced_error_handling()
    except Exception as e:
        logger.error(f"Final error: {e}")
