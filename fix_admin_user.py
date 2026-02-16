
import os
import sys
from flask import Flask

def fix_admin():
    # Force local Docker DB URL BEFORE importing app
    os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/music_craft_db'
    print(f"Set DATABASE_URL to: {os.environ['DATABASE_URL']}")

    from app import create_app, db, bcrypt
    from app.models import User, Role, UserRole, ensure_admin_basics

    print("Initializing app context...")
    app = create_app()
    print(f"DEBUG: Using DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    with app.app_context():
        # Ensure roles exist
        print("Ensuring default roles exist...")
        ensure_admin_basics()
        db.session.commit()

        email = 'admin@joefoxing.com'
        password = 'secure_admin_password_123'  # Change this!
        
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"Creating user {email}...")
            user = User(email=email, display_name='Admin')
            user.set_password(password)
            user.email_verified = True
            db.session.add(user)
            print(f"User created.")
        else:
            print(f"User {email} already exists. Updating password and unlocking...")
            user.set_password(password)
            user.email_verified = True
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.add(user)
            print("Password updated and account unlocked.")
            
        db.session.commit()
        print(f"Current password hash: {user.password_hash[:20]}...")
            
        # Assign admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("Error: 'admin' role not found. Run migrations/app startup first.")
            return

        if not user.has_permission('view_admin'):
            print(f"Assigning 'admin' role to {email}...")
            user_role = UserRole(user_id=user.id, role_id=admin_role.id)
            db.session.add(user_role)
            db.session.commit()
            print("Role assigned.")
        else:
            print(f"User {email} already has admin permissions.")

if __name__ == "__main__":
    fix_admin()
