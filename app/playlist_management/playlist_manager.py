"""
Playlist Manager module for playlist management system.

This module provides the PlaylistManager class for high-level playlist operations,
business logic, and coordination between multiple playlists.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from .playlist import Playlist, DuplicateSongError
from .song import Song
from .storage import StorageInterface, InMemoryStorage


class PlaylistManager:
    """
    High-level manager for playlist operations and business logic.
    
    This class provides methods for managing multiple playlists, searching,
    filtering, and coordinating playlist operations across the system.
    """
    
    def __init__(self, storage: Optional[StorageInterface] = None):
        """
        Initialize the playlist manager.
        
        Args:
            storage: Storage implementation (defaults to in-memory storage)
        """
        self.storage = storage or InMemoryStorage()
        self._cached_playlists: Dict[str, Playlist] = {}
        self._cache_dirty = True
    
    # Playlist CRUD Operations
    
    def create_playlist(self, 
                       name: str, 
                       description: str = "",
                       tags: Optional[List[str]] = None,
                       cover_image_url: Optional[str] = None,
                       is_public: bool = False) -> Playlist:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            tags: List of playlist tags
            cover_image_url: URL to playlist cover image
            is_public: Whether playlist is public
            
        Returns:
            Playlist: Created playlist instance
            
        Raises:
            ValueError: If playlist name is invalid
            PlaylistExistsError: If playlist with same name exists
        """
        # Validate playlist name
        if not name or not name.strip():
            raise ValueError("Playlist name cannot be empty")
        
        # Check for duplicate names (case-insensitive)
        if self._get_playlist_by_name(name) is not None:
            raise PlaylistExistsError(f"Playlist with name '{name}' already exists")
        
        # Create playlist
        playlist = Playlist(
            name=name,
            description=description,
            tags=tags,
            cover_image_url=cover_image_url,
            is_public=is_public
        )
        
        # Save to storage
        self.storage.save_playlist(playlist)
        
        # Update cache
        self._cached_playlists[playlist.playlist_id] = playlist
        self._cache_dirty = False
        
        return playlist
    
    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Retrieve a playlist by ID.
        
        Args:
            playlist_id: ID of the playlist to retrieve
            
        Returns:
            Optional[Playlist]: Playlist instance if found, None otherwise
        """
        # Check cache first
        if not self._cache_dirty and playlist_id in self._cached_playlists:
            return self._cached_playlists[playlist_id]
        
        # Load from storage
        playlist = self.storage.load_playlist(playlist_id)
        if playlist:
            self._cached_playlists[playlist_id] = playlist
            self._cache_dirty = False
        
        return playlist
    
    def get_playlist_by_name(self, name: str) -> Optional[Playlist]:
        """
        Retrieve a playlist by name (case-insensitive).
        
        Args:
            name: Name of the playlist to retrieve
            
        Returns:
            Optional[Playlist]: Playlist instance if found, None otherwise
        """
        return self._get_playlist_by_name(name)
    
    def update_playlist(self, playlist_id: str, **kwargs) -> bool:
        """
        Update playlist metadata.
        
        Args:
            playlist_id: ID of the playlist to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if update was successful
        """
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        # Update metadata
        playlist.update_metadata(**kwargs)
        
        # Save to storage
        self.storage.save_playlist(playlist)
        
        # Update cache
        self._cached_playlists[playlist_id] = playlist
        
        return True
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            bool: True if deletion was successful
        """
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        # Delete from storage
        success = self.storage.delete_playlist(playlist_id)
        
        if success:
            # Remove from cache
            if playlist_id in self._cached_playlists:
                del self._cached_playlists[playlist_id]
        
        return success
    
    def list_playlists(self, 
                      include_public: bool = True,
                      tags: Optional[List[str]] = None,
                      sort_by: str = "name") -> List[Playlist]:
        """
        List all playlists with optional filtering and sorting.
        
        Args:
            include_public: Whether to include public playlists
            tags: Filter by tags
            sort_by: Sort criteria ('name', 'creation_date', 'modification_date', 'song_count')
            
        Returns:
            List[Playlist]: List of matching playlists
        """
        playlists = []
        
        # Get all playlists from storage
        all_playlists = self.storage.list_all_playlists()
        
        for playlist in all_playlists:
            # Filter by public status
            if not include_public and playlist.metadata.is_public:
                continue
            
            # Filter by tags
            if tags:
                playlist_tags = set(tag.lower() for tag in playlist.metadata.tags)
                filter_tags = set(tag.lower() for tag in tags)
                if not filter_tags.issubset(playlist_tags):
                    continue
            
            playlists.append(playlist)
        
        # Sort playlists
        playlists.sort(key=lambda p: self._get_sort_key(p, sort_by))
        
        return playlists
    
    # Song Management Across Playlists
    
    def add_song_to_playlist(self, playlist_id: str, song: Song) -> bool:
        """
        Add a song to a specific playlist.
        
        Args:
            playlist_id: ID of the playlist
            song: Song to add
            
        Returns:
            bool: True if song was added successfully
        """
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        try:
            playlist.create_song(song)
            
            # Save to storage
            self.storage.save_playlist(playlist)
            
            # Update cache
            self._cached_playlists[playlist_id] = playlist
            
            return True
        except (ValueError, DuplicateSongError):
            return False
    
    def remove_song_from_playlist(self, playlist_id: str, song: Union[Song, str]) -> bool:
        """
        Remove a song from a specific playlist.
        
        Args:
            playlist_id: ID of the playlist
            song: Song to remove (Song object or song ID)
            
        Returns:
            bool: True if song was removed successfully
        """
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        success = playlist.delete_song(song)
        
        if success:
            # Save to storage
            self.storage.save_playlist(playlist)
            
            # Update cache
            self._cached_playlists[playlist_id] = playlist
        
        return success
    
    def move_song_between_playlists(self, 
                                  source_playlist_id: str,
                                  target_playlist_id: str,
                                  song: Union[Song, str]) -> bool:
        """
        Move a song from one playlist to another.
        
        Args:
            source_playlist_id: ID of source playlist
            target_playlist_id: ID of target playlist
            song: Song to move
            
        Returns:
            bool: True if song was moved successfully
        """
        source_playlist = self.get_playlist(source_playlist_id)
        target_playlist = self.get_playlist(target_playlist_id)
        
        if not source_playlist or not target_playlist:
            return False
        
        # Get song from source (if song is ID)
        if isinstance(song, str):
            song_obj = source_playlist.get_song_by_id(song)
            if not song_obj:
                return False
            song = song_obj
        
        # Remove from source
        if not source_playlist.delete_song(song):
            return False
        
        # Add to target
        try:
            target_playlist.create_song(song)
        except DuplicateSongError:
            # Song already exists in target, add back to source
            source_playlist.create_song(song)
            return False
        except ValueError:
            # Invalid song data, add back to source
            source_playlist.create_song(song)
            return False
        
        # Save both playlists
        self.storage.save_playlist(source_playlist)
        self.storage.save_playlist(target_playlist)
        
        # Update cache
        self._cached_playlists[source_playlist_id] = source_playlist
        self._cached_playlists[target_playlist_id] = target_playlist
        
        return True
    
    # Search and Filter Operations
    
    def search_playlists(self, query: str) -> List[Playlist]:
        """
        Search playlists by name, description, or tags.
        
        Args:
            query: Search query string
            
        Returns:
            List[Playlist]: Playlists matching the search query
        """
        query_lower = query.lower()
        matching_playlists = []
        
        for playlist in self.storage.list_all_playlists():
            if (query_lower in playlist.metadata.name.lower() or
                query_lower in playlist.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in playlist.metadata.tags)):
                matching_playlists.append(playlist)
        
        return matching_playlists
    
    def find_playlists_by_tag(self, tag: str) -> List[Playlist]:
        """
        Find all playlists containing a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List[Playlist]: Playlists containing the tag
        """
        tag_lower = tag.lower()
        matching_playlists = []
        
        for playlist in self.storage.list_all_playlists():
            if any(tag_lower == existing_tag.lower() for existing_tag in playlist.metadata.tags):
                matching_playlists.append(playlist)
        
        return matching_playlists
    
    def search_songs_across_playlists(self, 
                                    query: str,
                                    playlist_ids: Optional[List[str]] = None) -> Dict[str, List[Song]]:
        """
        Search for songs across all or specified playlists.
        
        Args:
            query: Search query string
            playlist_ids: Optional list of playlist IDs to search in
            
        Returns:
            Dict[str, List[Song]]: Dictionary mapping playlist IDs to matching songs
        """
        results = {}
        
        if playlist_ids:
            # Search in specific playlists
            for playlist_id in playlist_ids:
                playlist = self.get_playlist(playlist_id)
                if playlist:
                    matching_songs = playlist.search_songs(query)
                    if matching_songs:
                        results[playlist_id] = matching_songs
        else:
            # Search in all playlists
            for playlist in self.storage.list_all_playlists():
                matching_songs = playlist.search_songs(query)
                if matching_songs:
                    results[playlist.playlist_id] = matching_songs
        
        return results
    
    def get_duplicate_songs(self) -> Dict[str, List[str]]:
        """
        Find songs that appear in multiple playlists.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping song IDs to list of playlist IDs
        """
        song_playlists = {}
        
        for playlist in self.storage.list_all_playlists():
            for song in playlist.read_songs():
                if song.song_id not in song_playlists:
                    song_playlists[song.song_id] = []
                song_playlists[song.song_id].append(playlist.playlist_id)
        
        # Return only songs in multiple playlists
        return {song_id: playlists for song_id, playlists in song_playlists.items()
                if len(playlists) > 1}
    
    # Analytics and Statistics
    
    def get_playlist_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about all playlists.
        
        Returns:
            Dict[str, Any]: Dictionary containing various statistics
        """
        playlists = self.storage.list_all_playlists()
        
        if not playlists:
            return {
                'total_playlists': 0,
                'total_songs': 0,
                'total_unique_songs': 0,
                'average_songs_per_playlist': 0,
                'total_duration': 0,
                'average_duration_per_playlist': 0,
                'most_popular_genres': [],
                'most_active_playlist': None,
                'public_vs_private': {'public': 0, 'private': 0}
            }
        
        # Basic counts
        total_playlists = len(playlists)
        total_songs = sum(playlist.get_song_count() for playlist in playlists)
        
        # Unique songs
        all_song_ids = set()
        for playlist in playlists:
            for song in playlist.read_songs():
                all_song_ids.add(song.song_id)
        total_unique_songs = len(all_song_ids)
        
        # Durations
        total_duration = sum(playlist.get_total_duration() for playlist in playlists)
        
        # Genres
        genre_counts = {}
        for playlist in playlists:
            for song in playlist.read_songs():
                if song.genre:
                    genre = song.genre.lower()
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        most_popular_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Most active playlist
        most_active = max(playlists, key=lambda p: p.get_song_count())
        
        # Public vs private
        public_count = sum(1 for p in playlists if p.metadata.is_public)
        
        return {
            'total_playlists': total_playlists,
            'total_songs': total_songs,
            'total_unique_songs': total_unique_songs,
            'average_songs_per_playlist': total_songs / total_playlists if total_playlists > 0 else 0,
            'total_duration': total_duration,
            'average_duration_per_playlist': total_duration / total_playlists if total_playlists > 0 else 0,
            'most_popular_genres': most_popular_genres,
            'most_active_playlist': {
                'id': most_active.playlist_id,
                'name': most_active.metadata.name,
                'song_count': most_active.get_song_count()
            },
            'public_vs_private': {
                'public': public_count,
                'private': total_playlists - public_count
            }
        }
    
    # Cache Management
    
    def clear_cache(self) -> None:
        """Clear the playlist cache."""
        self._cached_playlists.clear()
        self._cache_dirty = True
    
    def refresh_cache(self) -> None:
        """Refresh the playlist cache from storage."""
        self.clear_cache()
        for playlist in self.storage.list_all_playlists():
            self._cached_playlists[playlist.playlist_id] = playlist
        self._cache_dirty = False
    
    # Private Helper Methods
    
    def _get_playlist_by_name(self, name: str) -> Optional[Playlist]:
        """Get playlist by name (case-insensitive)."""
        name_lower = name.lower()
        for playlist in self.storage.list_all_playlists():
            if playlist.metadata.name.lower() == name_lower:
                return playlist
        return None
    
    def _get_sort_key(self, playlist: Playlist, sort_by: str):
        """Get sorting key for playlist."""
        if sort_by == "name":
            return playlist.metadata.name.lower()
        elif sort_by == "creation_date":
            return playlist.creation_date
        elif sort_by == "modification_date":
            return playlist.modification_date
        elif sort_by == "song_count":
            return playlist.get_song_count()
        else:
            return playlist.metadata.name.lower()


class PlaylistExistsError(Exception):
    """Exception raised when attempting to create a playlist with an existing name."""
    pass