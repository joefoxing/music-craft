"""
Storage module for playlist management system.

This module provides storage abstractions and implementations for data persistence,
enabling dependency injection and framework-agnostic design.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from .playlist import Playlist


class StorageInterface(ABC):
    """
    Abstract interface for playlist storage implementations.
    
    This interface defines the contract for storage implementations, enabling
    dependency injection and allowing different storage backends to be used.
    """
    
    @abstractmethod
    def save_playlist(self, playlist: Playlist) -> bool:
        """
        Save a playlist to storage.
        
        Args:
            playlist: Playlist to save
            
        Returns:
            bool: True if save was successful
        """
        pass
    
    @abstractmethod
    def load_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Load a playlist from storage.
        
        Args:
            playlist_id: ID of the playlist to load
            
        Returns:
            Optional[Playlist]: Loaded playlist or None if not found
        """
        pass
    
    @abstractmethod
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist from storage.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            bool: True if deletion was successful
        """
        pass
    
    @abstractmethod
    def list_all_playlists(self) -> List[Playlist]:
        """
        List all playlists in storage.
        
        Returns:
            List[Playlist]: List of all playlists
        """
        pass
    
    @abstractmethod
    def playlist_exists(self, playlist_id: str) -> bool:
        """
        Check if a playlist exists in storage.
        
        Args:
            playlist_id: ID of the playlist to check
            
        Returns:
            bool: True if playlist exists
        """
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing storage statistics
        """
        pass


class InMemoryStorage(StorageInterface):
    """
    In-memory storage implementation for testing and development.
    
    This implementation stores playlists in memory and is suitable for
    testing, development, and scenarios where persistence is not required.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._playlists: Dict[str, Playlist] = {}
        self._created_at = datetime.now()
        self._operation_count = 0
    
    def save_playlist(self, playlist: Playlist) -> bool:
        """
        Save a playlist to memory.
        
        Args:
            playlist: Playlist to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            self._playlists[playlist.playlist_id] = playlist
            self._operation_count += 1
            return True
        except Exception:
            return False
    
    def load_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Load a playlist from memory.
        
        Args:
            playlist_id: ID of the playlist to load
            
        Returns:
            Optional[Playlist]: Loaded playlist or None if not found
        """
        return self._playlists.get(playlist_id)
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist from memory.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            bool: True if deletion was successful
        """
        if playlist_id in self._playlists:
            del self._playlists[playlist_id]
            self._operation_count += 1
            return True
        return False
    
    def list_all_playlists(self) -> List[Playlist]:
        """
        List all playlists in memory.
        
        Returns:
            List[Playlist]: List of all playlists
        """
        return list(self._playlists.values())
    
    def playlist_exists(self, playlist_id: str) -> bool:
        """
        Check if a playlist exists in memory.
        
        Args:
            playlist_id: ID of the playlist to check
            
        Returns:
            bool: True if playlist exists
        """
        return playlist_id in self._playlists
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing storage statistics
        """
        return {
            'type': 'in_memory',
            'total_playlists': len(self._playlists),
            'total_songs': sum(len(playlist.read_songs()) for playlist in self._playlists.values()),
            'operation_count': self._operation_count,
            'created_at': self._created_at.isoformat(),
            'memory_usage': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> Dict[str, int]:
        """Estimate memory usage of stored data."""
        import sys
        
        total_size = 0
        playlist_count = 0
        song_count = 0
        
        for playlist in self._playlists.values():
            playlist_count += 1
            playlist_size = sys.getsizeof(playlist) + sys.getsizeof(playlist.metadata)
            total_size += playlist_size
            
            for song in playlist.read_songs():
                song_count += 1
                total_size += sys.getsizeof(song) + sys.getsizeof(song.metadata)
        
        return {
            'estimated_bytes': total_size,
            'estimated_kb': total_size // 1024,
            'estimated_mb': total_size // (1024 * 1024)
        }
    
    def clear_all(self) -> None:
        """Clear all playlists from memory."""
        self._playlists.clear()
        self._operation_count = 0
    
    def backup_to_dict(self) -> Dict[str, Any]:
        """
        Create a backup dictionary of all playlists.
        
        Returns:
            Dict[str, Any]: Backup dictionary
        """
        return {
            'metadata': {
                'backup_created_at': datetime.now().isoformat(),
                'playlist_count': len(self._playlists),
                'storage_type': 'in_memory'
            },
            'playlists': {pid: playlist.to_dict() for pid, playlist in self._playlists.items()}
        }
    
    def restore_from_backup(self, backup_data: Dict[str, Any]) -> bool:
        """
        Restore playlists from backup data.
        
        Args:
            backup_data: Backup dictionary to restore from
            
        Returns:
            bool: True if restore was successful
        """
        try:
            if 'playlists' in backup_data:
                self._playlists.clear()
                
                for playlist_data in backup_data['playlists'].values():
                    playlist = Playlist.from_dict(playlist_data)
                    self._playlists[playlist.playlist_id] = playlist
                
                return True
            return False
        except Exception:
            return False


class FileStorage(StorageInterface):
    """
    File-based storage implementation for simple persistence.
    
    This implementation stores playlists as JSON files in a directory,
    suitable for small-scale applications and development.
    """
    
    def __init__(self, storage_dir: str = "playlist_data"):
        """
        Initialize file storage.
        
        Args:
            storage_dir: Directory to store playlist files
        """
        self.storage_dir = storage_dir
        self._ensure_storage_directory()
        self._operation_count = 0
    
    def _ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_playlist_file_path(self, playlist_id: str) -> str:
        """Get the file path for a playlist."""
        return os.path.join(self.storage_dir, f"{playlist_id}.json")
    
    def save_playlist(self, playlist: Playlist) -> bool:
        """
        Save a playlist to file.
        
        Args:
            playlist: Playlist to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            file_path = self._get_playlist_file_path(playlist.playlist_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._operation_count += 1
            return True
        except Exception:
            return False
    
    def load_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Load a playlist from file.
        
        Args:
            playlist_id: ID of the playlist to load
            
        Returns:
            Optional[Playlist]: Loaded playlist or None if not found
        """
        try:
            file_path = self._get_playlist_file_path(playlist_id)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)
            
            return Playlist.from_dict(playlist_data)
        except Exception:
            return None
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist file.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            file_path = self._get_playlist_file_path(playlist_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                self._operation_count += 1
                return True
            return False
        except Exception:
            return False
    
    def list_all_playlists(self) -> List[Playlist]:
        """
        List all playlists in the storage directory.
        
        Returns:
            List[Playlist]: List of all playlists
        """
        playlists = []
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    playlist_id = filename[:-5]  # Remove .json extension
                    playlist = self.load_playlist(playlist_id)
                    if playlist:
                        playlists.append(playlist)
        except Exception:
            pass  # Return whatever was loaded successfully
        
        return playlists
    
    def playlist_exists(self, playlist_id: str) -> bool:
        """
        Check if a playlist file exists.
        
        Args:
            playlist_id: ID of the playlist to check
            
        Returns:
            bool: True if playlist exists
        """
        file_path = self._get_playlist_file_path(playlist_id)
        return os.path.exists(file_path)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing storage statistics
        """
        try:
            files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            total_size = sum(os.path.getsize(os.path.join(self.storage_dir, f)) for f in files)
            
            return {
                'type': 'file',
                'storage_directory': self.storage_dir,
                'total_playlists': len(files),
                'total_files': len(files),
                'total_size_bytes': total_size,
                'total_size_kb': total_size // 1024,
                'total_size_mb': total_size // (1024 * 1024),
                'operation_count': self._operation_count
            }
        except Exception:
            return {
                'type': 'file',
                'storage_directory': self.storage_dir,
                'error': 'Unable to read storage directory'
            }
    
    def export_all_playlists(self, export_file: str) -> bool:
        """
        Export all playlists to a single file.
        
        Args:
            export_file: Path to export file
            
        Returns:
            bool: True if export was successful
        """
        try:
            playlists_data = {}
            
            for playlist in self.list_all_playlists():
                playlists_data[playlist.playlist_id] = playlist.to_dict()
            
            export_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'playlist_count': len(playlists_data),
                    'export_version': '1.0'
                },
                'playlists': playlists_data
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def import_playlists(self, import_file: str, overwrite: bool = False) -> int:
        """
        Import playlists from a file.
        
        Args:
            import_file: Path to import file
            overwrite: Whether to overwrite existing playlists
            
        Returns:
            int: Number of playlists imported
        """
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'playlists' not in import_data:
                return 0
            
            imported_count = 0
            
            for playlist_id, playlist_data in import_data['playlists'].items():
                if not overwrite and self.playlist_exists(playlist_id):
                    continue
                
                playlist = Playlist.from_dict(playlist_data)
                if self.save_playlist(playlist):
                    imported_count += 1
            
            return imported_count
        except Exception:
            return 0
    
    def cleanup_invalid_files(self) -> int:
        """
        Remove invalid or corrupted playlist files.
        
        Returns:
            int: Number of files removed
        """
        removed_count = 0
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    
                    try:
                        # Try to load the file to check if it's valid
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except Exception:
                        # File is invalid, remove it
                        os.remove(file_path)
                        removed_count += 1
        except Exception:
            pass
        
        return removed_count


class DatabaseStorage(StorageInterface):
    """
    Database storage interface for future database implementations.
    
    This class provides a template for implementing database storage
    using various database systems (SQLite, PostgreSQL, MySQL, etc.).
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize database storage.
        
        Args:
            connection_string: Database connection string
            **kwargs: Additional database configuration parameters
        """
        self.connection_string = connection_string
        self.config = kwargs
        self._operation_count = 0
    
    def save_playlist(self, playlist: Playlist) -> bool:
        """
        Save a playlist to database.
        
        Args:
            playlist: Playlist to save
            
        Returns:
            bool: True if save was successful
        """
        # TODO: Implement database save logic
        # This would involve:
        # 1. Creating/updating playlist record
        # 2. Handling songs as separate records or JSON
        # 3. Managing relationships
        # 4. Using transactions for data integrity
        raise NotImplementedError("Database storage implementation required")
    
    def load_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Load a playlist from database.
        
        Args:
            playlist_id: ID of the playlist to load
            
        Returns:
            Optional[Playlist]: Loaded playlist or None if not found
        """
        # TODO: Implement database load logic
        raise NotImplementedError("Database storage implementation required")
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist from database.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            bool: True if deletion was successful
        """
        # TODO: Implement database delete logic
        raise NotImplementedError("Database storage implementation required")
    
    def list_all_playlists(self) -> List[Playlist]:
        """
        List all playlists in database.
        
        Returns:
            List[Playlist]: List of all playlists
        """
        # TODO: Implement database list logic
        raise NotImplementedError("Database storage implementation required")
    
    def playlist_exists(self, playlist_id: str) -> bool:
        """
        Check if a playlist exists in database.
        
        Args:
            playlist_id: ID of the playlist to check
            
        Returns:
            bool: True if playlist exists
        """
        # TODO: Implement database existence check
        raise NotImplementedError("Database storage implementation required")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get database storage statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing storage statistics
        """
        return {
            'type': 'database',
            'connection_string': self.connection_string,
            'config': self.config,
            'operation_count': self._operation_count,
            'status': 'not_implemented'
        }