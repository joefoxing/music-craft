#!/usr/bin/env python3
"""
Comprehensive System Backup Script for Music Cover Generator

This script creates a compressed backup archive of all user data, 
application configurations, and system settings while excluding:
- Python virtual environments (venv/, .venv/, env/, *env*/)
- Temporary caches (__pycache__, *.pyc)
- Non-essential log files
- Development/test scripts
"""

import os
import sys
import tarfile
import zipfile
import hashlib
import json
from datetime import datetime
from pathlib import Path
import shutil
import argparse
import logging
from typing import List, Set, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemBackup:
    """Comprehensive system backup manager."""
    
    def __init__(self, project_root: str = ".", backup_dir: str = "backups"):
        """
        Initialize backup manager.
        
        Args:
            project_root: Root directory of the project
            backup_dir: Directory to store backup archives
        """
        self.project_root = Path(project_root).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Define patterns to exclude
        self.exclude_patterns = [
            # Virtual environments
            r'\.venv/.*',
            r'venv/.*',
            r'env/.*',
            r'.*env.*/.*',
            
            # Python cache files
            r'.*__pycache__/.*',
            r'.*\.pyc$',
            r'.*\.pyo$',
            r'.*\.pyd$',
            
            # IDE and editor files
            r'.*\.vscode/.*',
            r'.*\.idea/.*',
            r'.*\.swp$',
            r'.*\.swo$',
            
            # Temporary and log files
            r'.*\.log$',
            r'.*\.pid$',
            r'.*\.tmp$',
            r'.*temp/.*',
            r'.*tmp/.*',
            
            # Development and test scripts (exclude specific script patterns)
            r'.*debug_.*\.py$',
            r'.*test_.*\.py$',
            r'.*diagnose_.*\.py$',
            r'.*fix_config\.py$',
            r'.*check_config\.py$',
            r'.*start_tunnel.*\.py$',
            r'.*download_cloudflared\.py$',
            
            # Backup directories
            r'backups/.*',
            
            # Screenshots directory (optional - can be included if needed)
            # r'screenshots/.*',
            
            # Git files
            r'.*\.git/.*',
            r'.*\.gitignore$',
            
            # OS-specific files
            r'.*\.DS_Store$',
            r'.*Thumbs\.db$',
        ]
        
        # Define specific files to exclude (in addition to patterns)
        self.exclude_files = [
            'cloudflared.log',
            'cloudflared.pid',
            '.clinerules',  # User rules file - optional to include
        ]
        
        # Define directories to always include (even if they match exclude patterns)
        self.force_include = [
            'app/',
            'instance/',
            '.env',
            'requirements.txt',
            'VERSION',
            'README.md',
        ]
        
        # Backup metadata
        self.metadata = {
            'backup_timestamp': datetime.utcnow().isoformat(),
            'project_name': 'Music Cover Generator',
            'backup_version': '1.0.0',
            'files_included': 0,
            'total_size_bytes': 0,
            'excluded_count': 0,
            'integrity_checksum': None,
        }
    
    def should_exclude(self, file_path: Path) -> bool:
        """
        Determine if a file should be excluded from backup.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be excluded, False otherwise
        """
        # Convert to relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_str = str(rel_path).replace('\\', '/')
        except ValueError:
            # File is outside project root
            return True
        
        # Check force include first
        for include_pattern in self.force_include:
            if rel_str.startswith(include_pattern.rstrip('/')):
                return False
        
        # Check specific files to exclude
        if rel_str in self.exclude_files:
            logger.debug(f"Excluding specific file: {rel_str}")
            return True
        
        # Check exclude patterns
        import re
        for pattern in self.exclude_patterns:
            if re.match(pattern, rel_str):
                logger.debug(f"Excluding by pattern {pattern}: {rel_str}")
                return True
        
        return False
    
    def collect_files(self) -> List[Path]:
        """
        Collect all files to include in backup.
        
        Returns:
            List of file paths to include
        """
        files_to_backup = []
        excluded_count = 0
        
        logger.info(f"Scanning project directory: {self.project_root}")
        
        for root, dirs, filenames in os.walk(self.project_root):
            root_path = Path(root)
            
            # Skip excluded directories early
            dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]
            
            for filename in filenames:
                file_path = root_path / filename
                
                if self.should_exclude(file_path):
                    excluded_count += 1
                    continue
                
                files_to_backup.append(file_path)
        
        self.metadata['excluded_count'] = excluded_count
        self.metadata['files_included'] = len(files_to_backup)
        
        logger.info(f"Collected {len(files_to_backup)} files for backup")
        logger.info(f"Excluded {excluded_count} files/directories")
        
        return files_to_backup
    
    def calculate_file_stats(self, files: List[Path]) -> Dict[str, Any]:
        """
        Calculate statistics about files to backup.
        
        Args:
            files: List of file paths
            
        Returns:
            Dictionary with file statistics
        """
        stats = {
            'total_size': 0,
            'file_types': {},
            'largest_files': [],
            'directories': set(),
        }
        
        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                stats['total_size'] += file_size
                
                # Track file types
                ext = file_path.suffix.lower()
                stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                
                # Track directories
                stats['directories'].add(str(file_path.parent.relative_to(self.project_root)))
                
                # Track largest files
                stats['largest_files'].append((str(file_path.relative_to(self.project_root)), file_size))
                
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Could not stat file {file_path}: {e}")
        
        # Sort largest files
        stats['largest_files'].sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = stats['largest_files'][:10]  # Top 10
        
        self.metadata['total_size_bytes'] = stats['total_size']
        
        return stats
    
    def create_tar_backup(self, files: List[Path], stats: Dict[str, Any]) -> Path:
        """
        Create a compressed tar archive backup.
        
        Args:
            files: List of files to include
            stats: File statistics
            
        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"music_cover_generator_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"Creating backup archive: {backup_path}")
        
        total_files = len(files)
        processed_files = 0
        
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add metadata file
            metadata_content = json.dumps({
                **self.metadata,
                'file_stats': {
                    'total_size_human': self._human_readable_size(stats['total_size']),
                    'file_type_distribution': stats['file_types'],
                    'directory_count': len(stats['directories']),
                    'largest_files': stats['largest_files'],
                }
            }, indent=2)
            
            metadata_file = self.backup_dir / "backup_metadata.json"
            metadata_file.write_text(metadata_content)
            tar.add(metadata_file, arcname="backup_metadata.json")
            metadata_file.unlink()  # Remove temporary file
            
            # Add all files
            for file_path in files:
                try:
                    arcname = str(file_path.relative_to(self.project_root))
                    tar.add(file_path, arcname=arcname)
                    processed_files += 1
                    
                    if processed_files % 100 == 0:
                        logger.info(f"Progress: {processed_files}/{total_files} files added")
                        
                except (OSError, FileNotFoundError) as e:
                    logger.warning(f"Could not add file {file_path}: {e}")
        
        logger.info(f"Backup archive created: {backup_path}")
        logger.info(f"Archive size: {self._human_readable_size(backup_path.stat().st_size)}")
        
        return backup_path
    
    def create_zip_backup(self, files: List[Path], stats: Dict[str, Any]) -> Path:
        """
        Create a zip archive backup (alternative to tar).
        
        Args:
            files: List of files to include
            stats: File statistics
            
        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"music_cover_generator_backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"Creating ZIP backup archive: {backup_path}")
        
        total_files = len(files)
        processed_files = 0
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata
            metadata_content = json.dumps({
                **self.metadata,
                'file_stats': {
                    'total_size_human': self._human_readable_size(stats['total_size']),
                    'file_type_distribution': stats['file_types'],
                    'directory_count': len(stats['directories']),
                    'largest_files': stats['largest_files'],
                }
            }, indent=2)
            
            zipf.writestr("backup_metadata.json", metadata_content)
            
            # Add all files
            for file_path in files:
                try:
                    arcname = str(file_path.relative_to(self.project_root))
                    zipf.write(file_path, arcname=arcname)
                    processed_files += 1
                    
                    if processed_files % 100 == 0:
                        logger.info(f"Progress: {processed_files}/{total_files} files added")
                        
                except (OSError, FileNotFoundError) as e:
                    logger.warning(f"Could not add file {file_path}: {e}")
        
        logger.info(f"ZIP backup archive created: {backup_path}")
        logger.info(f"Archive size: {self._human_readable_size(backup_path.stat().st_size)}")
        
        return backup_path
    
    def verify_backup_integrity(self, backup_path: Path) -> bool:
        """
        Verify the integrity of the backup archive.
        
        Args:
            backup_path: Path to backup archive
            
        Returns:
            True if integrity check passes, False otherwise
        """
        logger.info(f"Verifying backup integrity: {backup_path}")
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        self.metadata['integrity_checksum'] = checksum
        
        # Test archive can be opened and read
        try:
            if backup_path.suffix == '.gz' or '.tar.gz' in backup_path.name:
                with tarfile.open(backup_path, "r:gz") as tar:
                    members = tar.getmembers()
                    logger.info(f"Archive contains {len(members)} items")
                    
                    # Verify metadata file exists
                    metadata_member = None
                    for member in members:
                        if member.name == "backup_metadata.json":
                            metadata_member = member
                            break
                    
                    if metadata_member:
                        logger.info("Metadata file found in archive")
                    else:
                        logger.warning("Metadata file not found in archive")
                        
            elif backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    members = zipf.namelist()
                    logger.info(f"Archive contains {len(members)} items")
                    
                    if "backup_metadata.json" in members:
                        logger.info("Metadata file found in archive")
                    else:
                        logger.warning("Metadata file not found in archive")
            
            logger.info(f"Backup integrity verified successfully")
            logger.info(f"Checksum: {checksum}")
            return True
            
        except (tarfile.TarError, zipfile.BadZipFile, OSError) as e:
            logger.error(f"Backup integrity check failed: {e}")
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        if size_bytes == 0:
            return "0B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        import math
        
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {units[i]}"
    
    def run_backup(self, format: str = "tar") -> Dict[str, Any]:
        """
        Run complete backup process.
        
        Args:
            format: Backup format ('tar' or 'zip')
            
        Returns:
            Dictionary with backup results
        """
        logger.info("=" * 60)
        logger.info("Starting comprehensive system backup")
        logger.info("=" * 60)
        
        # Collect files
        files = self.collect_files()
        
        if not files:
            logger.error("No files found to backup")
            return {"success": False, "error": "No files found"}
        
        # Calculate statistics
        stats = self.calculate_file_stats(files)
        
        logger.info(f"Total size to backup: {self._human_readable_size(stats['total_size'])}")
        logger.info(f"Number of directories: {len(stats['directories'])}")
        
        # Create backup archive
        if format.lower() == "zip":
            backup_path = self.create_zip_backup(files, stats)
        else:
            backup_path = self.create_tar_backup(files, stats)
        
        # Verify integrity
        integrity_ok = self.verify_backup_integrity(backup_path)
        
        # Save metadata separately
        metadata_path = self.backup_dir / f"{backup_path.stem}_metadata.json"
        metadata_path.write_text(json.dumps(self.metadata, indent=2))
        
        # Generate summary
        summary = {
            "success": integrity_ok,
            "backup_path": str(backup_path),
            "metadata_path": str(metadata_path),
            "backup_size": self._human_readable_size(backup_path.stat().st_size),
            "files_included": self.metadata['files_included'],
            "excluded_count": self.metadata['excluded_count'],
            "integrity_checksum": self.metadata['integrity_checksum'],
            "timestamp": self.metadata['backup_timestamp'],
        }
        
        logger.info("=" * 60)
        logger.info("BACKUP COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Backup file: {backup_path}")
        logger.info(f"Files included: {summary['files_included']}")
        logger.info(f"Files excluded: {summary['excluded_count']}")
        logger.info(f"Backup size: {summary['backup_size']}")
        logger.info(f"Integrity check: {'PASSED' if integrity_ok else 'FAILED'}")
        
        if integrity_ok:
            logger.info(f"Checksum: {summary['integrity_checksum']}")
        
        return summary

def main():
    """Main entry point for backup script."""
    parser = argparse.ArgumentParser(
        description="Create comprehensive system backup for Music Cover Generator"
    )
    parser.add_argument(
        "--format",
        choices=["tar", "zip"],
        default="tar",
        help="Backup archive format (default: tar)"
    )
    parser.add_argument(
        "--output-dir",
        default="backups",
        help="Directory to store backup archives (default: backups)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Create backup
        backup = SystemBackup(backup_dir=args.output_dir)
        result = backup.run_backup(format=args.format)
        
        if result["success"]:
            print("\n✅ Backup completed successfully!")
            print(f"📁 Backup file: {result['backup_path']}")
            print(f"📊 Files included: {result['files_included']}")
            print(f"🚫 Files excluded: {result['excluded_count']}")
            print(f"💾 Backup size: {result['backup_size']}")
            print(f"🔒 Integrity checksum: {result['integrity_checksum']}")
            print(f"⏰ Timestamp: {result['timestamp']}")
            print(f"\n📋 Metadata saved to: {result['metadata_path']}")
            print("\nTo restore from backup:")
            print(f"  tar -xzf {result['backup_path']} -C /path/to/restore")
        else:
            print("\n❌ Backup completed but integrity check failed!")
            print("Please verify the backup file manually.")
        
        return 0 if result["success"] else 1
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        print(f"\n❌ Backup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
