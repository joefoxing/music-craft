"""
Database models for the Music Cover Generator application.
"""
from datetime import datetime, timedelta
import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import CHAR, TypeDecorator
from app import db, bcrypt


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.UUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        return value


class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    display_name = db.Column(db.String(100))
    avatar_url = db.Column(db.Text)
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    verification_token_expires_at = db.Column(db.DateTime)
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires_at = db.Column(db.DateTime)
    
    # Account security
    last_login_at = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    oauth_connections = db.relationship('OAuthConnection', backref='user', lazy=True, cascade='all, delete-orphan')
    auth_audit_logs = db.relationship('AuthAuditLog', backref='user', lazy=True)
    user_roles = db.relationship('UserRole', foreign_keys='UserRole.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password=None, display_name=None):
        # Generate UUID for the id field immediately
        self.id = str(uuid.uuid4())
        self.email = email.lower().strip()
        self.display_name = display_name or email.split('@')[0]
        
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self, expires_in=86400):  # 24 hours
        """Generate a verification token for email confirmation."""
        self.verification_token = str(uuid.uuid4())
        self.verification_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return self.verification_token
    
    def verify_email(self, token):
        """Verify email using the provided token."""
        if (self.verification_token == token and 
            self.verification_token_expires_at and 
            self.verification_token_expires_at > datetime.utcnow()):
            self.email_verified = True
            self.verification_token = None
            self.verification_token_expires_at = None
            return True
        return False
    
    def generate_reset_token(self, expires_in=3600):  # 1 hour
        """Generate a password reset token."""
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return self.reset_token
    
    def reset_password(self, token, new_password):
        """Reset password using the provided token."""
        if (self.reset_token == token and 
            self.reset_token_expires_at and 
            self.reset_token_expires_at > datetime.utcnow()):
            self.set_password(new_password)
            self.reset_token = None
            self.reset_token_expires_at = None
            self.failed_login_attempts = 0
            self.locked_until = None
            return True
        return False
    
    def record_login(self, success=True):
        """Record a login attempt."""
        if success:
            self.last_login_at = datetime.utcnow()
            self.failed_login_attempts = 0
            self.locked_until = None
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
                self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def is_locked(self):
        """Check if the account is currently locked."""
        if self.locked_until:
            return self.locked_until > datetime.utcnow()
        return False
    
    def to_dict(self):
        """Convert user object to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'email_verified': self.email_verified,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def get_role_names(self):
        role_ids = [ur.role_id for ur in UserRole.query.filter_by(user_id=self.id).all()]
        if not role_ids:
            return set()
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        return {r.name for r in roles}

    def has_permission(self, perm_name: str) -> bool:
        role_ids = [ur.role_id for ur in UserRole.query.filter_by(user_id=self.id).all()]
        if not role_ids:
            return False
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        for role in roles:
            for perm in role.permissions:
                if perm.name == perm_name:
                    return True
        return False


class OAuthConnection(db.Model):
    """OAuth connection model for third-party authentication."""
    
    __tablename__ = 'oauth_connections'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google', 'github'
    provider_user_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    profile_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
    )


class AuthAuditLog(db.Model):
    """Audit log for authentication events."""
    
    __tablename__ = 'auth_audit_logs'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'))
    event_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'register', 'password_reset', etc.
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=True)
    event_data = db.Column(db.JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Role(db.Model):
    """Role model for authorization."""
    
    __tablename__ = 'roles'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)  # 'user', 'admin', 'staff'
    description = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    user_roles = db.relationship('UserRole', foreign_keys='UserRole.role_id', backref='role', lazy=True, cascade='all, delete-orphan')


class Permission(db.Model):
    """Permission model for fine-grained access control."""
    
    __tablename__ = 'permissions'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)  # 'manage_users', 'view_admin', 'manage_content'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RolePermission(db.Model):
    """Many-to-many relationship between roles and permissions."""
    
    __tablename__ = 'role_permissions'
    
    role_id = db.Column(GUID(), db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = db.Column(GUID(), db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)


class UserRole(db.Model):
    """Many-to-many relationship between users and roles."""
    
    __tablename__ = 'user_roles'
    
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(GUID(), db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_by = db.Column(GUID(), db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    """Project model for saving user-generated content like lyrics and music."""
    
    __tablename__ = 'projects'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    project_type = db.Column(db.String(50), nullable=False, default='lyrics')  # 'lyrics', 'music', 'combined'
    
    # Content storage
    lyrics_data = db.Column(db.JSON)  # Structured lyric data
    music_data = db.Column(db.JSON)   # Music generation parameters or references
    combined_data = db.Column(db.JSON)  # Combined lyrics + music data
    
    # Metadata
    tags = db.Column(db.JSON)  # Array of tag strings
    is_public = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='projects')
    
    def __init__(self, user_id, title, project_type='lyrics', **kwargs):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.project_type = project_type
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert project object to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'project_type': self.project_type,
            'lyrics_data': self.lyrics_data,
            'music_data': self.music_data,
            'combined_data': self.combined_data,
            'tags': self.tags or [],
            'is_public': self.is_public,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_lyrics(self, lyrics_data):
        """Update lyrics data in the project."""
        self.lyrics_data = lyrics_data
        self.project_type = 'lyrics' if not self.music_data else 'combined'
        self.updated_at = datetime.utcnow()
    
    def update_music(self, music_data):
        """Update music data in the project."""
        self.music_data = music_data
        self.project_type = 'music' if not self.lyrics_data else 'combined'
        self.updated_at = datetime.utcnow()


class AudioLibrary(db.Model):
    """Audio Library model for storing user-added audio content."""
    
    __tablename__ = 'audio_library'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Audio metadata
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255))
    duration = db.Column(db.Integer)  # Duration in seconds
    file_size = db.Column(db.BigInteger)  # File size in bytes
    file_format = db.Column(db.String(10))  # mp3, wav, flac, etc.
    
    # File paths and URLs
    audio_url = db.Column(db.Text)  # Primary audio file URL
    original_filename = db.Column(db.String(255))  # Original uploaded filename
    
    # Additional metadata
    genre = db.Column(db.String(100))
    album = db.Column(db.String(255))
    year = db.Column(db.Integer)
    tags = db.Column(db.JSON)  # Array of tag strings
    lyrics = db.Column(db.Text)
    lyrics_source = db.Column(db.String(50))  # metadata, whisper, user
    lyrics_extraction_status = db.Column(db.String(50), default='not_requested')  # not_requested, queued, processing, completed, failed
    lyrics_extraction_error = db.Column(db.Text)
    
    # Playback and library info
    play_count = db.Column(db.Integer, default=0)
    last_played_at = db.Column(db.DateTime)
    is_favorite = db.Column(db.Boolean, default=False)
    
    # Processing status
    processing_status = db.Column(db.String(50), default='ready')  # ready, processing, error
    source_type = db.Column(db.String(50))  # upload, generated, url, history
    source_reference = db.Column(db.Text)  # Reference to original source (task_id, etc.)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audio_library')
    playlists = db.relationship('Playlist', secondary='playlist_audio_library', backref='audio_items')
    
    def __init__(self, user_id, title, **kwargs):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self, include_relationships=False):
        """Convert audio library object to dictionary for API responses."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'artist': self.artist,
            'duration': self.duration,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'audio_url': self.audio_url,
            'original_filename': self.original_filename,
            'genre': self.genre,
            'album': self.album,
            'year': self.year,
            'tags': self.tags or [],
            'lyrics': self.lyrics,
            'lyrics_source': self.lyrics_source,
            'lyrics_extraction_status': self.lyrics_extraction_status,
            'lyrics_extraction_error': self.lyrics_extraction_error,
            'play_count': self.play_count,
            'is_favorite': self.is_favorite,
            'processing_status': self.processing_status,
            'source_type': self.source_type,
            'source_reference': self.source_reference,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            data['playlists'] = [playlist.to_dict() for playlist in self.playlists]
        
        return data
    
    def increment_play_count(self):
        """Increment play count and update last played timestamp."""
        self.play_count += 1
        self.last_played_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_formatted_duration(self):
        """Get formatted duration string (MM:SS or HH:MM:SS)."""
        if not self.duration:
            return "Unknown"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_formatted_file_size(self):
        """Get formatted file size string."""
        if not self.file_size:
            return "Unknown"
        
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class Playlist(db.Model):
    """Playlist model for organizing audio library items."""
    
    __tablename__ = 'playlists'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Playlist metadata
    cover_image_url = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)

    # Smart Playlist / Generation Metadata
    is_generated = db.Column(db.Boolean, default=False)
    generation_type = db.Column(db.String(50))  # 'prompt', 'template', 'infinite', 'manual'
    generation_prompt = db.Column(db.Text)
    template_id = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='playlists')
    
    def __init__(self, user_id, name, **kwargs):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self, include_audio_items=False):
        """Convert playlist object to dictionary for API responses."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'cover_image_url': self.cover_image_url,
            'is_public': self.is_public,
            'is_generated': self.is_generated,
            'generation_type': self.generation_type,
            'generation_prompt': self.generation_prompt,
            'template_id': self.template_id,
            'audio_count': len(self.audio_items),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_audio_items:
            data['audio_items'] = [audio_item.to_dict() for audio_item in self.audio_items]
        
        return data


class PlaylistAudioLibrary(db.Model):
    """Many-to-many relationship between playlists and audio library items."""
    
    __tablename__ = 'playlist_audio_library'
    
    playlist_id = db.Column(GUID(), db.ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True)
    audio_library_id = db.Column(GUID(), db.ForeignKey('audio_library.id', ondelete='CASCADE'), primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    position = db.Column(db.Integer)


class PlaylistGenerationJob(db.Model):
    """Model to track status of AI playlist generation jobs."""
    
    __tablename__ = 'playlist_generation_jobs'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    playlist_id = db.Column(GUID(), db.ForeignKey('playlists.id', ondelete='CASCADE'))
    
    status = db.Column(db.String(50), default='pending')
    prompt = db.Column(db.Text)
    template_id = db.Column(db.String(100))

    current_track_index = db.Column(db.Integer, default=0)
    total_tracks = db.Column(db.Integer, default=0)

    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'playlist_id': self.playlist_id,
            'status': self.status,
            'prompt': self.prompt,
            'template_id': self.template_id,
            'current_track_index': self.current_track_index,
            'total_tracks': self.total_tracks,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class VoiceProfile(db.Model):
    __tablename__ = 'voice_profiles'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)
    active_model_version_id = db.Column(GUID(), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoiceDatasetFile(db.Model):
    __tablename__ = 'voice_dataset_files'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    voice_profile_id = db.Column(GUID(), db.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    r2_key = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    duration_sec = db.Column(db.Float)
    size_bytes = db.Column(db.BigInteger)
    sha256 = db.Column(db.String(64))
    mime = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    voice_profile = db.relationship('VoiceProfile', backref=db.backref('dataset_files', lazy=True, cascade='all, delete-orphan'))


class VoiceTrainingJob(db.Model):
    __tablename__ = 'voice_training_jobs'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    voice_profile_id = db.Column(GUID(), db.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), default='queued', nullable=False)
    modal_call_id = db.Column(db.String(200))
    params_json = db.Column(db.JSON)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)

    voice_profile = db.relationship('VoiceProfile', backref=db.backref('training_jobs', lazy=True, cascade='all, delete-orphan'))


class VoiceModelVersion(db.Model):
    __tablename__ = 'voice_model_versions'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    voice_profile_id = db.Column(GUID(), db.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    training_job_id = db.Column(GUID(), db.ForeignKey('voice_training_jobs.id', ondelete='SET NULL'), nullable=True, index=True)
    status = db.Column(db.String(20), default='ready', nullable=False)
    r2_model_key = db.Column(db.Text)
    r2_config_key = db.Column(db.Text)
    metrics_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    voice_profile = db.relationship('VoiceProfile', backref=db.backref('model_versions', lazy=True, cascade='all, delete-orphan'))


class VoiceConversionJob(db.Model):
    __tablename__ = 'voice_conversion_jobs'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    voice_profile_id = db.Column(GUID(), db.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    model_version_id = db.Column(GUID(), db.ForeignKey('voice_model_versions.id', ondelete='SET NULL'), nullable=True, index=True)
    status = db.Column(db.String(20), default='queued', nullable=False)
    modal_call_id = db.Column(db.String(200))
    input_r2_key = db.Column(db.Text)
    output_r2_key = db.Column(db.Text)
    input_duration_sec = db.Column(db.Float)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    voice_profile = db.relationship('VoiceProfile', backref=db.backref('conversion_jobs', lazy=True, cascade='all, delete-orphan'))


class WebhookEvent(db.Model):
    __tablename__ = 'webhook_events'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.String(200), nullable=False, index=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('source', 'event_id', name='uq_webhook_source_event_id'),
    )


class AdminSetting(db.Model):
    __tablename__ = 'admin_settings'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = db.Column(db.String(200), unique=True, nullable=False, index=True)
    value = db.Column(db.JSON)
    updated_by = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, key, value=None, updated_by=None):
        self.id = str(uuid.uuid4())
        self.key = key
        self.value = value
        self.updated_by = updated_by

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UsageEvent(db.Model):
    __tablename__ = 'usage_events'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'), index=True)
    ip_address = db.Column(db.String(45), index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    units = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __init__(self, event_type, user_id=None, ip_address=None, units=1):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.ip_address = ip_address
        self.event_type = event_type
        self.units = units


def get_default_role():
    """Get or create the default 'user' role."""
    role = Role.query.filter_by(name='user').first()
    if not role:
        role = Role(name='user', description='Regular user', is_default=True)
        db.session.add(role)
        db.session.commit()
    return role


def ensure_admin_basics():
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator', is_default=False)
        db.session.add(admin_role)

    staff_role = Role.query.filter_by(name='staff').first()
    if not staff_role:
        staff_role = Role(name='staff', description='Staff', is_default=False)
        db.session.add(staff_role)

    permission_specs = [
        ('view_admin', 'Access admin API'),
        ('manage_users', 'Manage users'),
        ('manage_roles', 'Manage roles and permissions'),
        ('view_audit_logs', 'View audit logs'),
        ('manage_settings', 'Manage system settings'),
    ]
    permissions_by_name = {}
    for name, description in permission_specs:
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            perm = Permission(name=name, description=description)
            db.session.add(perm)
        permissions_by_name[name] = perm

    db.session.flush()

    for perm in permissions_by_name.values():
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)

    staff_defaults = ['view_admin', 'view_audit_logs']
    for name in staff_defaults:
        perm = permissions_by_name.get(name)
        if perm and perm not in staff_role.permissions:
            staff_role.permissions.append(perm)

    db.session.commit()