"""
Utilities module for the Music Cover Generator application.
Contains shared utility functions and helpers.
"""
import os
import uuid
import datetime
import json
import logging
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename


logger = logging.getLogger(__name__)


class FileUtils:
    """File handling utilities."""
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        Generate a unique filename for uploaded files.
        
        Args:
            original_filename: Original filename
            
        Returns:
            Unique filename with preserved extension
        """
        original_filename = secure_filename(original_filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        return unique_filename
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Get a safe version of a filename for downloads.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename with .mp3 extension if needed
        """
        safe_name = filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._-')
        
        if not safe_name.lower().endswith('.mp3'):
            safe_name += '.mp3'
            
        return safe_name
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to directory
        """
        os.makedirs(directory_path, exist_ok=True)


class DateTimeUtils:
    """Date and time utilities."""
    
    @staticmethod
    def get_current_iso_timestamp() -> str:
        """
        Get current UTC time as ISO format string.
        
        Returns:
            ISO format timestamp string
        """
        return datetime.datetime.utcnow().isoformat()
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime.datetime]:
        """
        Parse timestamp string to datetime object.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            if 'T' in timestamp_str:
                # ISO format with T separator
                return datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Try parsing as simple string
                return datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")
            return None
    
    @staticmethod
    def is_older_than(timestamp_str: str, days: int) -> bool:
        """
        Check if a timestamp is older than specified number of days.
        
        Args:
            timestamp_str: Timestamp string
            days: Number of days threshold
            
        Returns:
            True if timestamp is older than threshold, False otherwise
        """
        timestamp = DateTimeUtils.parse_timestamp(timestamp_str)
        if not timestamp:
            return False
        
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        return timestamp < cutoff_time
    
    @staticmethod
    def format_time_ago(timestamp_str: str) -> str:
        """
        Format timestamp as human-readable time ago string.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Human-readable time ago string
        """
        timestamp = DateTimeUtils.parse_timestamp(timestamp_str)
        if not timestamp:
            return "unknown time"
        
        now = datetime.datetime.utcnow()
        diff = now - timestamp
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"


class JSONUtils:
    """JSON handling utilities."""
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """
        Safely parse JSON string.
        
        Args:
            json_str: JSON string to parse
            default: Default value if parsing fails
            
        Returns:
            Parsed JSON object or default value
        """
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, default: Any = None) -> str:
        """
        Safely serialize object to JSON string.
        
        Args:
            obj: Object to serialize
            default: Default value if serialization fails
            
        Returns:
            JSON string or default value
        """
        try:
            return json.dumps(obj, default=str)
        except (TypeError, ValueError):
            return default if default is not None else "{}"
    
    @staticmethod
    def load_json_file(file_path: str, default: Any = None) -> Any:
        """
        Load JSON data from file.
        
        Args:
            file_path: Path to JSON file
            default: Default value if loading fails
            
        Returns:
            Parsed JSON data or default value
        """
        if not os.path.exists(file_path):
            return default if default is not None else []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            return default if default is not None else []
    
    @staticmethod
    def save_json_file(file_path: str, data: Any) -> bool:
        """
        Save data to JSON file.
        
        Args:
            file_path: Path to JSON file
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except IOError as e:
            logger.error(f"Error saving JSON file {file_path}: {e}")
            return False


class URLUtils:
    """URL handling utilities."""
    
    @staticmethod
    def is_kie_cdn_url(url: str) -> bool:
        """
        Check if URL is from Kie/Suno CDN.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is from Kie/Suno CDN, False otherwise
        """
        kie_domains = [
            'musicfile.kie.ai',
            'kie.ai',
            'cdn1.suno.ai',
            'cdn2.suno.ai'
        ]
        
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        return any(kie_domain in domain for kie_domain in kie_domains)
    
    @staticmethod
    def get_filename_from_url(url: str, default: str = "audio.mp3") -> str:
        """
        Extract filename from URL.
        
        Args:
            url: URL to extract filename from
            default: Default filename if extraction fails
            
        Returns:
            Extracted filename
        """
        import urllib.parse
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)
            
            if filename:
                return filename
        except:
            pass
        
        return default


class ResponseUtils:
    """HTTP response utilities."""
    
    @staticmethod
    def create_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            error_message: Error message
            status_code: HTTP status code
            
        Returns:
            Error response dictionary
        """
        return {
            'error': error_message,
            'code': status_code,
            'timestamp': DateTimeUtils.get_current_iso_timestamp()
        }
    
    @staticmethod
    def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """
        Create standardized success response.
        
        Args:
            data: Response data
            message: Success message
            
        Returns:
            Success response dictionary
        """
        response = {
            'success': True,
            'message': message,
            'timestamp': DateTimeUtils.get_current_iso_timestamp()
        }
        
        if data is not None:
            response['data'] = data
            
        return response