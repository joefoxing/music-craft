# Backup System - Quick Start Guide

## One-Minute Setup

### 1. Create Your First Backup
```bash
# Run from the project root directory
python backup_system.py
```

### 2. Check the Result
```bash
# View created backup
dir backups\
# or on Linux/macOS: ls -la backups/
```

### 3. Verify Backup Integrity
```bash
# The script automatically verifies integrity
# Check the metadata file for details
type backups\*_metadata.json
```

## Essential Commands

### Basic Backup
```bash
# Default tar.gz format
python backup_system.py

# Zip format
python backup_system.py --format zip

# Custom output directory
python backup_system.py --output-dir "D:\Backups\MusicCover"
```

### Restore Backup
```bash
# Extract tar.gz backup
tar -xzf backups\music_cover_backup_*.tar.gz

# Extract zip backup
unzip backups\music_cover_backup_*.zip
```

### Advanced Usage
```bash
# Verbose mode (see what's being backed up)
python backup_system.py --verbose

# Test with small backup (create in test directory)
python backup_system.py --output-dir test_backup
```

## What Gets Backed Up? (Summary)

**✅ INCLUDED:**
- User data (database, uploads, history, templates)
- Config files (.env, config.py, requirements.txt)
- Application code (app/ directory)
- Documentation

**❌ EXCLUDED:**
- Virtual environments (.venv/, venv/, etc.)
- Cache files (__pycache__, *.pyc)
- Log files (*.log, *.pid)
- Development scripts

## Automated Backup Schedule

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `backup_system.py --output-dir "D:\Backups\MusicCover"`

### Linux/macOS Cron Job
```bash
# Edit crontab
crontab -e

# Add line for daily backup at 2 AM
0 2 * * * cd /path/to/project && python backup_system.py --output-dir /var/backups/music_cover
```

## Emergency Restoration

### If System Fails:
1. **Locate latest backup**: Check `backups/` directory
2. **Verify backup**: Check `*_metadata.json` file
3. **Stop application**: Ensure app is not running
4. **Restore files**: Extract backup to project root
5. **Verify restoration**: Check critical files exist
6. **Restart application**: Start the Music Cover Generator

### Critical Files to Verify:
- `instance/app.db` (database)
- `.env` (configuration)
- `app/static/uploads/` (user uploads)
- `app/static/templates/` (templates)

## Troubleshooting Quick Fixes

### Issue: "No files found to backup"
```bash
# Check current directory
cd e:\Developer\Lyric_Cover
python backup_system.py
```

### Issue: Backup too large
```bash
# Check what's being included
python backup_system.py --verbose
```

### Issue: Permission errors
```bash
# Run as administrator (Windows)
# or use sudo (Linux/macOS)
```

## Next Steps

1. **Test restoration** in a safe environment
2. **Set up automation** for regular backups
3. **Configure off-site storage** for important backups
4. **Document your backup procedures** for your team

## Need Help?

- Check detailed documentation: `BACKUP_SYSTEM_DOCUMENTATION.md`
- Review backup metadata files for details
- Test with `--verbose` flag to see process details

---

*Last updated: 2026-01-24*  
*For detailed documentation, see BACKUP_SYSTEM_DOCUMENTATION.md*