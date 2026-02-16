"""
Audio Library service for the Music Cover Generator application.
Manages user audio library operations including CRUD operations for audio items.
"""
import os
import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app, request
from flask_login import current_user
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload

from app import db
from app.models import AudioLibrary, Playlist, PlaylistAudioLibrary
from app.core.utils import ResponseUtils, DateTimeUtils, FileUtils, URLUtils
from app.services.lyrics_extraction_service import LyricsExtractionService
from app.services.lyrics_job_service import LyricsJobService


class AudioLibraryService:
    """Service for managing user audio library operations."""
    
    def __init__(self):
        """Initialize audio library service."""
        pass
    
    def add_to_library(self, audio_data: Dict[str, Any]) -> Tuple[bool, str, Optional[AudioLibrary]]:
        """
        Add audio to user's library.
        
        Args:
            audio_data: Audio metadata and information
            
        Returns:
            Tuple of (success, error_message, audio_library_item)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required", None
        
        try:
            # Extract required fields
            title = audio_data.get('title')
            if not title:
                return False, "Title is required", None

            lyrics = audio_data.get('lyrics')
            lyrics_source = audio_data.get('lyrics_source', 'user' if lyrics else None)
            source_type = audio_data.get('source_type', 'upload')

            should_extract_lyrics = (
                not lyrics
                and source_type == 'upload'
                and bool(audio_data.get('audio_url'))
                and audio_data.get('extract_lyrics', True)
            )
            lyrics_language = audio_data.get('lyrics_language')

            lyrics_extraction_status = 'not_requested'
            lyrics_extraction_error = None

            if should_extract_lyrics and current_app.config.get('LYRICS_EXTRACTION_ASYNC_ENABLED', True):
                lyrics_extraction_status = 'queued'

            if should_extract_lyrics and not current_app.config.get('LYRICS_EXTRACTION_ASYNC_ENABLED', True):
                lyrics_extraction_status = 'processing'
                extractor = LyricsExtractionService()
                extracted_lyrics, extracted_source, extraction_error = extractor.extract_lyrics(
                    audio_url=audio_data.get('audio_url'),
                    whisper_language_override=lyrics_language
                )
                if extracted_lyrics:
                    lyrics = extracted_lyrics
                    lyrics_source = extracted_source
                    lyrics_extraction_status = 'completed'
                else:
                    lyrics_extraction_status = 'failed'
                    lyrics_extraction_error = extraction_error
                    if extraction_error:
                        current_app.logger.info(
                            f"Lyrics extraction skipped for '{title}': {extraction_error}"
                        )
            
            # Create audio library entry
            audio_item = AudioLibrary(
                user_id=current_user.id,
                title=title,
                artist=audio_data.get('artist'),
                duration=audio_data.get('duration'),
                file_size=audio_data.get('file_size'),
                file_format=audio_data.get('file_format'),
                audio_url=audio_data.get('audio_url'),
                original_filename=audio_data.get('original_filename'),
                genre=audio_data.get('genre'),
                album=audio_data.get('album'),
                year=audio_data.get('year'),
                tags=audio_data.get('tags', []),
                lyrics=lyrics,
                lyrics_source=lyrics_source,
                lyrics_extraction_status=lyrics_extraction_status,
                lyrics_extraction_error=lyrics_extraction_error,
                source_type=source_type,
                source_reference=audio_data.get('source_reference'),
                processing_status=audio_data.get('processing_status', 'ready')
            )
            
            db.session.add(audio_item)
            db.session.commit()

            if should_extract_lyrics and current_app.config.get('LYRICS_EXTRACTION_ASYNC_ENABLED', True):
                queued = LyricsJobService.enqueue_extraction(
                    audio_item.id,
                    whisper_language_override=lyrics_language
                )
                if not queued:
                    current_app.logger.info(f"Lyrics extraction already queued/running for audio item {audio_item.id}")
            
            current_app.logger.info(f"Audio item added to library: {audio_item.id} for user {current_user.id}")
            return True, "", audio_item
            
        except Exception as e:
            current_app.logger.error(f"Error adding audio to library: {e}")
            db.session.rollback()
            return False, f"Failed to add audio to library: {str(e)}", None
    
    def get_user_audio_library(self, page: int = 1, per_page: int = 20, 
                              sort_by: str = 'created_at', sort_order: str = 'desc',
                              search: str = None, filters: Dict[str, Any] = None) -> Tuple[List[AudioLibrary], int]:
        """
        Get user's audio library with pagination, sorting, and filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            search: Search query for title, artist, album
            filters: Additional filters (genre, year, tags, etc.)
            
        Returns:
            Tuple of (audio_items_list, total_count)
        """
        if not current_user.is_authenticated:
            return [], 0
        
        try:
            # Build query
            query = AudioLibrary.query.filter_by(user_id=current_user.id)
            
            # Apply search
            if search:
                search_filter = or_(
                    AudioLibrary.title.ilike(f"%{search}%"),
                    AudioLibrary.artist.ilike(f"%{search}%"),
                    AudioLibrary.album.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # Apply filters
            if filters:
                if filters.get('genre'):
                    query = query.filter(AudioLibrary.genre == filters['genre'])
                
                if filters.get('year'):
                    query = query.filter(AudioLibrary.year == filters['year'])
                
                if filters.get('tags'):
                    # Filter by tags (assuming tags is a JSON array)
                    for tag in filters['tags']:
                        query = query.filter(AudioLibrary.tags.contains([tag]))
                
                if filters.get('source_type'):
                    query = query.filter(AudioLibrary.source_type == filters['source_type'])
                
                if filters.get('is_favorite') is not None:
                    query = query.filter(AudioLibrary.is_favorite == filters['is_favorite'])
                
                if filters.get('playlist_id'):
                    # Join with PlaylistAudioLibrary to filter by playlist
                    query = query.join(PlaylistAudioLibrary).filter(
                        PlaylistAudioLibrary.playlist_id == filters['playlist_id']
                    )
            
            # Apply sorting
            sort_field = getattr(AudioLibrary, sort_by, AudioLibrary.created_at)
            if sort_order.lower() == 'desc':
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            audio_items = query.offset(offset).limit(per_page).all()
            
            return audio_items, total_count
            
        except Exception as e:
            current_app.logger.error(f"Error getting user audio library: {e}")
            return [], 0
    
    def get_audio_item(self, audio_id: str) -> Optional[AudioLibrary]:
        """
        Get a specific audio item from user's library.
        
        Args:
            audio_id: Audio library item ID
            
        Returns:
            AudioLibrary item or None if not found
        """
        if not current_user.is_authenticated:
            return None
        
        try:
            audio_item = AudioLibrary.query.filter_by(
                id=audio_id, 
                user_id=current_user.id
            ).first()
            
            return audio_item
            
        except Exception as e:
            current_app.logger.error(f"Error getting audio item {audio_id}: {e}")
            return None
    
    def update_audio_item(self, audio_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an audio item in the library.
        
        Args:
            audio_id: Audio library item ID
            updates: Fields to update
            
        Returns:
            Tuple of (success, error_message)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        try:
            audio_item = self.get_audio_item(audio_id)
            if not audio_item:
                return False, "Audio item not found"
            
            # Update allowed fields
            allowed_fields = [
                'title', 'artist', 'genre', 'album', 'year', 'tags', 
                'is_favorite', 'audio_url', 'lyrics', 'lyrics_source'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(audio_item, field):
                    setattr(audio_item, field, value)
            
            audio_item.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            current_app.logger.info(f"Audio item updated: {audio_id}")
            return True, ""
            
        except Exception as e:
            current_app.logger.error(f"Error updating audio item {audio_id}: {e}")
            db.session.rollback()
            return False, f"Failed to update audio item: {str(e)}"
    
    def delete_audio_item(self, audio_id: str) -> Tuple[bool, str]:
        """
        Delete an audio item from the library.
        
        Args:
            audio_id: Audio library item ID
            
        Returns:
            Tuple of (success, error_message)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        try:
            audio_item = self.get_audio_item(audio_id)
            if not audio_item:
                return False, "Audio item not found"
            
            # Remove from playlists first
            PlaylistAudioLibrary.query.filter_by(audio_library_id=audio_id).delete()
            
            # Delete the audio item
            db.session.delete(audio_item)
            db.session.commit()
            
            current_app.logger.info(f"Audio item deleted: {audio_id}")
            return True, ""
            
        except Exception as e:
            current_app.logger.error(f"Error deleting audio item {audio_id}: {e}")
            db.session.rollback()
            return False, f"Failed to delete audio item: {str(e)}"
    
    def increment_play_count(self, audio_id: str) -> bool:
        """
        Increment play count for an audio item.
        
        Args:
            audio_id: Audio library item ID
            
        Returns:
            True if successful, False otherwise
        """
        if not current_user.is_authenticated:
            return False
        
        try:
            audio_item = self.get_audio_item(audio_id)
            if audio_item:
                audio_item.increment_play_count()
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error incrementing play count for {audio_id}: {e}")
            db.session.rollback()
            return False
    
    def toggle_favorite(self, audio_id: str) -> Tuple[bool, str, Optional[bool]]:
        """
        Toggle favorite status of an audio item.
        
        Args:
            audio_id: Audio library item ID
            
        Returns:
            Tuple of (success, error_message, is_favorite)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required", None
        
        try:
            audio_item = self.get_audio_item(audio_id)
            if not audio_item:
                return False, "Audio item not found", None
            
            audio_item.is_favorite = not audio_item.is_favorite
            audio_item.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            current_app.logger.info(f"Favorite toggled for audio item {audio_id}: {audio_item.is_favorite}")
            return True, "", audio_item.is_favorite
            
        except Exception as e:
            current_app.logger.error(f"Error toggling favorite for {audio_id}: {e}")
            db.session.rollback()
            return False, f"Failed to toggle favorite: {str(e)}", None

    def retry_lyrics_extraction(self, audio_id: str) -> Tuple[bool, str]:
        """Retry async lyrics extraction for an audio item."""
        if not current_user.is_authenticated:
            return False, "Authentication required"

        try:
            audio_item = self.get_audio_item(audio_id)
            if not audio_item:
                return False, "Audio item not found"

            if not audio_item.audio_url:
                return False, "Audio URL is required for lyrics extraction"

            if audio_item.source_type != 'upload':
                return False, "Lyrics extraction retry is only supported for uploaded audio"

            audio_item.lyrics_extraction_status = 'queued'
            audio_item.lyrics_extraction_error = None
            db.session.commit()

            queued = LyricsJobService.enqueue_extraction(audio_item.id)
            if not queued:
                return False, "Lyrics extraction is already in progress"

            return True, ""

        except Exception as e:
            current_app.logger.error(f"Error retrying lyrics extraction for {audio_id}: {e}")
            db.session.rollback()
            return False, f"Failed to retry lyrics extraction: {str(e)}"
    
    def get_library_stats(self) -> Dict[str, Any]:
        """
        Get statistics about user's audio library.
        
        Returns:
            Dictionary with library statistics
        """
        if not current_user.is_authenticated:
            return {}
        
        try:
            # Get total count
            total_count = AudioLibrary.query.filter_by(user_id=current_user.id).count()
            
            # Get favorite count
            favorite_count = AudioLibrary.query.filter_by(
                user_id=current_user.id, 
                is_favorite=True
            ).count()
            
            # Get source type counts
            source_counts = db.session.query(
                AudioLibrary.source_type,
                func.count(AudioLibrary.id)
            ).filter_by(user_id=current_user.id).group_by(AudioLibrary.source_type).all()
            
            source_type_counts = {source: count for source, count in source_counts}
            
            # Get total duration
            total_duration_result = db.session.query(
                func.sum(AudioLibrary.duration)
            ).filter_by(user_id=current_user.id).scalar()
            
            total_duration = total_duration_result or 0
            
            # Get recent additions (last 7 days)
            week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            recent_count = AudioLibrary.query.filter(
                and_(
                    AudioLibrary.user_id == current_user.id,
                    AudioLibrary.created_at >= week_ago
                )
            ).count()
            
            # Get genre distribution
            genre_results = db.session.query(
                AudioLibrary.genre,
                func.count(AudioLibrary.id)
            ).filter(
                and_(
                    AudioLibrary.user_id == current_user.id,
                    AudioLibrary.genre.isnot(None)
                )
            ).group_by(AudioLibrary.genre).all()
            
            genre_distribution = {genre: count for genre, count in genre_results}
            
            return {
                'total_count': total_count,
                'favorite_count': favorite_count,
                'total_duration': total_duration,
                'recent_additions': recent_count,
                'source_type_counts': source_type_counts,
                'genre_distribution': genre_distribution
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting library stats: {e}")
            return {}
    
    def add_from_history(self, history_entry: Dict[str, Any]) -> Tuple[bool, str, Optional[AudioLibrary]]:
        """
        Add audio from history entry to library.
        
        Args:
            history_entry: History callback entry
            
        Returns:
            Tuple of (success, error_message, audio_library_item)
        """
        try:
            # Extract audio data from history entry
            audio_data = self._extract_audio_data_from_history(history_entry)
            if not audio_data:
                return False, "No audio data found in history entry", None
            
            # Add to library
            return self.add_to_library(audio_data)
            
        except Exception as e:
            current_app.logger.error(f"Error adding audio from history: {e}")
            return False, f"Failed to add audio from history: {str(e)}", None
    
    def _extract_audio_data_from_history(self, history_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract audio data from history callback entry.
        
        Args:
            history_entry: History callback entry
            
        Returns:
            Audio data dictionary or None
        """
        try:
            # Extract tracks from history entry
            tracks = history_entry.get('tracks', [])
            if not tracks:
                return None
            
            # Use the first track for now (can be extended for multiple tracks)
            track = tracks[0]
            
            # Build audio data
            audio_data = {
                'title': track.get('title', 'Generated Track'),
                'artist': 'AI Generated',
                'audio_url': track.get('audioUrl') or track.get('sourceAudioUrl'),
                'duration': track.get('duration'),
                'lyrics': track.get('prompt') or track.get('lyrics'),
                'lyrics_source': 'metadata' if track.get('lyrics') else ('user' if track.get('prompt') else None),
                'source_type': 'generated',
                'source_reference': history_entry.get('task_id'),
                'processing_status': 'ready',
                'tags': [track.get('tags', 'ai-generated')] if track.get('tags') else ['ai-generated']
            }
            
            return audio_data
            
        except Exception as e:
            current_app.logger.error(f"Error extracting audio data from history: {e}")
            return None
    
    def create_playlist(self, name: str, description: str = None) -> Tuple[bool, str, Optional[Playlist]]:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            
        Returns:
            Tuple of (success, error_message, playlist)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required", None
        
        try:
            playlist = Playlist(
                user_id=current_user.id,
                name=name,
                description=description
            )
            
            db.session.add(playlist)
            db.session.commit()
            
            current_app.logger.info(f"Playlist created: {playlist.id} for user {current_user.id}")
            return True, "", playlist
            
        except Exception as e:
            current_app.logger.error(f"Error creating playlist: {e}")
            db.session.rollback()
            return False, f"Failed to create playlist: {str(e)}", None
    
    def get_user_playlists(self) -> List[Playlist]:
        """
        Get all playlists for the current user.
        
        Returns:
            List of Playlist objects
        """
        if not current_user.is_authenticated:
            return []
        
        try:
            playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(
                desc(Playlist.created_at)
            ).all()
            
            return playlists
            
        except Exception as e:
            current_app.logger.error(f"Error getting user playlists: {e}")
            return []
    
    def add_to_playlist(self, playlist_id: str, audio_id: str) -> Tuple[bool, str]:
        """
        Add audio item to playlist.
        
        Args:
            playlist_id: Playlist ID
            audio_id: Audio library item ID
            
        Returns:
            Tuple of (success, error_message)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        try:
            # Verify ownership
            playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
            if not playlist:
                return False, "Playlist not found"
            
            audio_item = self.get_audio_item(audio_id)
            if not audio_item:
                return False, "Audio item not found"
            
            # Check if already in playlist
            existing = PlaylistAudioLibrary.query.filter_by(
                playlist_id=playlist_id,
                audio_library_id=audio_id
            ).first()
            
            if existing:
                return False, "Audio item already in playlist"
            
            # Get next position
            max_position = db.session.query(
                func.max(PlaylistAudioLibrary.position)
            ).filter_by(playlist_id=playlist_id).scalar()
            
            next_position = (max_position or 0) + 1
            
            # Add to playlist
            playlist_audio = PlaylistAudioLibrary(
                playlist_id=playlist_id,
                audio_library_id=audio_id,
                position=next_position
            )
            
            db.session.add(playlist_audio)
            db.session.commit()
            
            current_app.logger.info(f"Audio {audio_id} added to playlist {playlist_id}")
            return True, ""
            
        except Exception as e:
            current_app.logger.error(f"Error adding audio to playlist: {e}")
            db.session.rollback()
            return False, f"Failed to add to playlist: {str(e)}"
    
    def remove_from_playlist(self, playlist_id: str, audio_id: str) -> Tuple[bool, str]:
        """
        Remove audio item from playlist.
        
        Args:
            playlist_id: Playlist ID
            audio_id: Audio library item ID
            
        Returns:
            Tuple of (success, error_message)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        try:
            # Verify ownership
            playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
            if not playlist:
                return False, "Playlist not found"
            
            # Remove from playlist
            deleted = PlaylistAudioLibrary.query.filter_by(
                playlist_id=playlist_id,
                audio_library_id=audio_id
            ).delete()
            
            if not deleted:
                return False, "Audio item not found in playlist"
            
            db.session.commit()
            
            current_app.logger.info(f"Audio {audio_id} removed from playlist {playlist_id}")
            return True, ""
            
        except Exception as e:
            current_app.logger.error(f"Error removing audio from playlist: {e}")
            db.session.rollback()
            return False, f"Failed to remove from playlist: {str(e)}"

    def delete_playlist(self, playlist_id: str) -> Tuple[bool, str]:
        """
        Delete a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            Tuple of (success, error_message)
        """
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        try:
            # Verify ownership
            playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
            if not playlist:
                return False, "Playlist not found"
            
            # Remove all songs from playlist (explicitly delete associations)
            PlaylistAudioLibrary.query.filter_by(playlist_id=playlist_id).delete()
            
            # Delete playlist
            db.session.delete(playlist)
            db.session.commit()
            
            current_app.logger.info(f"Playlist deleted: {playlist_id}")
            return True, ""
            
        except Exception as e:
            current_app.logger.error(f"Error deleting playlist: {e}")
            db.session.rollback()
            return False, f"Failed to delete playlist: {str(e)}"