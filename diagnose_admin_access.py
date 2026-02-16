
import os
import sys
from flask import Flask
from app import create_app, db
from app.models import User, Role, Permission, UserRole

def diagnose():
    print("Initializing app context...")
    app = create_app()
    with app.app_context():
        print("\n--- Roles & Permissions ---")
        roles = Role.query.all()
        for role in roles:
            perms = [p.name for p in role.permissions]
            print(f"Role: {role.name}")
            print(f"  Permissions: {', '.join(perms)}")
        
        print("\n--- Users with 'admin' Role ---")
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("CRITICAL: 'admin' role does not exist!")
        else:
            # Join UserRole to find users
            admin_users = User.query.join(UserRole, User.id == UserRole.user_id).filter(UserRole.role_id == admin_role.id).all()
            if not admin_users:
                print("No users have the 'admin' role.")
            else:
                for u in admin_users:
                    print(f"User: {u.email} (ID: {u.id})")
        
        print("\n--- Users with 'view_admin' Permission (Direct or via Role) ---")
        # this is harder to query directly in SQL efficiently without complex joins, 
        # but we can check the 'admin' role users again or just check specific target users.
        
        target_email = 'admin@joefoxing.com'
        print(f"\n--- Checking target: {target_email} ---")
        user = User.query.filter_by(email=target_email).first()
        if user:
            print(f"User found: {user.id}")
            print(f"Roles: {user.get_role_names()}")
            print(f"Has 'view_admin': {user.has_permission('view_admin')}")
        else:
            print("User not found.")

if __name__ == "__main__":
    diagnose()
