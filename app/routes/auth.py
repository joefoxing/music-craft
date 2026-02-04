"""
Authentication routes for the Music Cover Generator application.
Handles user registration, login, logout, email verification, and password reset.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import generate_csrf
import re
from datetime import datetime
from authlib.integrations.flask_client import OAuth

from app import db, bcrypt, mail, limiter
from app.models import User, AuthAuditLog, get_default_role, UserRole, OAuthConnection
from app.forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ProfileForm

auth_bp = Blueprint('auth', __name__)

# Initialize OAuth
oauth = OAuth()


@auth_bp.context_processor
def inject_now():
    """Inject current datetime into template context."""
    return {'now': datetime.utcnow()}


# Helper functions
def log_auth_event(user_id, event_type, ip_address, user_agent, success=True, event_data=None):
    """Log authentication event to audit log."""
    log = AuthAuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        event_data=event_data or {}
    )
    db.session.add(log)
    db.session.commit()


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


def init_oauth(app):
    """Initialize OAuth for the application."""
    oauth.init_app(app)
    
    # Register Google OAuth
    if app.config.get('GOOGLE_OAUTH_CLIENT_ID') and app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    
    # Register GitHub OAuth
    if app.config.get('GITHUB_OAUTH_CLIENT_ID') and app.config.get('GITHUB_OAUTH_CLIENT_SECRET'):
        oauth.register(
            name='github',
            client_id=app.config['GITHUB_OAUTH_CLIENT_ID'],
            client_secret=app.config['GITHUB_OAUTH_CLIENT_SECRET'],
            authorize_url='https://github.com/login/oauth/authorize',
            access_token_url='https://github.com/login/oauth/access_token',
            client_kwargs={'scope': 'user:email'},
        )


def get_or_create_user_from_oauth(provider, provider_user_id, email, name, profile_data):
    """Get or create a user from OAuth provider data."""
    # Check if OAuth connection already exists
    oauth_conn = OAuthConnection.query.filter_by(
        provider=provider,
        provider_user_id=provider_user_id
    ).first()
    
    if oauth_conn:
        # Existing OAuth connection, return the user
        user = User.query.get(oauth_conn.user_id)
        if user:
            return user
    
    # Check if user with this email already exists
    user = User.query.filter_by(email=email).first() if email else None
    
    if not user:
        # Create new user
        user = User(
            email=email or f"{provider_user_id}@{provider}.oauth",
            display_name=name or email.split('@')[0] if email else provider_user_id
        )
        user.email_verified = True  # OAuth emails are typically verified
        db.session.add(user)
        db.session.commit()
        
        # Assign default role
        default_role = get_default_role()
        user_role = UserRole(user_id=user.id, role_id=default_role.id)
        db.session.add(user_role)
    
    # Create or update OAuth connection
    oauth_conn = OAuthConnection(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        profile_data=profile_data
    )
    db.session.add(oauth_conn)
    db.session.commit()
    
    return user


@auth_bp.route('/oauth/login/<provider>')
def oauth_login(provider):
    """Initiate OAuth login flow."""
    if not current_app.config.get('OAUTH_ENABLED', False):
        flash('OAuth login is not enabled.', 'danger')
        return redirect(url_for('auth.login'))
    
    if provider not in ['google', 'github']:
        flash('Invalid OAuth provider.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Generate redirect URI
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    
    # Start OAuth flow
    try:
        if provider == 'google':
            return oauth.google.authorize_redirect(redirect_uri)
        elif provider == 'github':
            return oauth.github.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"OAuth login error for {provider}: {e}")
        flash('Failed to initiate OAuth login. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/oauth/callback/<provider>')
def oauth_callback(provider):
    """Handle OAuth callback."""
    if not current_app.config.get('OAUTH_ENABLED', False):
        flash('OAuth login is not enabled.', 'danger')
        return redirect(url_for('auth.login'))
    
    if provider not in ['google', 'github']:
        flash('Invalid OAuth provider.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        # Get OAuth token
        if provider == 'google':
            token = oauth.google.authorize_access_token()
            userinfo = token.get('userinfo')
            if not userinfo:
                # Fetch userinfo if not included
                userinfo = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
            
            provider_user_id = userinfo['sub']
            email = userinfo.get('email')
            name = userinfo.get('name')
            profile_data = userinfo
            
        elif provider == 'github':
            token = oauth.github.authorize_access_token()
            # Fetch user info from GitHub
            resp = oauth.github.get('https://api.github.com/user')
            userinfo = resp.json()
            
            provider_user_id = str(userinfo['id'])
            email = userinfo.get('email')
            name = userinfo.get('name') or userinfo.get('login')
            
            # If email is not public, fetch from GitHub emails endpoint
            if not email:
                resp = oauth.github.get('https://api.github.com/user/emails')
                emails = resp.json()
                primary_email = next((e for e in emails if e.get('primary')), None)
                email = primary_email.get('email') if primary_email else None
            
            profile_data = userinfo
        
        # Get or create user
        user = get_or_create_user_from_oauth(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            profile_data=profile_data
        )
        
        # Log OAuth login event
        log_auth_event(
            user_id=user.id,
            event_type=f'oauth_login_{provider}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True,
            event_data={'provider': provider, 'email': email}
        )
        
        # Login the user
        login_user(user, remember=True)
        flash(f'Successfully logged in with {provider.capitalize()}!', 'success')
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f"OAuth callback error for {provider}: {e}")
        flash(f'Failed to authenticate with {provider.capitalize()}. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    """User registration endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        display_name = form.display_name.data.strip()
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login or use a different email.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Validate email format
        if not validate_email(email):
            flash('Invalid email format.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(email=email, password=password, display_name=display_name)
        
        # Generate verification token
        verification_token = user.generate_verification_token()
        
        # Assign default role
        default_role = get_default_role()
        user_role = UserRole(user_id=user.id, role_id=default_role.id)
        
        db.session.add(user)
        db.session.add(user_role)
        db.session.commit()
        
        # Log registration event
        log_auth_event(
            user_id=user.id,
            event_type='register',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True,
            event_data={'email': email}
        )
        
        # Send verification email (in production)
        if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
            try:
                from flask_mail import Message
                msg = Message(
                    'Verify Your Email - Music Cover Generator',
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
                msg.body = f'''Welcome to Music Cover Generator!

Please verify your email by clicking the following link:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Music Cover Generator Team
'''
                mail.send(msg)
                flash('Registration successful! Please check your email to verify your account.', 'success')
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {e}")
                # In development, show the verification link in console
                if current_app.debug:
                    verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
                    print(f"\n{'='*60}")
                    print("EMAIL VERIFICATION LINK (development mode):")
                    print(f"URL: {verification_url}")
                    print(f"Token: {verification_token}")
                    print(f"{'='*60}\n")
                    flash('Registration successful! Email service is not configured. '
                          'Check console for verification link (development mode).', 'warning')
                else:
                    flash('Registration successful! We could not send a verification email. '
                          'Please contact support or try again later.', 'warning')
        else:
            # Email credentials not configured
            if current_app.debug:
                verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
                print(f"\n{'='*60}")
                print("EMAIL VERIFICATION LINK (development mode - email not configured):")
                print(f"URL: {verification_url}")
                print(f"Token: {verification_token}")
                print(f"{'='*60}\n")
                flash('Registration successful! Email service is not configured. '
                      'Check console for verification link (development mode).', 'warning')
            else:
                flash('Registration successful! Email service is not configured. '
                      'Please contact support.', 'warning')
        
        # Auto-login after registration
        login_user(user, remember=True)
        
        return redirect(url_for('main.index'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        remember = form.remember.data
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Log login attempt
        log_auth_event(
            user_id=user.id if user else None,
            event_type='login',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=False,  # Will update if successful
            event_data={'email': email}
        )
        
        # Check if user exists and account is not locked
        if not user or user.is_locked():
            error_msg = 'Invalid email or password, or account is locked.'
            user.record_login(success=False) if user else None
            db.session.commit()
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
            
            flash(error_msg, 'danger')
            return render_template('auth/login.html', form=form)
        
        # Check password
        if not user.check_password(password):
            error_msg = 'Invalid email or password.'
            user.record_login(success=False)
            db.session.commit()
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
            
            flash(error_msg, 'danger')
            return render_template('auth/login.html', form=form)
        
        # Login successful
        user.record_login(success=True)
        login_user(user, remember=remember)
        
        # Update audit log
        log = AuthAuditLog.query.filter_by(
            user_id=user.id,
            event_type='login',
            success=False
        ).order_by(AuthAuditLog.created_at.desc()).first()
        if log:
            log.success = True
            db.session.commit()
        
        flash('Login successful!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        
        # Handle AJAX requests differently
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'redirect': next_page
            })
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout endpoint."""
    # Log logout event
    log_auth_event(
        user_id=current_user.id,
        event_type='logout',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        success=True
    )
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification endpoint."""
    if current_user.is_authenticated:
        user = current_user
    else:
        # Find user by verification token
        user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.verify_email(token):
        db.session.commit()
        
        # Log verification event
        log_auth_event(
            user_id=user.id,
            event_type='email_verified',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True
        )
        
        flash('Email verified successfully!', 'success')
        
        if not current_user.is_authenticated:
            login_user(user, remember=True)
        
        return redirect(url_for('main.index'))
    else:
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    """Resend verification email endpoint."""
    if current_user.email_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('main.index'))
    
    # Generate new verification token
    verification_token = current_user.generate_verification_token()
    db.session.commit()
    
    # Send verification email
    if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
        try:
            from flask_mail import Message
            msg = Message(
                'Verify Your Email - Music Cover Generator',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[current_user.email]
            )
            verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
            msg.body = f'''Please verify your email by clicking the following link:
{verification_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The Music Cover Generator Team
'''
            mail.send(msg)
            flash('Verification email sent! Please check your inbox.', 'success')
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")
            flash('Failed to send verification email. Please try again later.', 'danger')
    else:
        flash('Email service not configured. Please contact support.', 'warning')
    
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("2 per hour")
def forgot_password():
    """Forgot password endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = user.generate_reset_token()
            db.session.commit()
            
            # Log password reset request
            log_auth_event(
                user_id=user.id,
                event_type='password_reset_request',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                success=True,
                event_data={'email': email}
            )
            
            # Send reset email
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                try:
                    from flask_mail import Message
                    msg = Message(
                        'Reset Your Password - Music Cover Generator',
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[email]
                    )
                    reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
                    msg.body = f'''You requested to reset your password.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Best regards,
The Music Cover Generator Team
'''
                    mail.send(msg)
                    flash('Password reset instructions sent to your email.', 'success')
                except Exception as e:
                    current_app.logger.error(f"Failed to send reset email: {e}")
                    flash('Failed to send reset email. Please try again later.', 'danger')
            else:
                flash('Email service not configured. Please contact support.', 'warning')
        else:
            # Don't reveal if user exists for security
            flash('If an account exists with that email, reset instructions have been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("2 per hour")
def reset_password(token):
    """Reset password endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        new_password = form.password.data
        
        # Validate password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/reset_password.html', form=form, token=token)
        
        # Reset password
        if user.reset_password(token, new_password):
            db.session.commit()
            
            # Log password reset
            log_auth_event(
                user_id=user.id,
                event_type='password_reset',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                success=True
            )
            
            flash('Password reset successful! Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired reset token.', 'danger')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management endpoint."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update display name
        if form.display_name.data != current_user.display_name:
            current_user.display_name = form.display_name.data.strip()
        
        # Update email (requires verification)
        if form.email.data.lower().strip() != current_user.email:
            new_email = form.email.data.lower().strip()
            
            # Check if email is already taken
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already registered by another user.', 'danger')
                return render_template('auth/profile.html', form=form)
            
            # Update email and require verification
            current_user.email = new_email
            current_user.email_verified = False
            verification_token = current_user.generate_verification_token()
            
            # Send verification email for new email
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                try:
                    from flask_mail import Message
                    msg = Message(
                        'Verify Your New Email - Music Cover Generator',
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[new_email]
                    )
                    verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
                    msg.body = f'''You have changed your email address.

Please verify your new email by clicking the following link:
{verification_url}

This link will expire in 24 hours.

Best regards,
The Music Cover Generator Team
'''
                    mail.send(msg)
                    flash('Email updated! Please verify your new email address.', 'success')
                except Exception as e:
                    current_app.logger.error(f"Failed to send verification email: {e}")
                    flash('Email updated but failed to send verification email. Please contact support.', 'warning')
            else:
                flash('Email updated! Please verify your new email address.', 'success')
        
        # Update password if provided
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                is_valid, message = validate_password(form.new_password.data)
                if not is_valid:
                    flash(message, 'danger')
                    return render_template('auth/profile.html', form=form)
                
                current_user.set_password(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html', form=form)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)


@auth_bp.route('/csrf-token')
def get_csrf_token():
    """Get CSRF token for API requests."""
    return jsonify({'csrf_token': generate_csrf()})


# API endpoints for frontend
@auth_bp.route('/api/check-auth')
def check_auth():
    """Check if user is authenticated (API endpoint)."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    return jsonify({'authenticated': False})


@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout API endpoint."""
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})