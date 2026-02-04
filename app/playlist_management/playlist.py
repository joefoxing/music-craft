"""
Playlist module for playlist management system.

This module provides the Playlist class for managing collections of songs
with full CRUD operations and metadata handling.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
import uuid
from .song import Song, SongValidator


@dataclass
class PlaylistMetadata:
    """Metadata container for playlist information."""
    
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    cover_image_url: Optional[str] = None
    is_public: bool = False
    total_duration: Optional[int] = None  # Total duration in seconds
    
    def __post_init__(self):
        """Validate metadata after initialization."""
        if not self.name.strip():
            raise ValueError("Playlist name cannot be empty")


class Playlist:
    """
    Represents a playlist containing songs with full CRUD operations.
    
    This class manages playlists with comprehensive metadata, song management,
    and provides methods for playlist manipulation and validation.
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "",
                 playlist_id: Optional[str] = None,
                 creation_date: Optional[datetime] = None,
                 tags: Optional[List[str]] = None,
                 cover_image_url: Optional[str] = None,
                 is_public: bool = False):
        """
        Initialize a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            playlist_id: Optional playlist ID (generated if not provided)
            creation_date: Creation date (defaults to now)
            tags: List of playlist tags
            cover_image_url: URL to playlist cover image
            is_public: Whether playlist is public
        """
        self.metadata = PlaylistMetadata(
            name=name,
            description=description,
            tags=tags or [],
            cover_image_url=cover_image_url,
            is_public=is_public
        )
        
        self.playlist_id = playlist_id or str(uuid.uuid4())
        self.creation_date = creation_date or datetime.now()
        self.modification_date = self.creation_date
        
        # Song management
        self._songs: List[Song] = []
        self._song_ids: set = set()  # For fast duplicate checking
    
    # CRUD Operations
    
    def create_song(self, song: Song) -> None:
        """
        Add a song to the playlist.
        
        Args:
            song: Song object to add
            
        Raises:
            ValueError: If song data is invalid
            DuplicateSongError: If song already exists in playlist
        """
        if not SongValidator.validate_song_data(
            song.title, song.artist, 
            duration=song.duration, 
            genre=song.genre
        ):
            raise ValueError("Invalid song data")
        
        if song.song_id in self._song_ids:
            raise DuplicateSongError(f"Song '{song.display_name}' already exists in playlist")
        
        self._songs.append(song)
        self._song_ids.add(song.song_id)
        self._update_total_duration()
        self._update_modification_date()
    
    def read_songs(self, 
                  start_index: int = 0, 
                  end_index: Optional[int] = None) -> List[Song]:
        """
        Retrieve songs from the playlist.
        
        Args:
            start_index: Starting index for song retrieval
            end_index: Ending index for song retrieval (None for all remaining)
            
        Returns:
            List[Song]: List of songs in the specified range
        """
        if end_index is None:
            return self._songs[start_index:].copy()
        return self._songs[start_index:end_index].copy()
    
    def update_song(self, old_song: Song, new_song_data: Dict[str, Any]) -> None:
        """
        Update an existing song in the playlist.
        
        Args:
            old_song: Song to update
            new_song_data: Dictionary containing updated song data
            
        Raises:
            ValueError: If song not found or updated data is invalid
        """
        try:
            index = self._songs.index(old_song)
        except ValueError:
            raise ValueError("Song not found in playlist")
        
        # Create updated song
        updated_song = Song(
            title=new_song_data.get('title', old_song.title),
            artist=new_song_data.get('artist', old_song.artist),
            album=new_song_data.get('album', old_song.album),
            duration=new_song_data.get('duration', old_song.duration),
            genre=new_song_data.get('genre', old_song.genre),
            file_path=new_song_data.get('file_path', old_song.file_path),
            file_url=new_song_data.get('file_url', old_song.file_url),
            song_id=old_song.song_id
        )
        
        # Validate updated song
        if not SongValidator.validate_song_data(
            updated_song.title, updated_song.artist,
            duration=updated_song.duration,
            genre=updated_song.genre
        ):
            raise ValueError("Updated song data is invalid")
        
        self._songs[index] = updated_song
        self._update_modification_date()
    
    def delete_song(self, song: Union[Song, str]) -> bool:
        """
        Remove a song from the playlist.
        
        Args:
            song: Song object or song ID to remove
            
        Returns:
            bool: True if song was found and removed
        """
        if isinstance(song, str):
            # Find song by ID
            for i, s in enumerate(self._songs):
                if s.song_id == song:
                    del self._songs[i]
                    self._song_ids.remove(song)
                    self._update_total_duration()
                    self._update_modification_date()
                    return True
            return False
        else:
            # Find song by object
            try:
                self._songs.remove(song)
                self._song_ids.remove(song.song_id)
                self._update_total_duration()
                self._update_modification_date()
                return True
            except ValueError:
                return False
    
    # Playlist Metadata Operations
    
    def update_metadata(self, **kwargs) -> None:
        """
        Update playlist metadata.
        
        Args:
            **kwargs: Metadata fields to update
        """
        if 'name' in kwargs:
            if not kwargs['name'].strip():
                raise ValueError("Playlist name cannot be empty")
            self.metadata.name = kwargs['name']
        
        if 'description' in kwargs:
            self.metadata.description = kwargs['description']
        
        if 'tags' in kwargs:
            self.metadata.tags = kwargs['tags']
        
        if 'cover_image_url' in kwargs:
            self.metadata.cover_image_url = kwargs['cover_image_url']
        
        if 'is_public' in kwargs:
            self.metadata.is_public = kwargs['is_public']
        
        self._update_modification_date()
    
    # Utility Methods
    
    def get_song_by_id(self, song_id: str) -> Optional[Song]:
        """
        Get a song by its ID.
        
        Args:
            song_id: ID of the song to retrieve
            
        Returns:
            Optional[Song]: Song object if found, None otherwise
        """
        for song in self._songs:
            if song.song_id == song_id:
                return song
        return None
    
    def get_song_count(self) -> int:
        """Get total number of songs in playlist."""
        return len(self._songs)
    
    def get_total_duration(self) -> int:
        """
        Get total duration of all songs in playlist.
        
        Returns:
            int: Total duration in seconds
        """
        return sum(song.duration or 0 for song in self._songs)
    
    def get_total_duration_formatted(self) -> str:
        """
        Get formatted total duration.
        
        Returns:
            str: Formatted duration string (HH:MM:SS)
        """
        total_seconds = self.get_total_duration()
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def reorder_songs(self, new_order: List[str]) -> bool:
        """
 in the playlist.
        
        Args:
            new_order: List of song IDs in desired order
            
        Returns:
            bool: True if reordering was successful
        """
        if len(new_order) != len(self._songs):
            return False
        
        song_dict = {song.song_id: song for song in self._songs}
        
        try:
            reordered_songs = [song_dict[song_id] for song_id in new_order]
            self._songs = reordered_songs
            self._update_modification_date()
            return True
        except KeyError:
            return False
    
    def shuffle_songs(self) -> None:
        """Randomly shuffle songs in the playlist."""
        import random
        random.shuffle(self._songs)
        self._update_modification_date()
    
    def clear_songs(self) -> None:
        """Remove all songs from the playlist."""
        self._songs.clear()
        self._song_ids.clear()
        self._update_total_duration()
        self._update_modification_date()
    
    def search_songs(self, query: str) -> List[Song]:
        """
        Search for songs in the playlist.
        
        Args:
            query: Search query string
            
        Returns:
            List[Song]: Songs matching the search query
        """
        query_lower = query.lower()
        matches = []
        
        for song in self._songs:
            if (query_lower in song.title.lower() or
                query_lower in song.artist.lower() or
                query_lower in (song.album or "").lower() or
                query_lower in (song.genre or "").lower()):
                matches.append(song)
        
        return matches
    
    def filter_songs_by_genre(self, genre: str) -> List[Song]:
        """
        Filter songs by genre.
        
        Args:
            genre: Genre to filter by
            
        Returns:
            List[Song]: Songs matching the genre
        """
        return [song for song in self._songs if song.genre and song.genre.lower() == genre.lower()]
    
    def filter_songs_by_artist(self, artist: str) -> List[Song]:
        """
        Filter songs by artist.
        
        Args:
            artist: Artist to filter by
            
        Returns:
            List[Song]: Songs matching the artist
        """
        return [song for song in self._songs if song.artist.lower() == artist.lower()]
    
    # Data Conversion
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert playlist to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the playlist
        """
        return {
            'playlist_id': self.playlist_id,
            'name': self.metadata.name,
            'description': self.metadata.description,
            'tags': self.metadata.tags,
            'cover_image_url': self.metadata.cover_image_url,
            'is_public': self.metadata.is_public,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'song_count': self.get_song_count(),
            'total_duration': self.get_total_duration(),
            'total_duration_formatted': self.get_total_duration_formatted(),
            'songs': [song.to_dict() for song in self._songs]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Playlist':
        """
        Create playlist from dictionary representation.
        
        Args:
            data: Dictionary containing playlist data
            
        Returns:
            Playlist: Playlist instance created from dictionary
        """
        # Handle datetime conversions
        creation_date = None
        if 'creation_date' in data and isinstance(data['creation_date'], str):
            creation_date = datetime.fromisoformat(data['creation_date'])
        
        playlist = cls(
            name=data['name'],
            description=data.get('description', ''),
            playlist_id=data.get('playlist_id'),
            creation_date=creation_date,
            tags=data.get('tags', []),
            cover_image_url=data.get('cover_image_url'),
            is_public=data.get('is_public', False)
        )
        
        # Add songs
        if 'songs' in data:
            for song_data in data['songs']:
                song = Song.from_dict(song_data)
                playlist._songs.append(song)
                playlist._song_ids.add(song.song_id)
        
        playlist._update_total_duration()
        return playlist
    
    # Private Methods
    
    def _update_total_duration(self) -> None:
        """Update total duration in metadata."""
        self.metadata.total_duration = self.get_total_duration()
    
    def _update_modification_date(self) -> None:
        """Update modification date."""
        self.modification_date = datetime.now()
    
    # Magic Methods
    
    def __str__(self) -> str:
        """String representation of the playlist."""
        return f"Playlist '{self.metadata.name}' ({self.get_song_count()} songs)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the playlist."""
        return (f"Playlist(id={self.playlist_id[:8]}, "
                f"name='{self.metadata.name}', "
                f"songs={self.get_song_count()})")
    
    def __len__(self) -> int:
        """Number of songs in playlist."""
        return len(self._songs)
    
    def __contains__(self, song: Song) -> bool:
        """Check if song is in playlist."""
        return song.song_id in self._song_ids


class DuplicateSongError(Exception):
    """Exception raised when attempting to add a duplicate song."""
    pass