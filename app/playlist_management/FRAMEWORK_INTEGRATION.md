# Framework Integration Guide

This guide demonstrates how to integrate the Playlist Management System with various Python frameworks and applications.

## Table of Contents

- [Flask Integration](#flask-integration)
- [Django Integration](#django-integration)
- [FastAPI Integration](#fastapi-integration)
- [Command Line Interface](#command-line-interface)
- [Desktop Applications](#desktop-applications)
- [Mobile Backends](#mobile-backends)
- [Microservices](#microservices)

## Flask Integration

### Basic Flask Setup

```python
# app.py
from flask import Flask, jsonify, request, render_template
from app.playlist_management import create_playlist_manager, create_song
import os

app = Flask(__name__)

# Initialize playlist manager
manager = create_playlist_manager(
    storage_type='file',
    storage_dir=os.environ.get('PLAYLIST_DATA_DIR', 'playlist_data')
)

@app.route('/')
def index():
    return render_template('playlists.html')

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all playlists."""
    try:
        playlists = manager.list_playlists(
            include_public=request.args.get('include_public', 'true').lower() == 'true',
            sort_by=request.args.get('sort_by', 'name')
        )
        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in playlists]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    """Create a new playlist."""
    try:
        data = request.get_json()
        playlist = manager.create_playlist(**data)
        return jsonify({
            'success': True,
            'data': playlist.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    """Get a specific playlist."""
    try:
        playlist = manager.get_playlist(playlist_id)
        if playlist:
            return jsonify({
                'success': True,
                'data': playlist.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Playlist not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists/<playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    """Update a playlist."""
    try:
        data = request.get_json()
        result = manager.update_playlist(playlist_id, **data)
        if result:
            return jsonify({
                'success': True,
                'message': 'Playlist updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Playlist not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a playlist."""
    try:
        result = manager.delete_playlist(playlist_id)
        if result:
            return jsonify({
                'success': True,
                'message': 'Playlist deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Playlist not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists/<playlist_id>/songs', methods=['POST'])
def add_song_to_playlist(playlist_id):
    """Add a song to a playlist."""
    try:
        data = request.get_json()
        song = create_song(**data)
        result = manager.add_song_to_playlist(playlist_id, song)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Song added successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add song (playlist may not exist or song may be duplicate)'
            }), 400
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid song data: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['GET'])
def search():
    """Search songs across playlists."""
    try:
        query = request.args.get('q', '')
        playlist_ids = request.args.getlist('playlist_ids')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        results = manager.search_songs_across_playlists(query, playlist_ids)
        
        return jsonify({
            'success': True,
            'data': {
                playlist_id: [song.to_dict() for song in songs]
                for playlist_id, songs in results.items()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get playlist statistics."""
    try:
        stats = manager.get_playlist_statistics()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Flask Blueprint for Organization

```python
# api/playlists.py
from flask import Blueprint, jsonify, request
from app.playlist_management import create_playlist_manager, create_song

playlists_bp = Blueprint('playlists', __name__)
manager = create_playlist_manager()

@playlists_bp.route('/playlists', methods=['GET'])
def list_playlists():
    playlists = manager.list_playlists()
    return jsonify([p.to_dict() for p in playlists])

@playlists_bp.route('/playlists', methods=['POST'])
def create_playlist():
    data = request.json
    playlist = manager.create_playlist(**data)
    return jsonify(playlist.to_dict()), 201

# main.py
from flask import Flask
from api.playlists import playlists_bp

app = Flask(__name__)
app.register_blueprint(playlists_bp, url_prefix='/api')
```

## Django Integration

### Django Models and Views

```python
# models.py
from django.db import models
from app.playlist_management import create_playlist_manager
import json

class Playlist(models.Model):
    playlist_id = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_playlist_object(self):
        """Convert Django model to Playlist object."""
        # This would require loading the actual playlist data
        # Implementation depends on how you store playlist data
        pass

class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song_data = models.JSONField()  # Store song as JSON
    
    def to_song_object(self):
        """Convert to Song object."""
        from app.playlist_management.song import Song
        return Song.from_dict(self.song_data)

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET"])
def playlist_list(request):
    """List all playlists."""
    manager = create_playlist_manager()
    playlists = manager.list_playlists()
    
    return JsonResponse({
        'playlists': [p.to_dict() for p in playlists]
    })

@csrf_exempt
@require_http_methods(["POST"])
def playlist_create(request):
    """Create a new playlist."""
    try:
        data = json.loads(request.body)
        manager = create_playlist_manager()
        playlist = manager.create_playlist(**data)
        
        # Save to Django database as well
        Playlist.objects.create(
            playlist_id=playlist.playlist_id,
            name=playlist.metadata.name,
            description=playlist.metadata.description,
            tags=playlist.metadata.tags,
            is_public=playlist.metadata.is_public
        )
        
        return JsonResponse({
            'success': True,
            'playlist': playlist.to_dict()
        }, status=201)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def add_song_to_playlist(request, playlist_id):
    """Add a song to a playlist."""
    try:
        data = json.loads(request.body)
        manager = create_playlist_manager()
        
        song = create_song(**data)
        result = manager.add_song_to_playlist(playlist_id, song)
        
        if result:
            # Save to Django database
            playlist = Playlist.objects.get(playlist_id=playlist_id)
            PlaylistSong.objects.create(
                playlist=playlist,
                song_data=song.to_dict()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Song added successfully'
            }, status=201)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to add song'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```

### Django REST Framework Integration

```python
# serializers.py
from rest_framework import serializers
from app.playlist_management import create_song, create_playlist

class SongSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    artist = serializers.CharField(max_length=255)
    album = serializers.CharField(max_length=255, required=False, allow_blank=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    genre = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def create(self, validated_data):
        return create_song(**validated_data)

class PlaylistSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    is_public = serializers.BooleanField(default=False)

    def create(self, validated_data):
        manager = create_playlist_manager()
        return manager.create_playlist(**validated_data)

# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import PlaylistSerializer, SongSerializer

class PlaylistViewSet(viewsets.ViewSet):
    def list(self, request):
        manager = create_playlist_manager()
        playlists = manager.list_playlists()
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = PlaylistSerializer(data=request.data)
        if serializer.is_valid():
            playlist = serializer.save()
            return Response(PlaylistSerializer(playlist).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_song(self, request, pk=None):
        song_serializer = SongSerializer(data=request.data)
        if song_serializer.is_valid():
            song = song_serializer.save()
            manager = create_playlist_manager()
            result = manager.add_song_to_playlist(pk, song)
            
            if result:
                return Response({'message': 'Song added successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Failed to add song'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(song_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## FastAPI Integration

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.playlist_management import create_playlist_manager, create_song

app = FastAPI(title="Playlist Management API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get manager
def get_playlist_manager():
    return create_playlist_manager()

# Pydantic models
class SongCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    duration: Optional[int] = Field(None, gt=0)
    genre: Optional[str] = Field(None, max_length=100)

class SongResponse(BaseModel):
    song_id: str
    title: str
    artist: str
    album: Optional[str]
    duration: Optional[int]
    genre: Optional[str]
    duration_formatted: str
    display_name: str

class PlaylistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = []
    is_public: bool = False

class PlaylistResponse(BaseModel):
    playlist_id: str
    name: str
    description: str
    tags: List[str]
    is_public: bool
    song_count: int
    total_duration_formatted: str
    songs: List[SongResponse]

@app.get("/playlists", response_model=List[PlaylistResponse])
async def list_playlists(manager: create_playlist_manager = Depends(get_playlist_manager)):
    """Get all playlists."""
    playlists = manager.list_playlists()
    return [PlaylistResponse(**p.to_dict()) for p in playlists]

@app.post("/playlists", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    playlist_data: PlaylistCreate,
    manager: create_playlist_manager = Depends(get_playlist_manager)
):
    """Create a new playlist."""
    try:
        playlist = manager.create_playlist(**playlist_data.dict())
        return PlaylistResponse(**playlist.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/playlists/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str,
    manager: create_playlist_manager = Depends(get_playlist_manager)
):
    """Get a specific playlist."""
    playlist = manager.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return PlaylistResponse(**playlist.to_dict())

@app.post("/playlists/{playlist_id}/songs", status_code=201)
async def add_song_to_playlist(
    playlist_id: str,
    song_data: SongCreate,
    manager: create_playlist_manager = Depends(get_playlist_manager)
):
    """Add a song to a playlist."""
    try:
        song = create_song(**song_data.dict())
        result = manager.add_song_to_playlist(playlist_id, song)
        
        if result:
            return {"message": "Song added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add song")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid song data: {str(e)}")

@app.get("/search")
async def search_songs(
    query: str,
    playlist_ids: Optional[List[str]] = None,
    manager: create_playlist_manager = Depends(get_playlist_manager)
):
    """Search songs across playlists."""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    
    results = manager.search_songs_across_playlists(query, playlist_ids)
    return {
        "query": query,
        "results": {
            pid: [SongResponse(**song.to_dict()).dict() for song in songs]
            for pid, songs in results.items()
        }
    }

@app.get("/statistics")
async def get_statistics(manager: create_playlist_manager = Depends(get_playlist_manager)):
    """Get playlist statistics."""
    return manager.get_playlist_statistics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Command Line Interface

```python
# cli.py
import click
from app.playlist_management import create_playlist_manager, create_song, create_playlist

@click.group()
@click.pass_context
def cli(ctx):
    """Playlist Management CLI"""
    ctx.ensure_object(dict)
    ctx.obj['manager'] = create_playlist_manager()

@cli.command()
@click.pass_context
def list(ctx):
    """List all playlists"""
    manager = ctx.obj['manager']
    playlists = manager.list_playlists()
    
    for playlist in playlists:
        click.echo(f"{playlist.metadata.name} ({len(playlist)} songs)")
        if playlist.metadata.description:
            click.echo(f"  Description: {playlist.metadata.description}")

@cli.command()
@click.pass_context
def create(ctx, name, description, public):
    """Create a new playlist"""
    manager = ctx.obj['manager']
    try:
        playlist = manager.create_playlist(
            name=name,
            description=description or "",
            is_public=public
        )
        click.echo(f"Created playlist: {playlist.metadata.name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.pass_context
def add_song(ctx, playlist_name, title, artist, album, duration, genre):
    """Add a song to a playlist"""
    manager = ctx.obj['manager']
    
    # Find playlist by name
    playlist = manager.get_playlist_by_name(playlist_name)
    if not playlist:
        click.echo(f"Playlist '{playlist_name}' not found", err=True)
        return
    
    try:
        song = create_song(
            title=title,
            artist=artist,
            album=album,
            duration=int(duration) if duration else None,
            genre=genre
        )
        
        result = manager.add_song_to_playlist(playlist.playlist_id, song)
        if result:
            click.echo(f"Added song: {song.display_name}")
        else:
            click.echo("Failed to add song", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.pass_context
def search(ctx, query):
    """Search songs across all playlists"""
    manager = ctx.obj['manager']
    results = manager.search_songs_across_playlists(query)
    
    if not results:
        click.echo("No songs found")
        return
    
    for playlist_id, songs in results.items():
        playlist = manager.get_playlist(playlist_id)
        click.echo(f"\nPlaylist: {playlist.metadata.name}")
        for song in songs:
            click.echo(f"  - {song.display_name}")

@cli.command()
@click.pass_context
def stats(ctx):
    """Show playlist statistics"""
    manager = ctx.obj['manager']
    stats = manager.get_playlist_statistics()
    
    click.echo(f"Total Playlists: {stats['total_playlists']}")
    click.echo(f"Total Songs: {stats['total_songs']}")
    click.echo(f"Unique Songs: {stats['total_unique_songs']}")
    click.echo(f"Average Songs per Playlist: {stats['average_songs_per_playlist']:.1f}")

# Add parameters
create.add_argument('--name', required=True)
create.add_argument('--description')
create.add_argument('--public', is_flag=True)

add_song.add_argument('--playlist-name', required=True)
add_song.add_argument('--title', required=True)
add_song.add_argument('--artist', required=True)
add_song.add_argument('--album')
add_song.add_argument('--duration', type=int)
add_song.add_argument('--genre')

search.add_argument('--query', required=True)

if __name__ == '__main__':
    cli()
```

## Desktop Applications

### Tkinter Integration

```python
# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.playlist_management import create_playlist_manager, create_song

class PlaylistGUI:
    def __init__(self):
        self.manager = create_playlist_manager()
        self.window = tk.Tk()
        self.window.title("Playlist Manager")
        self.window.geometry("800x600")
        
        self.setup_ui()
        self.refresh_playlists()
    
    def setup_ui(self):
        # Playlist list
        self.playlist_frame = ttk.LabelFrame(self.window, text="Playlists")
        self.playlist_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.playlist_tree = ttk.Treeview(self.playlist_frame, columns=('songs', 'duration'))
        self.playlist_tree.heading('#0', text='Name')
        self.playlist_tree.heading('songs', text='Songs')
        self.playlist_tree.heading('duration', text='Duration')
        self.playlist_tree.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="New Playlist", command=self.create_playlist_dialog).pack(side='left')
        ttk.Button(button_frame, text="Add Song", command=self.add_song_dialog).pack(side='left')
        ttk.Button(button_frame, text="Refresh", command=self.refresh_playlists).pack(side='left')
    
    def create_playlist_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Playlist")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Name:").pack()
        name_entry = ttk.Entry(dialog)
        name_entry.pack()
        
        ttk.Label(dialog, text="Description:").pack()
        desc_entry = ttk.Entry(dialog)
        desc_entry.pack()
        
        def create():
            try:
                self.manager.create_playlist(
                    name=name_entry.get(),
                    description=desc_entry.get()
                )
                self.refresh_playlists()
                dialog.destroy()
                messagebox.showinfo("Success", "Playlist created successfully")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Create", command=create).pack(pady=10)
    
    def add_song_dialog(self):
        selected = self.playlist_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a playlist first")
            return
        
        playlist_id = self.playlist_tree.item(selected[0])['values'][2]  # Assuming playlist_id is stored
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Song")
        dialog.geometry("300x250")
        
        ttk.Label(dialog, text="Title:").pack()
        title_entry = ttk.Entry(dialog)
        title_entry.pack()
        
        ttk.Label(dialog, text="Artist:").pack()
        artist_entry = ttk.Entry(dialog)
        artist_entry.pack()
        
        ttk.Label(dialog, text="Album:").pack()
        album_entry = ttk.Entry(dialog)
        album_entry.pack()
        
        def add():
            try:
                song = create_song(
                    title=title_entry.get(),
                    artist=artist_entry.get(),
                    album=album_entry.get() or None
                )
                result = self.manager.add_song_to_playlist(playlist_id, song)
                if result:
                    self.refresh_playlists()
                    dialog.destroy()
                    messagebox.showinfo("Success", "Song added successfully")
                else:
                    messagebox.showerror("Error", "Failed to add song")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Add", command=add).pack(pady=10)
    
    def refresh_playlists(self):
        # Clear existing items
        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)
        
        # Add playlists
        playlists = self.manager.list_playlists()
        for playlist in playlists:
            self.playlist_tree.insert(
                '', 'end',
                text=playlist.metadata.name,
                values=(len(playlist), playlist.get_total_duration_formatted(), playlist.playlist_id)
            )
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = PlaylistGUI()
    app.run()
```

## Mobile Backends

### Flask-RESTful for Mobile Apps

```python
# mobile_api.py
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from app.playlist_management import create_playlist_manager, create_song
import jwt
import datetime

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'your-secret-key'

manager = create_playlist_manager()

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

class Auth(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Simple authentication (replace with proper auth)
        if username == 'admin' and password == 'password':
            token = jwt.encode({
                'user': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return {'token': token}
        else:
            return {'error': 'Invalid credentials'}, 401

class MobilePlaylists(Resource):
    @token_required
    def get(self):
        """Get playlists for mobile app."""
        include_public = request.args.get('include_public', 'true').lower() == 'true'
        playlists = manager.list_playlists(include_public=include_public)
        
        # Simplified response for mobile
        return [{
            'id': p.playlist_id,
            'name': p.metadata.name,
            'description': p.metadata.description,
            'songCount': len(p),
            'duration': p.get_total_duration(),
            'isPublic': p.metadata.is_public,
            'coverImage': p.metadata.cover_image_url
        } for p in playlists]
    
    @token_required
    def post(self):
        """Create playlist from mobile app."""
        data = request.get_json()
        try:
            playlist = manager.create_playlist(**data)
            return {
                'id': playlist.playlist_id,
                'name': playlist.metadata.name
            }, 201
        except Exception as e:
            return {'error': str(e)}, 400

class MobilePlaylistDetail(Resource):
    @token_required
    def get(self, playlist_id):
        """Get playlist details for mobile app."""
        playlist = manager.get_playlist(playlist_id)
        if not playlist:
            return {'error': 'Playlist not found'}, 404
        
        return {
            'id': playlist.playlist_id,
            'name': playlist.metadata.name,
            'description': playlist.metadata.description,
            'songs': [{
                'id': song.song_id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'duration': song.duration,
                'genre': song.genre
            } for song in playlist.read_songs()]
        }
    
    @token_required
    def post(self, playlist_id):
        """Add song to playlist from mobile app."""
        data = request.get_json()
        try:
            song = create_song(**data)
            result = manager.add_song_to_playlist(playlist_id, song)
            return {'success': result}, 201 if result else 400
        except Exception as e:
            return {'error': str(e)}, 400

# Register resources
api.add_resource(Auth, '/auth')
api.add_resource(MobilePlaylists, '/mobile/playlists')
api.add_resource(MobilePlaylistDetail, '/mobile/playlists/<playlist_id>')

if __name__ == '__main__':
    app.run(debug=True)
```

## Microservices

### AsyncIO with Custom Storage

```python
# microservice.py
import asyncio
import aiofiles
import json
from typing import Dict, Any, List, Optional
from app.playlist_management.storage import StorageInterface
from app.playlist_management.playlist import Playlist

class AsyncFileStorage(StorageInterface):
    """Asynchronous file storage implementation."""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self._lock = asyncio.Lock()
    
    async def save_playlist(self, playlist: Playlist) -> bool:
        async with self._lock:
            try:
                file_path = f"{self.storage_dir}/{playlist.playlist_id}.json"
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(json.dumps(playlist.to_dict()))
                return True
            except Exception:
                return False
    
    async def load_playlist(self, playlist_id: str) -> Optional[Playlist]:
        try:
            file_path = f"{self.storage_dir}/{playlist_id}.json"
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            return Playlist.from_dict(data)
        except Exception:
            return None
    
    async def delete_playlist(self, playlist_id: str) -> bool:
        import os
        async with self._lock:
            try:
                file_path = f"{self.storage_dir}/{playlist_id}.json"
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            except Exception:
                return False
    
    async def list_all_playlists(self) -> List[Playlist]:
        import os
        playlists = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    playlist_id = filename[:-5]
                    playlist = await self.load_playlist(playlist_id)
                    if playlist:
                        playlists.append(playlist)
        except Exception:
            pass
        return playlists
    
    async def playlist_exists(self, playlist_id: str) -> bool:
        import os
        file_path = f"{self.storage_dir}/{playlist_id}.json"
        return os.path.exists(file_path)
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        # Implementation for async stats
        return {
            'type': 'async_file',
            'storage_directory': self.storage_dir
        }

# Async playlist service
class AsyncPlaylistService:
    def __init__(self, storage: AsyncFileStorage):
        self.storage = storage
    
    async def create_playlist(self, name: str, **kwargs) -> Playlist:
        playlist = Playlist(name=name, **kwargs)
        await self.storage.save_playlist(playlist)
        return playlist
    
    async def get_playlists(self) -> List[Playlist]:
        return await self.storage.list_all_playlists()
    
    async def add_song_to_playlist(self, playlist_id: str, song) -> bool:
        playlist = await self.storage.load_playlist(playlist_id)
        if not playlist:
            return False
        
        try:
            playlist.create_song(song)
            await self.storage.save_playlist(playlist)
            return True
        except:
            return False

# Usage with FastAPI
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()
storage = AsyncFileStorage("async_playlist_data")
service = AsyncPlaylistService(storage)

@app.get("/playlists")
async def list_playlists():
    playlists = await service.get_playlists()
    return JSONResponse([p.to_dict() for p in playlists])

@app.post("/playlists")
async def create_playlist_endpoint(data: dict):
    playlist = await service.create_playlist(**data)
    return JSONResponse(playlist.to_dict())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This comprehensive framework integration guide demonstrates how the Playlist Management System can be adapted to various Python frameworks and application types while maintaining clean separation of concerns and framework-agnostic design.