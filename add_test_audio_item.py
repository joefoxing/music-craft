#!/usr/bin/env python3
"""
Add a test audio item to the library for testing
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import User, AudioLibrary, db
from datetime import datetime
import uuid

def add_test_audio_item():
    app = create_app()
    
    with app.app_context():
        # Get the test user
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            print("Test user not found!")
            return
        
        print(f"Found user: {user.email}")
        
        # Check if test audio item already exists
        existing_item = AudioLibrary.query.filter_by(
            user_id=user.id,
            title='Test Song'
        ).first()
        
        if existing_item:
            print("Test audio item already exists")
            return
        
        # Create test audio item
        audio_item = AudioLibrary(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title='Test Song',
            artist='Test Artist',
            album='Test Album',
            duration=180,  # 3 minutes
            file_size=5242880,  # 5MB
            genre='Electronic',
            source_type='upload',
            audio_url='/static/uploads/test-song.mp3',
            file_path='/static/uploads/test-song.mp3',
            is_favorite=False,
            play_count=0,
            uploaded_at=datetime.utcnow()
        )
        
        db.session.add(audio_item)
        db.session.commit()
        
        print(f"Added test audio item: {audio_item.title}")
        print(f"Audio item ID: {audio_item.id}")

if __name__ == '__main__':
    add_test_audio_item()