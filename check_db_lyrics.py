#!/usr/bin/env python3
"""Check lyrics stored in database for newlines."""
import os
import sys

sys.path.insert(0, '.')
os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app
app = create_app()

with app.app_context():
    from app.models import AudioLibrary
    
    items = AudioLibrary.query.filter(
        AudioLibrary.lyrics.isnot(None)
    ).order_by(AudioLibrary.id.desc()).limit(5).all()
    
    if not items:
        print("No audio items with lyrics found in database.")
    
    for item in items:
        lyrics = item.lyrics or ""
        newlines = lyrics.count('\n')
        print(f"\n{'='*70}")
        print(f"ID: {item.id}")
        print(f"Status: {item.lyrics_extraction_status}")
        print(f"Source: {item.lyrics_source}")
        print(f"Length: {len(lyrics)} chars")
        print(f"Newlines: {newlines}")
        print(f"\nFirst 300 chars (repr):")
        print(repr(lyrics[:300]))
        print(f"\nFirst 300 chars (display):")
        print(lyrics[:300])
