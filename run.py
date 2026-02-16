#!/usr/bin/env python3
"""
Music Cover Generator - Main Application Entry Point
Uses Kie API to generate music covers from uploaded audio files.

Version: 1.0.0
Release Date: January 11, 2026
"""

import os
import atexit
from app import create_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"""
    ============================================
    Music Cover Generator v1.0.0
    ============================================
    Starting server...
    Host: {host}
    Port: {port}
    Debug: {debug}
    
    Endpoints:
    - Web Interface: http://{host}:{port}/
    - File Upload: http://{host}:{port}/upload
    - Generate Cover: http://{host}:{port}/api/generate-cover
    - Task Status: http://{host}:{port}/api/task-status/<task_id>
    - Callback: http://{host}:{port}/callback
    
    Note: Make sure to set KIE_API_KEY environment variable
    ============================================
    """)
    
    app.run(host=host, port=port, debug=debug)