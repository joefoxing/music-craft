#!/usr/bin/env python3
"""Check lyrics completeness for a specific song."""
from app import create_app
from app.models import AudioLibrary

app = create_app()

with app.app_context():
    song = AudioLibrary.query.filter_by(id='a74e4191-9ac1-4995-98b3-40a76c45210e').first()
    if song:
        print(f'Title: {song.title}')
        print(f'Status: {song.lyrics_extraction_status}')
        print(f'Source: {song.lyrics_source}')
        print(f'Lyrics length: {len(song.lyrics) if song.lyrics else 0} characters')
        print(f'Lyrics line count: {song.lyrics.count(chr(10)) + 1 if song.lyrics else 0} lines')
        print(f'\n--- First 300 chars ---')
        print(song.lyrics[:300] if song.lyrics else 'None')
        print(f'\n--- Last 300 chars ---')
        print(song.lyrics[-300:] if song.lyrics else 'None')
        print(f'\n--- Full lyrics ---')
        print(song.lyrics if song.lyrics else 'None')
    else:
        print('Song not found')
