# API Documentation - Playlist Management System

This document provides detailed API reference for all classes and methods in the Playlist Management System.

## Table of Contents

- [Core Classes](#core-classes)
- [Storage Classes](#storage-classes)
- [Exceptions](#exceptions)
- [Factory Functions](#factory-functions)
- [Enumerations](#enumerations)

## Core Classes

### Song Class

Represents an individual song with comprehensive metadata management.

```python
class Song:
    def __init__(self, 
                 title: str, 
                 artist: str, 
                 album: Optional[str] = None,
                 duration: Optional[int] = None,
                 genre: Optional[str] = None,
                 file_path: Optional[str] = None,
                 file_url: Optional[str] = None,
                 song_id: str = None,
                 creation_date: datetime = None,
                 metadata: Dict[str, Any] = None)
```

#### Parameters

- `title` (str): Song title (required, non-empty)
- `artist` (str): Artist name (required, non-empty)
- `album` (Optional[str]): Album name
- `duration` (Optional[int]): Duration in seconds (must be positive if provided)
- `genre` (Optional[str]): Music genre
- `file_path` (Optional[str]): Local file path to audio file
- `file_url` (Optional[str]): URL to audio file
- `song_id` (str): Unique identifier (auto-generated if not provided)
- `creation_date` (datetime): Creation timestamp (auto-generated if not provided)
- `metadata` (Dict[str, Any]): Custom metadata dictionary

#### Properties

- `duration_formatted` (str): Duration formatted as MM:SS
- `display_name` (str): Display name in "Artist - Title" format
- `song_id` (str): Unique song identifier
- `creation_date` (datetime): Song creation timestamp

#### Methods

##### `update_metadata(**kwargs) -> None`

Update song metadata fields.

**Parameters:**
- `**kwargs`: Metadata fields to update

**Raises:**
- `ValueError`: If updating built-in attributes with invalid data

**Example:**
```python
song.update_metadata(duration=240, genre='Jazz')
```

##### `to_dict() -> Dict[str, Any]`

Convert song to dictionary representation.

**Returns:**
- Dictionary containing all song data

**Example:**
```python
data = song.to_dict()
# Returns: {
#     'song_id': 'uuid-string',
#     'title': 'Song Title',
#     'artist': 'Artist Name',
#     'album': 'Album Name',
#     'duration': 180,
#     'duration_formatted': '03:00',
#     'genre': 'Rock',
#     'file_path': '/path/to/song.mp3',
#     'file_url': None,
#     'creation_date': '2023-01-01T00:00:00',
#     'metadata': {}
# }
```

##### `from_dict(data: Dict[str, Any]) -> Song`

Create song from dictionary representation.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary containing song data

**Returns:**
- New Song instance

**Raises:**
- `ValueError`: If required fields are missing or invalid

#### Magic Methods

- `__str__()`: Returns `display_name`
- `__repr__()`: Returns detailed string representation
- `__eq__(other)`: Equality based on `song_id`
- `__hash__()`: Hash based on `song_id`

### Playlist Class

Manages collections of songs with full CRUD operations and metadata.

```python
class Playlist:
    def __init__(self, 
                 name: str,
                 description: str = "",
                 playlist_id: Optional[str] = None,
                 creation_date: Optional[datetime] = None,
                 tags: Optional[List[str]] = None,
                 cover_image_url: Optional[str] = None,
                 is_public: bool = False)
```

#### Parameters

- `name` (str): Playlist name (required, non-empty)
- `description` (str): Playlist description
- `playlist_id` (str): Unique identifier (auto-generated if not provided)
- `creation_date` (datetime): Creation timestamp (auto-generated if not provided)
- `tags` (List[str]): List of playlist tags
- `cover_image_url` (Optional[str]): URL to playlist cover image
- `is_public` (bool): Whether playlist is publicly visible

#### Properties

- `playlist_id` (str): Unique playlist identifier
- `creation_date` (datetime): Playlist creation timestamp
- `modification_date` (datetime): Last modification timestamp

#### CRUD Operations

##### `create_song(song: Song) -> None`

Add a song to the playlist.

**Parameters:**
- `song` (Song): Song object to add

**Raises:**
- `ValueError`: If song data is invalid
- `DuplicateSongError`: If song already exists in playlist

**Example:**
```python
playlist.create_song(song)
```

##### `read_songs(start_index: int = 0, end_index: Optional[int] = None) -> List[Song]`

Retrieve songs from the playlist.

**Parameters:**
- `start_index` (int): Starting index (default: 0)
- `end_index` (Optional[int]): Ending index (default: None for all remaining)

**Returns:**
- List of songs in the specified range

**Example:**
```python
# Get all songs
all_songs = playlist.read_songs()

# Get songs from index 2 to 5
subset = playlist.read_songs(2, 5)

# Get songs from index 3 onwards
from_index = playlist.read_songs(3)
```

##### `update_song(old_song: Song, new_data: Dict[str, Any]) -> None`

Update an existing song in the playlist.

**Parameters:**
- `old_song` (Song): Song to update
- `new_data` (Dict[str, Any]): Dictionary containing updated song data

**Raises:**
- `ValueError`: If song not found or updated data is invalid

**Example:**
```python
playlist.update_song(song, {
    'title': 'New Title',
    'duration': 200,
    'genre': 'Alternative'
})
```

##### `delete_song(song: Union[Song, str]) -> bool`

Remove a song from the playlist.

**Parameters:**
- `song` (Union[Song, str]): Song object or song ID to remove

**Returns:**
- bool: True if song was found and removed

**Example:**
```python
# Delete by object
result = playlist.delete_song(song)

# Delete by ID
result = playlist.delete_song(song.song_id)
```

#### Metadata Operations

##### `update_metadata(**kwargs) -> None`

Update playlist metadata.

**Parameters:**
- `**kwargs`: Metadata fields to update

**Raises:**
- `ValueError`: If playlist name is set to empty string

**Example:**
```python
playlist.update_metadata(
    name='New Playlist Name',
    description='Updated description',
    tags=['rock', 'favorites'],
    is_public=True
)
```

#### Utility Methods

##### `get_song_by_id(song_id: str) -> Optional[Song]`

Get a song by its ID.

**Parameters:**
- `song_id` (str): ID of the song to retrieve

**Returns:**
- Optional[Song]: Song object if found, None otherwise

##### `get_song_count() -> int`

Get total number of songs in playlist.

**Returns:**
- int: Number of songs

##### `get_total_duration() -> int`

Get total duration of all songs in playlist.

**Returns:**
- int: Total duration in seconds

##### `get_total_duration_formatted() -> str`

Get formatted total duration.

**Returns:**
- str: Formatted duration string (HH:MM:SS)

##### `reorder_songs(new_order: List[str]) -> bool`

Reorder songs in the playlist.

**Parameters:**
- `new_order` (List[str]): List of song IDs in desired order

**Returns:**
- bool: True if reordering was successful

**Example:**
```python
song_ids = [song3.song_id, song1.song_id, song2.song_id]
playlist.reorder_songs(song_ids)
```

##### `shuffle_songs() -> None`

Randomly shuffle songs in the playlist.

**Example:**
```python
playlist.shuffle_songs()
```

##### `clear_songs() -> None`

Remove all songs from the playlist.

**Example:**
```python
playlist.clear_songs()
```

#### Search and Filter Methods

##### `search_songs(query: str) -> List[Song]`

Search for songs in the playlist.

**Parameters:**
- `query` (str): Search query string

**Returns:**
- List[Song]: Songs matching the search query

**Search Criteria:**
- Song title (case-insensitive)
- Artist name (case-insensitive)
- Album name (case-insensitive)
- Genre (case-insensitive)

**Example:**
```python
results = playlist.search_songs('Queen')
# Returns all songs containing 'Queen' in title, artist, album, or genre
```

##### `filter_songs_by_genre(genre: str) -> List[Song]`

Filter songs by genre.

**Parameters:**
- `genre` (str): Genre to filter by

**Returns:**
- List[Song]: Songs matching the genre (case-insensitive)

##### `filter_songs_by_artist(artist: str) -> List[Song]`

Filter songs by artist.

**Parameters:**
- `artist` (str): Artist to filter by

**Returns:**
- List[Song]: Songs matching the artist (case-insensitive)

#### Data Conversion

##### `to_dict() -> Dict[str, Any]`

Convert playlist to dictionary representation.

**Returns:**
- Dictionary containing all playlist data including songs

##### `from_dict(data: Dict[str, Any]) -> Playlist`

Create playlist from dictionary representation.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary containing playlist data

**Returns:**
- New Playlist instance

#### Magic Methods

- `__str__()`: Returns formatted playlist info
- `__repr__()`: Returns detailed string representation
- `__len__()`: Returns number of songs
- `__contains__(song)`: Returns True if song is in playlist

### PlaylistManager Class

High-level manager for playlist operations and business logic.

```python
class PlaylistManager:
    def __init__(self, storage: Optional[StorageInterface] = None)
```

#### Parameters

- `storage` (Optional[StorageInterface]): Storage implementation (defaults to InMemoryStorage)

#### Playlist CRUD Operations

##### `create_playlist(name: str, description: str = "", **kwargs) -> Playlist`

Create a new playlist.

**Parameters:**
- `name` (str): Playlist name
- `description` (str): Playlist description
- `**kwargs`: Additional playlist metadata

**Returns:**
- Playlist: Created playlist instance

**Raises:**
- `ValueError`: If playlist name is invalid
- `PlaylistExistsError`: If playlist with same name exists

**Example:**
```python
playlist = manager.create_playlist(
    name="My Favorites",
    description="My favorite songs",
    tags=['rock', 'favorites'],
    is_public=True
)
```

##### `get_playlist(playlist_id: str) -> Optional[Playlist]`

Retrieve a playlist by ID.

**Parameters:**
- `playlist_id` (str): ID of the playlist to retrieve

**Returns:**
- Optional[Playlist]: Playlist instance if found, None otherwise

##### `get_playlist_by_name(name: str) -> Optional[Playlist]`

Retrieve a playlist by name (case-insensitive).

**Parameters:**
- `name` (str): Name of the playlist to retrieve

**Returns:**
- Optional[Playlist]: Playlist instance if found, None otherwise

##### `update_playlist(playlist_id: str, **kwargs) -> bool`

Update playlist metadata.

**Parameters:**
- `playlist_id` (str): ID of the playlist to update
- `**kwargs`: Fields to update

**Returns:**
- bool: True if update was successful

##### `delete_playlist(playlist_id: str) -> bool`

Delete a playlist.

**Parameters:**
- `playlist_id` (str): ID of the playlist to delete

**Returns:**
- bool: True if deletion was successful

##### `list_playlists(include_public: bool = True, tags: Optional[List[str]] = None, sort_by: str = "name") -> List[Playlist]`

List all playlists with optional filtering and sorting.

**Parameters:**
- `include_public` (bool): Whether to include public playlists
- `tags` (Optional[List[str]]): Filter by tags
- `sort_by` (str): Sort criteria ('name', 'creation_date', 'modification_date', 'song_count')

**Returns:**
- List[Playlist]: List of matching playlists

**Example:**
```python
# List all playlists
all_playlists = manager.list_playlists()

# List only public playlists with 'rock' tag
public_rock = manager.list_playlists(
    include_public=True,
    tags=['rock']
)

# Sort by song count
by_song_count = manager.list_playlists(sort_by='song_count')
```

#### Song Management Across Playlists

##### `add_song_to_playlist(playlist_id: str, song: Song) -> bool`

Add a song to a specific playlist.

**Parameters:**
- `playlist_id` (str): ID of the playlist
- `song` (Song): Song to add

**Returns:**
- bool: True if song was added successfully

##### `remove_song_from_playlist(playlist_id: str, song: Union[Song, str]) -> bool`

Remove a song from a specific playlist.

**Parameters:**
- `playlist_id` (str): ID of the playlist
- `song` (Union[Song, str]): Song to remove (Song object or song ID)

**Returns:**
- bool: True if song was removed successfully

##### `move_song_between_playlists(source_playlist_id: str, target_playlist_id: str, song: Union[Song, str]) -> bool`

Move a song from one playlist to another.

**Parameters:**
- `source_playlist_id` (str): ID of source playlist
- `target_playlist_id` (str): ID of target playlist
- `song` (Union[Song, str]): Song to move

**Returns:**
- bool: True if song was moved successfully

#### Search and Filter Operations

##### `search_playlists(query: str) -> List[Playlist]`

Search playlists by name, description, or tags.

**Parameters:**
- `query` (str): Search query string

**Returns:**
- List[Playlist]: Playlists matching the search query

##### `find_playlists_by_tag(tag: str) -> List[Playlist]`

Find all playlists containing a specific tag.

**Parameters:**
- `tag` (str): Tag to search for

**Returns:**
- List[Playlist]: Playlists containing the tag

##### `search_songs_across_playlists(query: str, playlist_ids: Optional[List[str]] = None) -> Dict[str, List[Song]]`

Search for songs across all or specified playlists.

**Parameters:**
- `query` (str): Search query string
- `playlist_ids` (Optional[List[str]]): Optional list of playlist IDs to search in

**Returns:**
- Dict[str, List[Song]]: Dictionary mapping playlist IDs to matching songs

**Example:**
```python
# Search across all playlists
results = manager.search_songs_across_playlists('Queen')

# Search in specific playlists only
results = manager.search_songs_across_playlists(
    'Rock', 
    [playlist1_id, playlist2_id]
)
```

##### `get_duplicate_songs() -> Dict[str, List[str]]`

Find songs that appear in multiple playlists.

**Returns:**
- Dict[str, List[str]]: Dictionary mapping song IDs to list of playlist IDs

#### Analytics and Statistics

##### `get_playlist_statistics() -> Dict[str, Any]`

Get comprehensive statistics about all playlists.

**Returns:**
- Dictionary containing various statistics including:
  - `total_playlists`: Total number of playlists
  - `total_songs`: Total number of song instances
  - `total_unique_songs`: Number of unique songs
  - `average_songs_per_playlist`: Average songs per playlist
  - `total_duration`: Total duration in seconds
  - `average_duration_per_playlist`: Average duration per playlist
  - `most_popular_genres`: List of genre popularity
  - `most_active_playlist`: Playlist with most songs
  - `public_vs_private`: Count of public vs private playlists

#### Cache Management

##### `clear_cache() -> None`

Clear the playlist cache.

##### `refresh_cache() -> None`

Refresh the playlist cache from storage.

## Storage Classes

### StorageInterface (Abstract Base Class)

Abstract interface for playlist storage implementations.

#### Methods

##### `save_playlist(playlist: Playlist) -> bool`

Save a playlist to storage.

##### `load_playlist(playlist_id: str) -> Optional[Playlist]`

Load a playlist from storage.

##### `delete_playlist(playlist_id: str) -> bool`

Delete a playlist from storage.

##### `list_all_playlists() -> List[Playlist]`

List all playlists in storage.

##### `playlist_exists(playlist_id: str) -> bool`

Check if a playlist exists in storage.

##### `get_storage_stats() -> Dict[str, Any]`

Get storage statistics.

### InMemoryStorage

In-memory storage implementation for testing and development.

#### Constructor

```python
InMemoryStorage()
```

#### Additional Methods

##### `clear_all() -> None`

Clear all playlists from memory.

##### `backup_to_dict() -> Dict[str, Any]`

Create a backup dictionary of all playlists.

##### `restore_from_backup(backup_data: Dict[str, Any]) -> bool`

Restore playlists from backup data.

### FileStorage

File-based storage implementation for simple persistence.

#### Constructor

```python
FileStorage(storage_dir: str = "playlist_data")
```

#### Additional Methods

##### `export_all_playlists(export_file: str) -> bool`

Export all playlists to a single file.

##### `import_playlists(import_file: str, overwrite: bool = False) -> int`

Import playlists from a file.

##### `cleanup_invalid_files() -> int`

Remove invalid or corrupted playlist files.

### DatabaseStorage

Database storage interface for future database implementations.

#### Constructor

```python
DatabaseStorage(connection_string: str, **kwargs)
```

**Note:** This is a template implementation. Actual database operations need to be implemented.

## Exceptions

### DuplicateSongError

Exception raised when attempting to add a duplicate song to a playlist.

**Base Class:** `Exception`

### PlaylistExistsError

Exception raised when attempting to create a playlist with an existing name.

**Base Class:** `Exception`

## Factory Functions

### `create_playlist_manager(storage_type: str = "memory", **storage_config) -> PlaylistManager`

Factory function to create a playlist manager with specified storage.

**Parameters:**
- `storage_type` (str): Type of storage ('memory', 'file', or 'database')
- `**storage_config`: Configuration parameters for storage

**Returns:**
- PlaylistManager: Configured playlist manager

**Raises:**
- ValueError: If storage type is not supported

**Example:**
```python
# Create with in-memory storage
manager = create_playlist_manager()

# Create with file storage
manager = create_playlist_manager(storage_type='file', storage_dir='data/')

# Create with database storage
manager = create_playlist_manager(
    storage_type='database',
    connection_string='sqlite:///app.db'
)
```

### `create_song(title: str, artist: str, **kwargs) -> Song`

Convenience function to create a song with validation.

**Parameters:**
- `title` (str): Song title
- `artist` (str): Artist name
- `**kwargs`: Additional song metadata

**Returns:**
- Song: Created song instance

**Raises:**
- ValueError: If song data is invalid

### `create_playlist(name: str, description: str = "", **kwargs) -> Playlist`

Convenience function to create a playlist with validation.

**Parameters:**
- `name` (str): Playlist name
- `description` (str): Playlist description
- `**kwargs`: Additional playlist metadata

**Returns:**
- Playlist: Created playlist instance

**Raises:**
- ValueError: If playlist data is invalid

## Enumerations

### Storage Types

```python
STORAGE_TYPES = {
    'memory': 'InMemoryStorage',
    'file': 'FileStorage',
    'database': 'DatabaseStorage'
}
```

### Sort Options

```python
SORT_OPTIONS = [
    'name',
    'creation_date',
    'modification_date',
    'song_count'
]
```

## Error Handling

All methods include comprehensive error handling:

1. **Input Validation**: All inputs are validated before processing
2. **Type Checking**: Proper type checking for parameters
3. **Exception Raising**: Descriptive exceptions for error conditions
4. **Graceful Degradation**: Methods return sensible defaults when possible

### Common Error Scenarios

- **Invalid Song Data**: Missing title/artist, invalid duration
- **Duplicate Songs**: Attempting to add same song to playlist
- **Missing Playlists**: Operations on non-existent playlists
- **Storage Failures**: I/O errors, permission issues
- **Serialization Errors**: Invalid data formats

## Performance Considerations

### Memory Usage

- **InMemoryStorage**: Loads all data into memory
- **FileStorage**: Loads playlists on-demand
- **DatabaseStorage**: Uses database query optimization

### Search Performance

- Linear search through playlist songs
- Case-insensitive string matching
- Consider indexing for large datasets

### Caching

- PlaylistManager includes optional caching
- Cache invalidation on modifications
- Configurable cache size

## Thread Safety

The current implementation is not thread-safe. For multi-threaded applications:

1. Use locks around PlaylistManager operations
2. Consider using thread-safe storage implementations
3. Implement proper synchronization for shared resources

## Best Practices

1. **Error Handling**: Always catch and handle exceptions
2. **Validation**: Validate inputs before operations
3. **Resource Management**: Properly close file handles
4. **Testing**: Write comprehensive unit tests
5. **Documentation**: Document custom implementations
6. **Performance**: Consider data size and usage patterns