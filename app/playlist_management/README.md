# Playlist Management System

A comprehensive, framework-agnostic playlist management module with modular architecture, comprehensive CRUD operations, and clean separation of concerns.

## Features

- **Modular Architecture**: Separate classes for Song, Playlist, PlaylistManager, and Storage
- **Full CRUD Operations**: Complete Create, Read, Update, Delete functionality for playlists and songs
- **Advanced Search & Filtering**: Search songs and playlists by various criteria
- **Metadata Management**: Comprehensive handling of song and playlist metadata
- **Duplicate Prevention**: Built-in validation to prevent duplicate songs in playlists
- **Dependency Injection**: Flexible storage layer with multiple implementations
- **Framework Agnostic**: Can be integrated into any Python application
- **Comprehensive Testing**: Full unit test coverage for all components
- **Error Handling**: Robust error handling with custom exceptions
- **Data Persistence**: Multiple storage options (memory, file, database-ready)

## Quick Start

### Installation

```bash
# Copy the playlist_management module to your project
cp -r app/playlist_management /path/to/your/project/
```

### Basic Usage

```python
from app.playlist_management import create_playlist_manager, create_song

# Create a playlist manager with in-memory storage
manager = create_playlist_manager(storage_type='memory')

# Create a playlist
playlist = manager.create_playlist(
    name="My Favorites",
    description="My favorite songs",
    tags=['rock', 'favorites'],
    is_public=True
)

# Create a song
song = create_song(
    title="Bohemian Rhapsody",
    artist="Queen",
    album="A Night at the Opera",
    duration=355,
    genre="Rock"
)

# Add song to playlist
manager.add_song_to_playlist(playlist.playlist_id, song)

# Search for songs
results = manager.search_songs_across_playlists("Queen")
for playlist_id, songs in results.items():
    for song in songs:
        print(f"Found: {song.display_name}")
```

## Architecture

### Core Components

1. **Song Class** (`song.py`)
   - Represents individual songs with metadata
   - Supports title, artist, album, duration, genre, and custom metadata
   - Provides validation and formatting utilities

2. **Playlist Class** (`playlist.py`)
   - Manages collections of songs
   - Full CRUD operations for songs within playlists
   - Metadata management and search functionality

3. **PlaylistManager Class** (`playlist_manager.py`)
   - High-level business logic coordination
   - Cross-playlist operations
   - Search and analytics functionality

4. **Storage Layer** (`storage.py`)
   - Abstract storage interface
   - Multiple implementations (InMemory, File, Database)
   - Dependency injection support

### Design Patterns

- **Dependency Injection**: Storage layer is injected, allowing different backends
- **Factory Pattern**: Convenience functions for easy object creation
- **Strategy Pattern**: Different storage strategies can be swapped
- **Observer Pattern**: Metadata updates track modification times

## API Reference

### Song Class

#### Constructor
```python
Song(title: str, artist: str, album: Optional[str] = None, 
     duration: Optional[int] = None, genre: Optional[str] = None,
     file_path: Optional[str] = None, file_url: Optional[str] = None)
```

#### Properties
- `duration_formatted`: Returns duration in MM:SS format
- `display_name`: Returns "Artist - Title" format
- `song_id`: Unique identifier for the song

#### Methods
- `update_metadata(**kwargs)`: Update song metadata
- `to_dict()`: Serialize to dictionary
- `from_dict(data)`: Create from dictionary

### Playlist Class

#### Constructor
```python
Playlist(name: str, description: str = "", playlist_id: Optional[str] = None,
         creation_date: Optional[datetime] = None, tags: Optional[List[str]] = None,
         cover_image_url: Optional[str] = None, is_public: bool = False)
```

#### Song Management (CRUD)
- `create_song(song)`: Add song to playlist
- `read_songs(start_index=0, end_index=None)`: Retrieve songs
- `update_song(old_song, new_data)`: Update existing song
- `delete_song(song)`: Remove song from playlist

#### Utility Methods
- `search_songs(query)`: Search songs by title, artist, album, or genre
- `filter_songs_by_genre(genre)`: Filter songs by genre
- `filter_songs_by_artist(artist)`: Filter songs by artist
- `reorder_songs(new_order)`: Reorder songs in playlist
- `shuffle_songs()`: Randomly shuffle songs

### PlaylistManager Class

#### Playlist Operations
- `create_playlist(name, description, **kwargs)`: Create new playlist
- `get_playlist(playlist_id)`: Retrieve playlist by ID
- `update_playlist(playlist_id, **kwargs)`: Update playlist metadata
- `delete_playlist(playlist_id)`: Delete playlist
- `list_playlists(**kwargs)`: List all playlists with filtering

#### Cross-Playlist Operations
- `add_song_to_playlist(playlist_id, song)`: Add song to playlist
- `remove_song_from_playlist(playlist_id, song)`: Remove song from playlist
- `move_song_between_playlists(source_id, target_id, song)`: Move song between playlists

#### Search & Analytics
- `search_playlists(query)`: Search playlists by name, description, or tags
- `search_songs_across_playlists(query, playlist_ids)`: Search songs across playlists
- `get_duplicate_songs()`: Find songs appearing in multiple playlists
- `get_playlist_statistics()`: Get comprehensive statistics

### Storage Implementations

#### InMemoryStorage
```python
storage = InMemoryStorage()
manager = PlaylistManager(storage)
```

#### FileStorage
```python
storage = FileStorage(storage_dir="playlist_data")
manager = PlaylistManager(storage)
```

#### DatabaseStorage (Template)
```python
storage = DatabaseStorage(connection_string="sqlite:///app.db")
manager = PlaylistManager(storage)
```

## Error Handling

### Custom Exceptions

- `DuplicateSongError`: Raised when attempting to add duplicate song to playlist
- `PlaylistExistsError`: Raised when creating playlist with existing name

### Validation

All classes include comprehensive validation:
- Empty title/artist validation for songs
- Empty name validation for playlists
- Duration must be positive
- Genre and metadata validation

## Testing

Run the comprehensive test suite:

```bash
cd app/playlist_management/tests
python -m unittest discover
```

### Test Coverage

- **Song Class**: 100% coverage including validation, serialization, and utility methods
- **Playlist Class**: Full CRUD operations, search, filtering, and metadata management
- **PlaylistManager**: Business logic, cross-playlist operations, and analytics
- **Storage Classes**: All storage implementations and their features

## Advanced Usage

### Custom Storage Implementation

```python
from app.playlist_management.storage import StorageInterface

class CustomStorage(StorageInterface):
    def save_playlist(self, playlist):
        # Implement your custom save logic
        pass
    
    def load_playlist(self, playlist_id):
        # Implement your custom load logic
        pass
    
    # Implement all other abstract methods...

# Use custom storage
storage = CustomStorage()
manager = PlaylistManager(storage)
```

### Batch Operations

```python
# Create multiple playlists
playlists = []
for i in range(10):
    playlist = manager.create_playlist(f"Playlist {i}")
    playlists.append(playlist)

# Add songs to all playlists
for playlist in playlists:
    for song in song_library:
        manager.add_song_to_playlist(playlist.playlist_id, song)
```

### Data Migration

```python
# Backup to file storage
manager = create_playlist_manager(storage_type='memory')
# ... add playlists and songs ...

# Export all data
storage = manager.storage
backup_data = storage.backup_to_dict()

# Restore to file storage
file_manager = create_playlist_manager(storage_type='file')
file_manager.storage.restore_from_backup(backup_data)
```

## Performance Considerations

- **Memory Usage**: InMemoryStorage loads all data into memory
- **File I/O**: FileStorage performs I/O operations for each playlist
- **Caching**: PlaylistManager includes optional caching for frequently accessed playlists
- **Search Performance**: Large datasets may benefit from database storage

## Security Considerations

- **Input Validation**: All inputs are validated before processing
- **File Paths**: FileStorage prevents path traversal attacks
- **Data Integrity**: All operations include error handling and validation

## Integration Examples

### Flask Integration

```python
from flask import Flask, jsonify, request
from app.playlist_management import create_playlist_manager

app = Flask(__name__)
manager = create_playlist_manager(storage_type='file')

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    playlists = manager.list_playlists()
    return jsonify([p.to_dict() for p in playlists])

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    data = request.json
    playlist = manager.create_playlist(**data)
    return jsonify(playlist.to_dict()), 201
```

### Django Integration

```python
from django.http import JsonResponse
from app.playlist_management import create_playlist_manager

manager = create_playlist_manager(storage_type='database')

def playlist_list(request):
    playlists = manager.list_playlists()
    return JsonResponse([p.to_dict() for p in playlists], safe=False)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Ensure all tests pass
5. Submit a pull request

## License

This module is provided as-is for educational and development purposes.

## Support

For issues, questions, or contributions, please refer to the project's main repository.