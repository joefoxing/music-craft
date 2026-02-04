"""
Song module for playlist management system.

This module provides the Song class for representing individual songs
with comprehensive metadata management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class Song:
    """
    Represents a song with comprehensive metadata.
    
    This class encapsulates all song-related information and provides
    validation and utility methods for song management.
    """
    
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds
    genre: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    song_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creation_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate song attributes after initialization."""
        if not self.title.strip():
            raise ValueError("Song title cannot be empty")
        if not self.artist.strip():
            raise ValueError("Song artist cannot be empty")
        if self.duration is not None and self.duration <= 0:
            raise ValueError("Song duration must be positive")
    
    @property
    def duration_formatted(self) -> str:
        """
        Get formatted duration string (MM:SS format).
        
        Returns:
            str: Formatted duration string
        """
        if self.duration is None:
            return "00:00"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def display_name(self) -> str:
        """
        Get display name for the song.
        
        Returns:
            str: Display name in format "Artist - Title"
        """
        return f"{self.artist} - {self.title}"
    
    def update_metadata(self, **kwargs) -> None:
        """
        Update song metadata.
        
        Args:
            **kwargs: Metadata fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert song to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the song
        """
        return {
            'song_id': self.song_id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'duration_formatted': self.duration_formatted,
            'genre': self.genre,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'creation_date': self.creation_date.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Song':
        """
        Create song from dictionary representation.
        
        Args:
            data: Dictionary containing song data
            
        Returns:
            Song: Song instance created from dictionary
        """
        # Handle datetime conversion
        if 'creation_date' in data and isinstance(data['creation_date'], str):
            data['creation_date'] = datetime.fromisoformat(data['creation_date'])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of the song."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Detailed string representation of the song."""
        return f"Song(id={self.song_id[:8]}, title='{self.title}', artist='{self.artist}')"
    
    def __eq__(self, other) -> bool:
        """Check equality based on song_id."""
        if not isinstance(other, Song):
            return False
        return self.song_id == other.song_id
    
    def __hash__(self) -> int:
        """Hash based on song_id for use in sets."""
        return hash(self.song_id)


class SongValidator:
    """
    Utility class for validating song data.
    """
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate song title."""
        return bool(title and title.strip())
    
    @staticmethod
    def validate_artist(artist: str) -> bool:
        """Validate song artist."""
        return bool(artist and artist.strip())
    
    @staticmethod
    def validate_duration(duration: Optional[int]) -> bool:
        """Validate song duration."""
        return duration is None or duration > 0
    
    @staticmethod
    def validate_genre(genre: Optional[str]) -> bool:
        """Validate song genre."""
        return genre is None or bool(genre.strip())
    
    @classmethod
    def validate_song_data(cls, title: str, artist: str, **kwargs) -> bool:
        """Validate complete song data."""
        return (cls.validate_title(title) and 
                cls.validate_artist(artist) and
                cls.validate_duration(kwargs.get('duration')) and
                cls.validate_genre(kwargs.get('genre')))