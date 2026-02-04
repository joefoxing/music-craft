"""
Playlist Management System

A comprehensive, framework-agnostic playlist management module with modular architecture,
comprehensive CRUD operations, and clean separation of concerns.

Main Components:
- Song: Represents individual songs with metadata
- Playlist: Manages collections of songs
- PlaylistManager: High-level business logic and coordination
- Storage: Abstract storage layer with multiple implementations

Features:
- Full CRUD operations for playlists and songs
- Song search and filtering capabilities
- Duplicate song prevention
- Comprehensive metadata management
- Dependency injection for storage layer
- Framework-agnostic design
- Comprehensive error handling
- Unit testing support

Usage:
    from app.playlist_management import create_playlist_manager
    
    # Create manager with in-memory storage
    manager = create_playlist_manager()
    
    # Create a playlist
    playlist = manager.create_playlist(
        name="My Favorites",
        description="My favorite songs"
    )
    
    # Add songs
    song = Song(
        title="Song Title",
        artist="Artist Name",
        album="Album Name",
        duration=180  # 3 minutes
    )
    manager.add_song_to_playlist(playlist.playlist_id, song)
"""

# Core imports
from .song import Song, SongValidator
from .playlist import Playlist, DuplicateSongError
from .playlist_manager import PlaylistManager, PlaylistExistsError
from .storage import (
    StorageInterface, 
    InMemoryStorage, 
    FileStorage, 
    DatabaseStorage
)

# Main factory function
def create_playlist_manager(storage_type: str = "memory", **storage_config) -> PlaylistManager:
    """
    Factory function to create a playlist manager with specified storage.
    
    Args:
        storage_type: Type of storage ('memory', 'file', or 'database')
        **storage_config: Configuration parameters for storage
        
    Returns:
        PlaylistManager: Configured playlist manager
        
    Raises:
        ValueError: If storage type is not supported
    """
    storage_type = storage_type.lower()
    
    if storage_type == "memory":
        storage = InMemoryStorage()
    elif storage_type == "file":
        storage_dir = storage_config.get("storage_dir", "playlist_data")
        storage = FileStorage(storage_dir)
    elif storage_type == "database":
        connection_string = storage_config.get("connection_string", "")
        storage = DatabaseStorage(connection_string, **storage_config)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
    
    return PlaylistManager(storage)


# Convenience functions
def create_song(title: str, artist: str, **kwargs) -> Song:
    """
    Convenience function to create a song with validation.
    
    Args:
        title: Song title
        artist: Artist name
        **kwargs: Additional song metadata
        
    Returns:
        Song: Created song instance
        
    Raises:
        ValueError: If song data is invalid
    """
    if not SongValidator.validate_song_data(title, artist, **kwargs):
        raise ValueError("Invalid song data provided")
    
    return Song(title=title, artist=artist, **kwargs)


def create_playlist(name: str, description: str = "", **kwargs) -> Playlist:
    """
    Convenience function to create a playlist with validation.
    
    Args:
        name: Playlist name
        description: Playlist description
        **kwargs: Additional playlist metadata
        
    Returns:
        Playlist: Created playlist instance
        
    Raises:
        ValueError: If playlist data is invalid
    """
    try:
        return Playlist(name=name, description=description, **kwargs)
    except ValueError as e:
        raise ValueError(f"Invalid playlist data: {e}")


# Version information
__version__ = "1.0.0"
__author__ = "Playlist Management System"
__description__ = "Comprehensive playlist management module"

# Public API exports
__all__ = [
    # Core classes
    "Song",
    "Playlist", 
    "PlaylistManager",
    "StorageInterface",
    
    # Storage implementations
    "InMemoryStorage",
    "FileStorage", 
    "DatabaseStorage",
    
    # Exceptions
    "DuplicateSongError",
    "PlaylistExistsError",
    
    # Factory functions
    "create_playlist_manager",
    "create_song",
    "create_playlist",
    
    # Validators
    "SongValidator"
]