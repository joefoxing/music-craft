"""
Test script to verify Flask app integration with lyrics microservice.
Run this after starting the microservice to test the integration.
"""
import os
import sys

# Set environment to use microservice
os.environ['LYRICS_USE_MICROSERVICE'] = 'true'
os.environ['LYRICS_MICROSERVICE_URL'] = 'http://localhost:8000/v1'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.lyrics_extraction_service import LyricsExtractionService


def test_microservice_integration():
    """Test that Flask app can call the microservice."""
    print("="*60)
    print("Flask App + Lyrics Microservice Integration Test")
    print("="*60)
    
    # Create Flask app
    print("\n1. Creating Flask app context...")
    app = create_app()
    
    with app.app_context():
        print("✓ Flask app created")
        
        # Check config
        use_microservice = app.config.get('LYRICS_USE_MICROSERVICE')
        microservice_url = app.config.get('LYRICS_MICROSERVICE_URL')
        
        print(f"\n2. Configuration:")
        print(f"   USE_MICROSERVICE: {use_microservice}")
        print(f"   MICROSERVICE_URL: {microservice_url}")
        
        if not use_microservice:
            print("\n❌ Microservice mode is not enabled!")
            print("   Set LYRICS_USE_MICROSERVICE=true in your environment")
            return False
        
        # Test with a sample audio file
        audio_file = input("\n3. Enter path to test audio file (or press Enter to skip): ").strip()
        
        if not audio_file:
            print("\n✓ Configuration test passed!")
            print("\nTo test with actual audio:")
            print("  python test_flask_integration.py")
            print("  # Then enter path when prompted")
            return True
        
        if not os.path.exists(audio_file):
            print(f"\n❌ File not found: {audio_file}")
            return False
        
        print(f"\n4. Extracting lyrics from: {audio_file}")
        print("   (This may take several minutes...)")
        
        # Extract lyrics
        service = LyricsExtractionService()
        lyrics, source, error = service.extract_lyrics(local_file_path=audio_file)
        
        if error:
            print(f"\n❌ Extraction failed: {error}")
            return False
        
        if not lyrics:
            print("\n❌ No lyrics extracted")
            return False
        
        print(f"\n✓ Lyrics extracted successfully!")
        print(f"   Source: {source}")
        print(f"   Length: {len(lyrics)} characters")
        print(f"\n   Preview:")
        print("   " + "-"*56)
        preview = lyrics[:500] if len(lyrics) > 500 else lyrics
        for line in preview.split('\n')[:10]:
            print(f"   {line}")
        if len(lyrics) > 500:
            print("   ...")
        print("   " + "-"*56)
        
        return True


def test_microservice_health():
    """Quick health check of the microservice."""
    import requests
    
    url = os.environ.get('LYRICS_MICROSERVICE_URL', 'http://localhost:8000/v1')
    health_url = url.replace('/v1', '') + '/healthz'
    
    print(f"\nChecking microservice health: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Microservice is healthy")
        print(f"  Status: {data.get('status')}")
        print(f"  Redis: {'connected' if data.get('redis_connected') else 'disconnected'}")
        print(f"  Queue size: {data.get('queue_size')}")
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to microservice")
        print(f"   Make sure the service is running:")
        print(f"   bash start-lyrics-service.sh")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Main entry point."""
    print("\nStep 1: Health Check")
    print("-" * 60)
    
    if not test_microservice_health():
        print("\n❌ Test failed: Microservice is not running")
        print("\nTo start the microservice:")
        print("  bash start-lyrics-service.sh")
        print("  OR")
        print("  docker compose -f docker-compose.lyrics.yml up")
        sys.exit(1)
    
    print("\nStep 2: Integration Test")
    print("-" * 60)
    
    success = test_microservice_integration()
    
    if success:
        print("\n" + "="*60)
        print("✓ Integration test PASSED")
        print("="*60)
        print("\nYour Flask app can now use the lyrics microservice!")
        print("\nTo enable in production, set these environment variables:")
        print("  LYRICS_USE_MICROSERVICE=true")
        print("  LYRICS_MICROSERVICE_URL=http://lyrics-api:8000/v1")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Integration test FAILED")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
