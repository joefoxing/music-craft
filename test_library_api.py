from app import create_app
from app.services.audio_library_service import AudioLibraryService
from app.models import User
from flask_login import login_user

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='joefoxing@gmail.com').first()
    
    with app.test_request_context():
        login_user(user)
        
        service = AudioLibraryService()
        songs, total = service.get_user_audio_library(page=1, per_page=5, sort_by='created_at', sort_order='desc')
        
        print(f'Total songs: {total}')
        print(f'\nFirst 5 songs:\n')
        for i, song in enumerate(songs, 1):
            print(f'{i}. {song.title[:50]}')
            print(f'   ID: {song.id}')
            print(f'   created_at: {song.created_at}')
            print(f'   Status: {song.lyrics_extraction_status}')
            print()
