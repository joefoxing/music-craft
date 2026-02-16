"""
Test script for lyrics extraction service.
Tests the complete pipeline with a simple audio file.
"""
import os
import sys
import time
import requests
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("LYRICS_SERVICE_URL", "http://localhost:8000/v1")
TEST_AUDIO_PATH = "test_audio.mp3"  # Update this path

def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/v1', '')}/healthz", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def submit_job(audio_path: str, language_hint: str = "auto", timestamps: str = "none"):
    """Submit a lyrics extraction job."""
    print(f"\nSubmitting job for: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"✗ Audio file not found: {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': f}
            data = {
                'language_hint': language_hint,
                'timestamps': timestamps
            }
            
            response = requests.post(
                f"{API_BASE_URL}/lyrics",
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            job_id = result['job_id']
            print(f"✓ Job submitted: {job_id}")
            print(f"  Status: {result['status']}")
            
            return job_id
    
    except Exception as e:
        print(f"✗ Failed to submit job: {e}")
        return None


def get_job_status(job_id: str):
    """Get job status."""
    try:
        response = requests.get(f"{API_BASE_URL}/lyrics/{job_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Failed to get job status: {e}")
        return None


def wait_for_completion(job_id: str, max_wait_seconds: int = 600, poll_interval: int = 2):
    """Wait for job to complete."""
    print(f"\nWaiting for job completion (max {max_wait_seconds}s)...")
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait_seconds:
            print(f"✗ Timeout after {max_wait_seconds}s")
            return None
        
        result = get_job_status(job_id)
        
        if not result:
            return None
        
        status = result['status']
        print(f"  [{int(elapsed)}s] Status: {status}")
        
        if status == 'done':
            print("✓ Job completed successfully!")
            return result
        
        elif status == 'error':
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            print(f"✗ Job failed: {error_msg}")
            return result
        
        elif status == 'not_found':
            print("✗ Job not found (may have expired)")
            return None
        
        time.sleep(poll_interval)


def display_result(result: dict):
    """Display extraction result."""
    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    
    if result['status'] == 'done':
        lyrics = result['result']['lyrics']
        meta = result.get('meta', {})
        
        print(f"\nLyrics ({len(lyrics)} characters):")
        print("-" * 60)
        print(lyrics)
        print("-" * 60)
        
        print(f"\nMetadata:")
        print(f"  Duration: {meta.get('duration_sec')}s")
        print(f"  Language: {meta.get('language_detected')}")
        print(f"  Models: {meta.get('model')}")
        
        if result['result'].get('words'):
            print(f"  Word timestamps: {len(result['result']['words'])} words")
    
    elif result['status'] == 'error':
        error = result.get('error', {})
        print(f"\nError Code: {error.get('code')}")
        print(f"Error Message: {error.get('message')}")
    
    print("="*60)


def run_full_test(audio_path: str, language: str = "auto", timestamps: str = "none"):
    """Run complete test."""
    print("="*60)
    print("LYRICS EXTRACTION SERVICE TEST")
    print("="*60)
    
    # Test health
    if not test_health_check():
        print("\n✗ Service is not healthy. Please start the service first.")
        print("\nTo start the service:")
        print("  bash start-lyrics-service.sh")
        print("  OR")
        print("  docker compose -f docker-compose.lyrics.yml up")
        return False
    
    # Submit job
    job_id = submit_job(audio_path, language, timestamps)
    if not job_id:
        return False
    
    # Wait for completion
    result = wait_for_completion(job_id)
    if not result:
        return False
    
    # Display result
    display_result(result)
    
    return result['status'] == 'done'


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test lyrics extraction service")
    parser.add_argument("audio_file", nargs="?", default=TEST_AUDIO_PATH, 
                       help="Path to audio file")
    parser.add_argument("--language", default="auto", 
                       choices=["auto", "en", "vi"],
                       help="Language hint")
    parser.add_argument("--timestamps", default="none",
                       choices=["none", "word"],
                       help="Include word timestamps")
    parser.add_argument("--api-url", default=API_BASE_URL,
                       help="API base URL")
    
    args = parser.parse_args()
    
    # Update global API URL
    global API_BASE_URL
    API_BASE_URL = args.api_url
    
    # Run test
    success = run_full_test(args.audio_file, args.language, args.timestamps)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
