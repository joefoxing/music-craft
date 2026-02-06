from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
import os
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    
    # Load configuration first to get CORS settings
    Config.configure_app(app)
    
    if test_config:
        app.config.update(test_config)
    
    # Configure CORS with environment-based allowed origins
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    # Filter out empty strings and strip whitespace
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    
    # If no origins specified, use localhost for development
    if not allowed_origins:
        allowed_origins = ['http://localhost:5000', 'http://127.0.0.1:5000']
    
    CORS(app, 
         supports_credentials=True,
         origins=allowed_origins,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # When behind a proxy (like Cloudflare tunnel), use ProxyFix to handle headers
    # This ensures url_for(_external=True) generates correct URLs
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,  # Number of proxies trusted for X-Forwarded-For
        x_proto=1,  # Number of proxies trusted for X-Forwarded-Proto
        x_host=1,  # Number of proxies trusted for X-Forwarded-Host
        x_prefix=1  # Number of proxies trusted for X-Forwarded-Prefix
    )
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import request, jsonify
        # Return proper error for CSRF failures
        # API routes are already exempted via csrf.exempt() calls below
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'CSRF token missing or incorrect', 'reason': str(e)}), 403
        # For form requests, return the error
        return jsonify({'error': 'CSRF token missing or incorrect', 'reason': str(e)}), 403
    
    # Health check endpoint for Docker/container orchestration
    @app.route('/health')
    def health_check():
        from flask import jsonify
        from datetime import datetime
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Please re-authenticate to access this page.'
    login_manager.needs_refresh_message_category = 'info'
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(user_id)

    # Unauthorized handler for API requests
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        # For AJAX/JSON requests, return JSON error instead of redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.path.startswith('/upload') or \
           request.path.startswith('/api/') or \
           (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
            return jsonify({'error': 'Authentication required'}), 401
        # Default behavior: redirect to login page
        return redirect(url_for(login_manager.login_view))
    
    # Create database tables
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from app.models import User, OAuthConnection, AuthAuditLog, Role, Permission, RolePermission, UserRole
        from app.models import AdminSetting, UsageEvent
        from app.models import Project, AudioLibrary, Playlist, PlaylistAudioLibrary
        
        if app.config.get('AUTO_CREATE_DB', False):
            db.create_all()
            
            # Create default roles if they don't exist
            from app.models import get_default_role, ensure_admin_basics
            get_default_role()
            ensure_admin_basics()
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.callback import callback_bp
    from app.routes.history_routes import history_api_bp
    from app.routes.audio_library_api import audio_library_bp
    from app.routes.playlist_api import playlist_api_bp
    from app.routes.api_auth import api_auth_bp
    from app.routes.api_admin import api_admin_bp
    from app.routes.vc_api import vc_bp
    
    # Import and register auth blueprint
    # (Forces reload)
    from app.routes.auth import auth_bp

    # Exempt API blueprints from CSRF protection
    csrf.exempt(api_bp)
    csrf.exempt(callback_bp)
    csrf.exempt(history_api_bp)
    csrf.exempt(audio_library_bp)
    csrf.exempt(playlist_api_bp)
    # api_auth_bp is NOT exempted to protect login/register/profile endpoints
    csrf.exempt(api_admin_bp)
    csrf.exempt(vc_bp)
    csrf.exempt(auth_bp)  # Exempt auth for tunnel compatibility

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(callback_bp)
    app.register_blueprint(history_api_bp)
    app.register_blueprint(audio_library_bp)
    app.register_blueprint(playlist_api_bp)
    app.register_blueprint(vc_bp)
    app.register_blueprint(api_auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_admin_bp, url_prefix='/api/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Initialize OAuth
    from app.routes.auth import init_oauth
    init_oauth(app)
    
    # Configure structured logging
    from app.core.logging import configure_logging
    configure_logging(app)
    
    return app