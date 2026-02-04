#!/usr/bin/env python3
"""
Create a test user for debugging the song library issue
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            print(f"User already exists: {existing_user.email}")
            return existing_user
        
        # Create new user
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash=generate_password_hash('password123'),
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Created test user: {user.email}")
        return user

if __name__ == '__main__':
    create_test_user()