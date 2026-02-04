"""
Forms for the Music Cover Generator application.
Uses Flask-WTF for form handling and validation.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    """User registration form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address'),
        Length(max=255, message='Email must be less than 255 characters')
    ])
    
    display_name = StringField('Display Name', validators=[
        DataRequired(message='Display name is required'),
        Length(min=2, max=100, message='Display name must be between 2 and 100 characters')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Validate that email is not already registered."""
        user = User.query.filter_by(email=email.data.lower().strip()).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    
    remember = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    
    submit = SubmitField('Send Reset Instructions')


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Reset Password')


class ProfileForm(FlaskForm):
    """User profile form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address'),
        Length(max=255, message='Email must be less than 255 characters')
    ])
    
    display_name = StringField('Display Name', validators=[
        DataRequired(message='Display name is required'),
        Length(min=2, max=100, message='Display name must be between 2 and 100 characters')
    ])
    
    current_password = PasswordField('Current Password (leave blank to keep unchanged)')
    
    new_password = PasswordField('New Password (leave blank to keep unchanged)', validators=[
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Update Profile')
    
    def validate(self, extra_validators=None):
        """Custom validation for profile form."""
        # Run default validators first
        if not super().validate(extra_validators):
            return False
        
        # Validate that if new_password is provided, current_password must also be provided
        if self.new_password.data and not self.current_password.data:
            self.current_password.errors.append('Current password is required to set a new password')
            return False
        
        # Validate that if current_password is provided, new_password must also be provided
        if self.current_password.data and not self.new_password.data:
            self.new_password.errors.append('New password is required when providing current password')
            return False
        
        return True


class ChangePasswordForm(FlaskForm):
    """Change password form (standalone)."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Change Password')