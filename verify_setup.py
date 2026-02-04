import os
import sys

print("Verifying setup...")

try:
    from app import create_app, db
    print("Successfully imported app modules.")
except ImportError as e:
    print(f"Failed to import app modules: {e}")
    sys.exit(1)

try:
    app = create_app()
    print("Successfully created app instance.")
except Exception as e:
    print(f"Failed to create app instance: {e}")
    sys.exit(1)

with app.app_context():
    try:
        # Verify DB connection/creation
        db.create_all()
        print("Successfully initialized database.")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)

print("Setup verification complete. You can now run 'python run.py'.")
