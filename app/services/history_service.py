"""
History service for the Music Cover Generator application.
Manages callback history storage and retrieval.
"""
import os
import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app

from app.config import Config
from app.core.utils import JSONUtils, DateTimeUtils, FileUtils


class HistoryService:
    """Service for managing callback history."""
    
    def __init__(self):
        """Initialize history service."""
        self.history_file = self._get_history_file_path()
        FileUtils.ensure_directory_exists(os.path.dirname(self.history_file))
    
    def _get_history_file_path(self) -> str:
        """Get the path to the history JSON file."""
        history_dir = os.path.join(current_app.root_path, 'static', 'history')
        return os.path.join(history_dir, 'history.json')
    
    def load_history(self) -> List[Dict[str, Any]]:
        """
        Load history data from JSON file.
        
        Returns:
            List of history entries
        """
        return JSONUtils.load_json_file(self.history_file, [])
    
    def save_history(self, history_data: List[Dict[str, Any]]) -> bool:
        """
        Save history data to JSON file.
        
        Args:
            history_data: History data to save
            
        Returns:
            True if successful, False otherwise
        """
        return JSONUtils.save_json_file(self.history_file, history_data)
    
    def add_to_history(self, entry: Dict[str, Any]) -> bool:
        """
        Add a new entry to history.
        
        Args:
            entry: History entry to add
            
        Returns:
            True if successful, False otherwise
        """
        history = self.load_history()
        
        # Ensure entry has required fields
        if 'id' not in entry:
            entry['id'] = str(uuid.uuid4())
        if 'timestamp' not in entry:
            entry['timestamp'] = DateTimeUtils.get_current_iso_timestamp()
        
        # Add to beginning of list (most recent first)
        history.insert(0, entry)
        
        # Keep only last N entries to prevent file from growing too large
        if len(history) > Config.HISTORY_MAX_ENTRIES:
            history = history[:Config.HISTORY_MAX_ENTRIES]
        
        # Save the history
        if self.save_history(history):
            # Run cleanup of old entries periodically
            # We'll run cleanup every 10th entry to avoid performance issues
            if len(history) % 10 == 0:
                try:
                    self.cleanup_old_history(days_threshold=Config.HISTORY_CLEANUP_DAYS)
                except Exception as e:
                    current_app.logger.warning(f"Failed to run history cleanup: {e}")
            return True
        return False
    
    def update_history_entry(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing history entry by task_id.
        
        Args:
            task_id: Task ID to update
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        history = self.load_history()
        updated = False
        
        for entry in history:
            if entry.get('task_id') == task_id:
                entry.update(updates)
                entry['last_updated'] = DateTimeUtils.get_current_iso_timestamp()
                updated = True
                break
        
        if updated:
            return self.save_history(history)
        return False
    
    def get_history_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry by ID.
        
        Args:
            entry_id: Entry ID to find
            
        Returns:
            History entry or None if not found
        """
        history = self.load_history()
        for entry in history:
            if entry.get('id') == entry_id or entry.get('task_id') == entry_id:
                return entry
        return None
    
    def get_history_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all history entries for a specific task.
        
        Args:
            task_id: Task ID to filter by
            
        Returns:
            List of history entries for the task
        """
        history = self.load_history()
        return [entry for entry in history if entry.get('task_id') == task_id]
    
    def cleanup_old_history(self, days_threshold: int = 15) -> Tuple[int, int]:
        """
        Remove history entries older than the specified number of days.
        
        Args:
            days_threshold: Number of days after which entries should be removed.
            
        Returns:
            tuple: (removed_count, total_count_after_cleanup)
        """
        history = self.load_history()
        if not history:
            return 0, 0
        
        # Filter entries newer than cutoff
        filtered_history = []
        removed_count = 0
        
        for entry in history:
            timestamp_str = entry.get('timestamp')
            if not timestamp_str:
                # If no timestamp, keep the entry (shouldn't happen)
                filtered_history.append(entry)
                continue
            
            # Check if entry is older than cutoff
            if DateTimeUtils.is_older_than(timestamp_str, days_threshold):
                removed_count += 1
                current_app.logger.info(f"Removing old history entry: {entry.get('id')} from {timestamp_str}")
            else:
                filtered_history.append(entry)
        
        # Save filtered history
        if self.save_history(filtered_history):
            current_app.logger.info(
                f"History cleanup removed {removed_count} entries older than {days_threshold} days. "
                f"{len(filtered_history)} entries remain."
            )
            return removed_count, len(filtered_history)
        else:
            current_app.logger.error("Failed to save history after cleanup")
            return 0, len(history)
    
    def clear_history(self) -> bool:
        """
        Clear all history entries.
        
        Returns:
            True if successful, False otherwise
        """
        empty_history = []
        return self.save_history(empty_history)

    def delete_history_entries(self, entry_ids: List[str]) -> Tuple[int, int]:
        """Delete specific history entries by entry IDs.

        Args:
            entry_ids: List of entry IDs to delete

        Returns:
            tuple: (removed_count, remaining_count)
        """
        history = self.load_history()
        if not history:
            return 0, 0

        ids_set = set(str(entry_id) for entry_id in entry_ids if entry_id is not None)
        if not ids_set:
            return 0, len(history)

        original_count = len(history)
        filtered_history = [entry for entry in history if str(entry.get('id')) not in ids_set]
        removed_count = original_count - len(filtered_history)

        if self.save_history(filtered_history):
            return removed_count, len(filtered_history)
        raise RuntimeError('Failed to save history after deleting entries')
    
    def get_history_stats(self) -> Dict[str, Any]:
        """
        Get statistics about history entries.
        
        Returns:
            Dictionary with history statistics
        """
        history = self.load_history()
        
        if not history:
            return {
                'total': 0,
                'today': 0,
                'success': 0,
                'failed': 0,
                'video_count': 0,
                'audio_count': 0
            }
        
        today = datetime.datetime.utcnow().date().isoformat()
        today_count = 0
        success_count = 0
        failed_count = 0
        video_count = 0
        audio_count = 0
        
        for entry in history:
            # Count entries from today
            timestamp_str = entry.get('timestamp')
            if timestamp_str:
                entry_date = DateTimeUtils.parse_timestamp(timestamp_str)
                if entry_date and entry_date.date().isoformat() == today:
                    today_count += 1
            
            # Count by status
            status_code = entry.get('status_code')
            if status_code == 200 or entry.get('status') == 'success':
                success_count += 1
            elif status_code and status_code != 200:
                failed_count += 1
            
            # Count by type
            if entry.get('is_video_callback', False):
                video_count += 1
            else:
                audio_count += 1
        
        return {
            'total': len(history),
            'today': today_count,
            'success': success_count,
            'failed': failed_count,
            'video_count': video_count,
            'audio_count': audio_count
        }