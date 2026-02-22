"""
Configuration module for the Music Cover Generator application.
Centralizes all configuration settings and environment variable handling.
"""
import os
from typing import Dict, Any


def normalize_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    if url.startswith('postgresql://') and 'postgresql+' not in url:
        try:
            import psycopg2  # noqa: F401
        except Exception:
            try:
                import psycopg  # noqa: F401
            except Exception:
                return url
            return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


class Config:
    """Application configuration."""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    PREFERRED_URL_SCHEME = 'https'
    TEMPLATES_AUTO_RELOAD = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.environ.get('DATABASE_URL', 'sqlite:///app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    AUTO_CREATE_DB = os.environ.get('AUTO_CREATE_DB')
    if AUTO_CREATE_DB is None:
        AUTO_CREATE_DB = SQLALCHEMY_DATABASE_URI.startswith('sqlite') and os.environ.get('FLASK_ENV', '').lower() != 'production'
    else:
        AUTO_CREATE_DB = AUTO_CREATE_DB.lower() == 'true'
    
    # File upload configuration
    UPLOAD_FOLDER = None  # Will be set in configure_app()
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB default
    MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB default

    # Kie API configuration
    KIE_API_KEY = os.environ.get('KIE_API_KEY', '')
    KIE_API_BASE_URL = 'https://api.kie.ai'
    USE_MOCK = os.environ.get('USE_MOCK', 'false').lower() == 'true'
    
    # History configuration
    HISTORY_MAX_ENTRIES = 100
    HISTORY_CLEANUP_DAYS = 15
    
    # Audio file configuration
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}

    # Lyrics extraction configuration
    LYRICS_EXTRACTION_ENABLED = os.environ.get('LYRICS_EXTRACTION_ENABLED', 'true').lower() == 'true'
    LYRICS_WHISPER_LANGUAGE = os.environ.get('LYRICS_WHISPER_LANGUAGE')
    LYRICS_ENFORCE_ORIGINAL_LANGUAGE = os.environ.get('LYRICS_ENFORCE_ORIGINAL_LANGUAGE', 'true').lower() == 'true'
    LYRICS_VI_CUSTOM_CORRECTIONS_JSON = os.environ.get('LYRICS_VI_CUSTOM_CORRECTIONS_JSON', '')
    LYRICS_MIN_UNIQUE_WORD_RATIO = float(os.environ.get('LYRICS_MIN_UNIQUE_WORD_RATIO', '0.22'))
    LYRICS_MAX_REPEATED_NGRAM_RATIO = float(os.environ.get('LYRICS_MAX_REPEATED_NGRAM_RATIO', '0.08'))
    LYRICS_MAX_SAME_CHUNK_REPEATS = int(os.environ.get('LYRICS_MAX_SAME_CHUNK_REPEATS', '2'))
    LYRICS_VOCAL_SEPARATION_ENABLED = os.environ.get('LYRICS_VOCAL_SEPARATION_ENABLED', 'false').lower() == 'true'
    LYRICS_MAX_DOWNLOAD_MB = int(os.environ.get('LYRICS_MAX_DOWNLOAD_MB', '30'))
    LYRICS_EXTRACTION_ASYNC_ENABLED = os.environ.get('LYRICS_EXTRACTION_ASYNC_ENABLED', 'true').lower() == 'true'
    LYRICS_EXTRACTION_WORKERS = int(os.environ.get('LYRICS_EXTRACTION_WORKERS', '2'))
    
    # AssemblyAI (Tier 3)
    ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY', '')
    LYRICS_USE_ASSEMBLYAI = os.environ.get('LYRICS_USE_ASSEMBLYAI', 'true').lower() == 'true'
    
    # LRCLIB API (Tier 2 - free, no API key required)
    LYRICS_USE_LRCLIB = os.environ.get('LYRICS_USE_LRCLIB', 'true').lower() == 'true'
    
    # Musixmatch API (legacy, deprecated - replaced by LRCLIB)
    MUSIXMATCH_API_KEY = os.environ.get('MUSIXMATCH_API_KEY', '')
    LYRICS_USE_MUSIXMATCH = os.environ.get('LYRICS_USE_MUSIXMATCH', 'false').lower() == 'true'
    
    # Authentication configuration
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'password-salt')
    BCRYPT_LOG_ROUNDS = 12
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')
    
    # OAuth configuration
    OAUTH_ENABLED = os.environ.get('OAUTH_ENABLED', 'false').lower() == 'true'
    
    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
    
    # GitHub OAuth
    GITHUB_OAUTH_CLIENT_ID = os.environ.get('GITHUB_OAUTH_CLIENT_ID', '')
    GITHUB_OAUTH_CLIENT_SECRET = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET', '')
    
    # Stripe / Billing configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PRO_MONTHLY_PRICE_ID = os.environ.get('STRIPE_PRO_MONTHLY_PRICE_ID', '')
    STRIPE_PRO_ANNUAL_PRICE_ID = os.environ.get('STRIPE_PRO_ANNUAL_PRICE_ID', '')
    STRIPE_TOKEN_PACK_PRICE_ID = os.environ.get('STRIPE_TOKEN_PACK_PRICE_ID', '')

    # Security configuration
    LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '5 per minute')
    REGISTER_RATE_LIMIT = os.environ.get('REGISTER_RATE_LIMIT', '50 per hour')
    PASSWORD_RESET_RATE_LIMIT = os.environ.get('PASSWORD_RESET_RATE_LIMIT', '10 per hour')
    
    FREE_DAILY_LIMIT_USER = int(os.environ.get('FREE_DAILY_LIMIT_USER', '20'))
    FREE_MONTHLY_LIMIT_USER = int(os.environ.get('FREE_MONTHLY_LIMIT_USER', '200'))
    FREE_DAILY_LIMIT_ANON = int(os.environ.get('FREE_DAILY_LIMIT_ANON', '5'))
    FREE_MONTHLY_LIMIT_ANON = int(os.environ.get('FREE_MONTHLY_LIMIT_ANON', '50'))
    
    # Session configuration
    REMEMBER_COOKIE_DURATION = 86400  # 1 day in seconds
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day
    # For OAuth to work properly, we need proper cookie settings
    # Note: SESSION_COOKIE_SECURE controls HTTPS requirement
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    # Use 'Lax' for better compatibility with OAuth flows from third-party (Google)
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() == 'true'  # Make configurable
    
    @classmethod
    def configure_app(cls, app) -> None:
        """
        Configure Flask application with settings.
        
        Args:
            app: Flask application instance
        """
        # Set upload folder relative to app root
        cls.UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
        app.config['UPLOAD_FOLDER'] = cls.UPLOAD_FOLDER
        
        # Set database configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = cls.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = cls.SQLALCHEMY_TRACK_MODIFICATIONS
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = cls.SQLALCHEMY_ENGINE_OPTIONS
        app.config['AUTO_CREATE_DB'] = cls.AUTO_CREATE_DB
        
        # Set other configuration values
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = cls._get_max_content_length()
        app.config['MAX_UPLOAD_SIZE'] = cls._get_max_upload_size()
        app.config['KIE_API_KEY'] = cls.KIE_API_KEY
        app.config['KIE_API_BASE_URL'] = cls.KIE_API_BASE_URL
        app.config['USE_MOCK'] = cls.USE_MOCK
        app.config['PREFERRED_URL_SCHEME'] = cls.PREFERRED_URL_SCHEME
        app.config['LYRICS_EXTRACTION_ENABLED'] = cls.LYRICS_EXTRACTION_ENABLED
        app.config['LYRICS_WHISPER_LANGUAGE'] = cls.LYRICS_WHISPER_LANGUAGE
        app.config['LYRICS_ENFORCE_ORIGINAL_LANGUAGE'] = cls.LYRICS_ENFORCE_ORIGINAL_LANGUAGE
        app.config['LYRICS_VI_CUSTOM_CORRECTIONS_JSON'] = cls.LYRICS_VI_CUSTOM_CORRECTIONS_JSON
        app.config['LYRICS_MIN_UNIQUE_WORD_RATIO'] = cls.LYRICS_MIN_UNIQUE_WORD_RATIO
        app.config['LYRICS_MAX_REPEATED_NGRAM_RATIO'] = cls.LYRICS_MAX_REPEATED_NGRAM_RATIO
        app.config['LYRICS_MAX_SAME_CHUNK_REPEATS'] = cls.LYRICS_MAX_SAME_CHUNK_REPEATS
        app.config['LYRICS_VOCAL_SEPARATION_ENABLED'] = cls.LYRICS_VOCAL_SEPARATION_ENABLED
        app.config['LYRICS_MAX_DOWNLOAD_MB'] = cls.LYRICS_MAX_DOWNLOAD_MB
        app.config['LYRICS_EXTRACTION_ASYNC_ENABLED'] = cls.LYRICS_EXTRACTION_ASYNC_ENABLED
        app.config['LYRICS_EXTRACTION_WORKERS'] = cls.LYRICS_EXTRACTION_WORKERS
        
        # AssemblyAI configuration
        app.config['ASSEMBLYAI_API_KEY'] = cls.ASSEMBLYAI_API_KEY
        app.config['LYRICS_USE_ASSEMBLYAI'] = cls.LYRICS_USE_ASSEMBLYAI
        
        # LRCLIB configuration
        app.config['LYRICS_USE_LRCLIB'] = cls.LYRICS_USE_LRCLIB
        
        # Musixmatch configuration (legacy)
        app.config['MUSIXMATCH_API_KEY'] = cls.MUSIXMATCH_API_KEY
        app.config['LYRICS_USE_MUSIXMATCH'] = cls.LYRICS_USE_MUSIXMATCH
        
        # Authentication configuration
        app.config['SECURITY_PASSWORD_SALT'] = cls.SECURITY_PASSWORD_SALT
        app.config['BCRYPT_LOG_ROUNDS'] = cls.BCRYPT_LOG_ROUNDS
        
        # Email configuration
        app.config['MAIL_SERVER'] = cls.MAIL_SERVER
        app.config['MAIL_PORT'] = cls.MAIL_PORT
        app.config['MAIL_USE_TLS'] = cls.MAIL_USE_TLS
        app.config['MAIL_USERNAME'] = cls.MAIL_USERNAME
        app.config['MAIL_PASSWORD'] = cls.MAIL_PASSWORD
        app.config['MAIL_DEFAULT_SENDER'] = cls.MAIL_DEFAULT_SENDER
        
        # OAuth configuration
        app.config['OAUTH_ENABLED'] = cls.OAUTH_ENABLED
        app.config['GOOGLE_OAUTH_CLIENT_ID'] = cls.GOOGLE_OAUTH_CLIENT_ID
        app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = cls.GOOGLE_OAUTH_CLIENT_SECRET
        app.config['GITHUB_OAUTH_CLIENT_ID'] = cls.GITHUB_OAUTH_CLIENT_ID
        app.config['GITHUB_OAUTH_CLIENT_SECRET'] = cls.GITHUB_OAUTH_CLIENT_SECRET
        
        app.config['FREE_DAILY_LIMIT_USER'] = cls.FREE_DAILY_LIMIT_USER
        app.config['FREE_MONTHLY_LIMIT_USER'] = cls.FREE_MONTHLY_LIMIT_USER
        app.config['FREE_DAILY_LIMIT_ANON'] = cls.FREE_DAILY_LIMIT_ANON
        app.config['FREE_MONTHLY_LIMIT_ANON'] = cls.FREE_MONTHLY_LIMIT_ANON
        
        # Session configuration
        app.config['REMEMBER_COOKIE_DURATION'] = cls.REMEMBER_COOKIE_DURATION
        app.config['SESSION_COOKIE_SECURE'] = cls.SESSION_COOKIE_SECURE
        app.config['SESSION_COOKIE_HTTPONLY'] = cls.SESSION_COOKIE_HTTPONLY
        app.config['SESSION_COOKIE_SAMESITE'] = cls.SESSION_COOKIE_SAMESITE
        app.config['WTF_CSRF_ENABLED'] = cls.WTF_CSRF_ENABLED

        # Stripe / Billing configuration
        app.config['STRIPE_SECRET_KEY'] = cls.STRIPE_SECRET_KEY
        app.config['STRIPE_PUBLISHABLE_KEY'] = cls.STRIPE_PUBLISHABLE_KEY
        app.config['STRIPE_WEBHOOK_SECRET'] = cls.STRIPE_WEBHOOK_SECRET
        app.config['STRIPE_PRO_MONTHLY_PRICE_ID'] = cls.STRIPE_PRO_MONTHLY_PRICE_ID
        app.config['STRIPE_PRO_ANNUAL_PRICE_ID'] = cls.STRIPE_PRO_ANNUAL_PRICE_ID
        app.config['STRIPE_TOKEN_PACK_PRICE_ID'] = cls.STRIPE_TOKEN_PACK_PRICE_ID

        # Ensure upload folder exists
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
    
    @classmethod
    def _get_max_content_length(cls) -> int:
        """Get maximum content length from environment or default."""
        max_content_length = os.environ.get('MAX_CONTENT_LENGTH')
        if max_content_length:
            return int(max_content_length)
        return cls.MAX_CONTENT_LENGTH
    
    @classmethod
    def _get_max_upload_size(cls) -> int:
        """Get maximum upload size from environment or default."""
        max_upload_size = os.environ.get('MAX_UPLOAD_SIZE')
        if max_upload_size:
            return int(max_upload_size)
        return cls.MAX_UPLOAD_SIZE

    @classmethod
    def get_allowed_extensions(cls) -> set:
        """Get allowed audio file extensions."""
        return cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def is_extension_allowed(cls, filename: str) -> bool:
        """
        Check if a file extension is allowed.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if extension is allowed, False otherwise
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_model_limits(cls, model: str) -> Dict[str, int]:
        """
        Get character limits for a specific model.
        
        Args:
            model: Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            
        Returns:
            Dictionary with prompt, style, and title limits
        """
        model_limits = {
            "V5": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5PLUS": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5": {"prompt": 5000, "style": 1000, "title": 100},
            "V4_5ALL": {"prompt": 5000, "style": 1000, "title": 80},
            "V4": {"prompt": 3000, "style": 200, "title": 80}
        }
        return model_limits.get(model, model_limits["V5"])
    
    @classmethod
    def get_public_base_url(cls, request=None) -> str:
        """
        Get public base URL.
        
        Args:
            request: Flask request object (optional)
            
        Returns:
            Public base URL string
        """
        # Try to get current app context to check for BASE_URL
        try:
            from flask import current_app
            if current_app:
                if current_app.config.get('BASE_URL'):
                    return current_app.config['BASE_URL'].rstrip('/')
        except RuntimeError:
            # Outside of app context
            pass
        
        # Fall back to request host URL if available
        if request:
            return request.host_url.rstrip('/')

        # Default fallback
        return "http://localhost:5000"


def configure_proxy(app) -> None:
    """
    Configure proxy settings for the Flask application.
    
    Args:
        app: Flask application instance
    """
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    # When behind a proxy, use ProxyFix to handle headers
    # This ensures url_for(_external=True) generates correct URLs
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,  # Number of proxies trusted for X-Forwarded-For
        x_proto=1,  # Number of proxies trusted for X-Forwarded-Proto
        x_host=1,  # Number of proxies trusted for X-Forwarded-Host
        x_prefix=1  # Number of proxies trusted for X-Forwarded-Prefix
    )