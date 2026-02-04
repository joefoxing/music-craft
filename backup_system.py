#!/usr/bin/env python3
"""
Comprehensive System Backup for Music Cover Generator

Creates a timestamped, compressed backup archive of:
- User data (database, uploads, history, templates)
- Application configurations (.env, config files)
- System settings (VERSION, documentation)

Excludes:
- Python virtual environments (venv/, .venv/, env/, *env*/)
- Temporary caches (__pycache__, *.pyc)
- Log files (*.log, *.pid)
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
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def should_exclude(path: Path, root: Path) -> bool:
    """Determine if a path should be excluded from backup."""
    rel_path = str(path.relative_to(root)).replace('\\', '/')
    
    # Exclude virtual environments
    if any(pattern in rel_path for pattern in ['/.venv/', '/venv/', '/env/', '/.envs/']):
        return True
    
    # Exclude cache directories
    if '/__pycache__/' in rel_path or rel_path.endswith('/__pycache__'):
        return True
    
    # Exclude Python cache files
    if rel_path.endswith('.pyc') or rel_path.endswith('.pyo'):
        return True
    
    # Exclude specific files
    exclude_files = [
        'cloudflared.log', 'cloudflared.pid',
        '.clinerules',  # Optional: include if you want to backup rules
    ]
    if os.path.basename(path) in exclude_files:
        return True
    
    # Exclude development/test scripts
    dev_scripts = [
        'debug_', 'test_', 'diagnose_', 'fix_config', 'check_config',
        'start_tunnel', 'download_cloudflared', 'add_templates',
        'generate_templates', 'merge_templates', 'create_new_templates',
        'final_merge', 'final_add', 'add_missing', 'add_all_templates',
        'run_new_connector'
    ]
    filename = path.name.lower()
    if any(script in filename for script in dev_scripts):
        return True
    
    return False

def collect_backup_files(project_root: Path):
    """Collect all files to include in backup."""
    files_to_backup = []
    excluded_count = 0
    
    logger.info(f"Scanning project: {project_root}")
    
    for root_dir, dirs, files in os.walk(project_root):
        root_path = Path(root_dir)
        
        # Filter directories to exclude
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d, project_root)]
        
        for file in files:
            file_path = root_path / file
            
            if should_exclude(file_path, project_root):
                excluded_count += 1
                continue
            
            files_to_backup.append(file_path)
    
    logger.info(f"Found {len(files_to_backup)} files to backup")
    logger.info(f"Excluded {excluded_count} files/directories")
    
    return files_to_backup, excluded_count

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def create_backup_archive(files: list, project_root: Path, backup_dir: Path, format: str = 'tar') -> Path:
    """Create compressed backup archive."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'zip':
        backup_name = f"music_cover_backup_{timestamp}.zip"
        backup_path = backup_dir / backup_name
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                arcname = str(file_path.relative_to(project_root))
                zipf.write(file_path, arcname)
                logger.debug(f"Added: {arcname}")
    
    else:  # tar.gz
        backup_name = f"music_cover_backup_{timestamp}.tar.gz"
        backup_path = backup_dir / backup_name
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for file_path in files:
                arcname = str(file_path.relative_to(project_root))
                tar.add(file_path, arcname=arcname)
                logger.debug(f"Added: {arcname}")
    
    return backup_path

def verify_backup_integrity(backup_path: Path) -> tuple:
    """Verify backup archive integrity and calculate checksum."""
    logger.info(f"Verifying backup: {backup_path}")
    
    # Calculate checksum
    checksum = calculate_checksum(backup_path)
    
    # Test archive can be opened
    try:
        if backup_path.suffix == '.gz' or '.tar.gz' in backup_path.name:
            with tarfile.open(backup_path, 'r:gz') as tar:
                file_count = len(tar.getmembers())
                logger.info(f"Archive contains {file_count} files")
                return True, checksum, file_count
        elif backup_path.suffix == '.zip':
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                file_count = len(zipf.namelist())
                logger.info(f"Archive contains {file_count} files")
                return True, checksum, file_count
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        return False, checksum, 0
    
    return False, checksum, 0

def create_backup_metadata(backup_path: Path, files_count: int, excluded_count: int, 
                          checksum: str, format: str) -> Path:
    """Create metadata JSON file for the backup."""
    metadata = {
        'backup_timestamp': datetime.utcnow().isoformat(),
        'backup_file': backup_path.name,
        'backup_format': format,
        'files_included': files_count,
        'files_excluded': excluded_count,
        'integrity_checksum': checksum,
        'system': 'Music Cover Generator',
        'version': get_version(),
        'backup_size_bytes': backup_path.stat().st_size,
        'backup_size_human': human_readable_size(backup_path.stat().st_size),
    }
    
    metadata_path = backup_path.parent / f"{backup_path.stem}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_path

def get_version() -> str:
    """Get system version from VERSION file."""
    version_file = Path('VERSION')
    if version_file.exists():
        return version_file.read_text().strip()
    return 'unknown'

def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def main():
    parser = argparse.ArgumentParser(description='Create comprehensive system backup')
    parser.add_argument('--format', choices=['tar', 'zip'], default='tar',
                       help='Backup format (default: tar.gz)')
    parser.add_argument('--output-dir', default='backups',
                       help='Directory to store backups (default: backups)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Setup paths
    project_root = Path('.').resolve()
    backup_dir = Path(args.output_dir).resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("COMPREHENSIVE SYSTEM BACKUP")
    print("=" * 60)
    
    # Collect files
    files, excluded_count = collect_backup_files(project_root)
    
    if not files:
        print("[ERROR] No files found to backup")
        return 1
    
    # Create backup archive
    print(f"\n[INFO] Creating {args.format.upper()} backup archive...")
    backup_path = create_backup_archive(files, project_root, backup_dir, args.format)
    
    # Verify integrity
    print("\n[INFO] Verifying backup integrity...")
    integrity_ok, checksum, file_count = verify_backup_integrity(backup_path)
    
    # Create metadata
    metadata_path = create_backup_metadata(
        backup_path, len(files), excluded_count, checksum, args.format
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    print(f"[SUCCESS] Backup created: {backup_path.name}")
    print(f"[INFO] Files included: {len(files)}")
    print(f"[INFO] Files excluded: {excluded_count}")
    print(f"[INFO] Backup size: {human_readable_size(backup_path.stat().st_size)}")
    print(f"[INTEGRITY] {'PASSED' if integrity_ok else 'FAILED'}")
    print(f"[CHECKSUM] {checksum}")
    print(f"[METADATA] {metadata_path.name}")
    
    if integrity_ok:
        print("\n[SUCCESS] Backup completed successfully!")
        print(f"\nTo restore from backup:")
        if args.format == 'tar':
            print(f"  tar -xzf {backup_path} -C /path/to/restore")
        else:
            print(f"  unzip {backup_path} -d /path/to/restore")
        return 0
    else:
        print("\n[WARNING] Backup created but integrity check failed!")
        print("Please verify the backup file manually.")
        return 1

if __name__ == '__main__':
    sys.exit(main())