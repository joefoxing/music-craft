# Comprehensive System Backup Documentation

## Overview

The Music Cover Generator includes a comprehensive backup system that archives all user data, application configurations, and system settings while excluding unnecessary files like virtual environments, temporary caches, and log files.

## Backup Scripts

### Primary Backup Script: `backup_system.py`

This is the main backup script that provides:
- **Timestamped backups** with format: `music_cover_backup_YYYYMMDD_HHMMSS.tar.gz`
- **Compression** using gzip (tar.gz) or zip format
- **Integrity verification** with SHA256 checksums
- **Metadata generation** with backup details
- **Smart exclusions** for virtual environments and temporary files

### Advanced Backup Script: `create_backup.py`

An alternative script with more advanced features:
- More granular exclusion patterns
- Detailed file statistics
- Progress reporting
- Configurable backup formats

## What Gets Backed Up

### ✅ INCLUDED (Essential Data)

#### User Data
- Database files: `instance/app.db`
- Uploaded audio files: `app/static/uploads/`
- History data: `app/static/history/`
- Template configurations: `app/static/templates/`

#### Application Configurations
- Environment variables: `.env`
- Configuration files: `app/config.py`
- Requirements: `requirements.txt`
- System version: `VERSION`

#### Application Code
- Core application: `app/` directory
- Routes, services, models, and utilities
- Static assets (CSS, JavaScript, images)
- HTML templates

#### Documentation
- README files and user guides
- API specifications
- System design documents
- Implementation plans

### ❌ EXCLUDED (Non-Essential)

#### Virtual Environments
- `.venv/`, `venv/`, `env/`, `*env*/` directories
- `Pipfile`, `poetry.lock`, `pyvenv.cfg`

#### Temporary Files
- Python cache: `__pycache__/`, `*.pyc`, `*.pyo`
- Log files: `*.log`, `*.pid`
- Temporary files: `*.tmp`

#### Development Files
- Debug scripts: `debug_*.py`
- Test scripts: `test_*.py`, `diagnose_*.py`
- Configuration test scripts: `check_config.py`, `fix_config.py`

#### System Files
- IDE configurations: `.vscode/`, `.idea/`
- Git files: `.git/`, `.gitignore`
- OS-specific files: `.DS_Store`, `Thumbs.db`

## Usage Instructions

### Basic Backup

```bash
# Create a tar.gz backup in the default 'backups' directory
python backup_system.py

# Create a zip backup
python backup_system.py --format zip

# Specify custom output directory
python backup_system.py --output-dir /path/to/backups
```

### Advanced Options

```bash
# Enable verbose output for debugging
python backup_system.py --verbose

# Create backup with specific format
python backup_system.py --format zip --output-dir monthly_backups
```

### Restoring from Backup

#### From tar.gz backup:
```bash
# Extract to current directory
tar -xzf backups/music_cover_backup_20260124_174508.tar.gz

# Extract to specific directory
tar -xzf backup_file.tar.gz -C /path/to/restore
```

#### From zip backup:
```bash
# Extract to current directory
unzip music_cover_backup_20260124_174508.zip

# Extract to specific directory
unzip backup_file.zip -d /path/to/restore
```

## Backup Verification

### Manual Verification

1. **Check metadata file**: Each backup includes a `*_metadata.json` file with:
   - Backup timestamp
   - Number of files included/excluded
   - SHA256 checksum
   - Backup size

2. **Verify checksum**:
   ```bash
   # On Linux/macOS
   sha256sum backup_file.tar.gz
   
   # On Windows (PowerShell)
   Get-FileHash backup_file.tar.gz -Algorithm SHA256
   ```

3. **Test archive integrity**:
   ```bash
   # For tar.gz
   tar -tzf backup_file.tar.gz > /dev/null && echo "Archive is valid"
   
   # For zip
   unzip -t backup_file.zip
   ```

### Automated Verification

The backup script automatically:
1. Calculates SHA256 checksum of the backup file
2. Tests that the archive can be opened and read
3. Reports integrity status (PASSED/FAILED)
4. Saves checksum in metadata for future verification

## Backup Schedule Recommendations

### Development Environment
- **Frequency**: Before major changes or deployments
- **Retention**: Keep last 5 backups
- **Location**: Local `backups/` directory

### Production Environment
- **Frequency**: Daily automated backups
- **Retention**: 30 days of daily, 12 months of monthly
- **Location**: Off-site/cloud storage
- **Encryption**: Consider encrypting sensitive backups

### Manual Triggers
- Before system upgrades
- Before database migrations
- Before major configuration changes
- Before deleting user data

## Monitoring and Maintenance

### Check Backup Status
```bash
# List available backups
ls -la backups/

# Check backup sizes
du -sh backups/*

# View latest metadata
cat backups/*_metadata.json | jq .  # If jq is installed
```

### Cleanup Old Backups
```bash
# Keep only last 7 days of backups (Linux/macOS)
find backups/ -name "music_cover_backup_*.tar.gz" -mtime +7 -delete
find backups/ -name "music_cover_backup_*.zip" -mtime +7 -delete
find backups/ -name "*_metadata.json" -mtime +7 -delete

# Windows PowerShell equivalent
Get-ChildItem backups\*_backup_* | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

### Automation Script Example

Create `automated_backup.bat` (Windows) or `automated_backup.sh` (Linux):

```bash
#!/bin/bash
# automated_backup.sh
BACKUP_DIR="/path/to/backups"
LOG_FILE="/var/log/backup.log"

echo "$(date): Starting backup" >> $LOG_FILE
python backup_system.py --output-dir $BACKUP_DIR >> $LOG_FILE 2>&1
echo "$(date): Backup completed" >> $LOG_FILE

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "music_cover_backup_*" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

1. **"No files found to backup"**
   - Check that you're in the correct project directory
   - Verify the script has read permissions

2. **Backup size is too large**
   - Check if large temporary files are being included
   - Verify exclusions are working correctly
   - Consider excluding `screenshots/` directory if not needed

3. **Integrity check fails**
   - Disk space issues during backup creation
   - File permissions preventing read access
   - Network issues for remote backups

4. **Windows encoding errors**
   - Script uses ASCII-only output for compatibility
   - If issues persist, run with `--verbose` flag

### Testing Backup Restoration

Regularly test backup restoration:
1. Create a test backup
2. Extract to a temporary location
3. Verify critical files are present
4. Test application functionality with restored data

## Security Considerations

### Sensitive Data
- `.env` files may contain API keys and secrets
- Database may contain user information
- Consider encryption for production backups

### Access Control
- Restrict backup directory permissions
- Use secure transfer methods for off-site backups
- Implement backup rotation to prevent accumulation

### Compliance
- Follow data retention policies
- Ensure backups comply with privacy regulations
- Document backup procedures for audit purposes

## Performance Notes

- **Backup size**: ~200MB for typical installation
- **Backup time**: 1-5 minutes depending on system
- **Compression ratio**: ~60-70% reduction with gzip
- **Memory usage**: Minimal (streaming compression)

## Customization

### Modifying Exclusions

Edit `backup_system.py` to adjust exclusion patterns:

```python
# Add custom exclusions
exclude_files = [
    'cloudflared.log', 'cloudflared.pid',
    '.clinerules',
    # Add your custom files here
]

# Add custom patterns
if 'custom_pattern' in rel_path:
    return True
```

### Adding Custom Inclusions

To force-include specific files/directories:
```python
# Add to force_include logic
if rel_path.startswith('custom_data/'):
    return False
```

## Support

For backup-related issues:
1. Check the metadata file for error details
2. Run with `--verbose` flag for debugging
3. Verify disk space and permissions
4. Test with smaller subset of files first

## Version History

- **v1.0.0** (2026-01-24): Initial release
  - Comprehensive backup with exclusions
  - Integrity verification with checksums
  - Metadata generation
  - Support for tar.gz and zip formats

---

*Last updated: 2026-01-24*  
*Backup system version: 1.0.0*