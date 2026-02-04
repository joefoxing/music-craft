import sys
sys.path.insert(0, '.')

from app import create_app

app = create_app()
with app.app_context():
    print('MAX_CONTENT_LENGTH:', app.config.get('MAX_CONTENT_LENGTH'))
    print('MAX_UPLOAD_SIZE:', app.config.get('MAX_UPLOAD_SIZE'))
    print('UPLOAD_FOLDER:', app.config.get('UPLOAD_FOLDER'))
    # Also check environment variables
    import os
    print('ENV MAX_CONTENT_LENGTH:', os.environ.get('MAX_CONTENT_LENGTH'))
    print('ENV MAX_UPLOAD_SIZE:', os.environ.get('MAX_UPLOAD_SIZE'))
    # Calculate MB
    max_content = app.config.get('MAX_CONTENT_LENGTH')
    if max_content:
        print('MAX_CONTENT_LENGTH (MB):', max_content / (1024 * 1024))
    max_upload = app.config.get('MAX_UPLOAD_SIZE')
    if max_upload:
        print('MAX_UPLOAD_SIZE (MB):', max_upload / (1024 * 1024))