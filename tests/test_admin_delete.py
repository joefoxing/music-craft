import sys
import os
import unittest
from datetime import datetime

# Add root to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Role, UserRole, Permission, AuthAuditLog

class TestAdminDelete(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False, 'AUTO_CREATE_DB': False})
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Create Roles & Permissions
        admin_role = Role(name='admin', description='Admin')
        view_admin = Permission(name='view_admin', description='View Admin')
        manage_users = Permission(name='manage_users', description='Manage Users')
        
        db.session.add(admin_role)
        db.session.add(view_admin)
        db.session.add(manage_users)
        db.session.commit()
        
        admin_role.permissions.append(view_admin)
        admin_role.permissions.append(manage_users)
        db.session.commit()

        # Create Admin
        self.admin = User(email='admin@test.com', password='password')
        db.session.add(self.admin)
        db.session.commit()
        
        # Assign Admin Role
        ur = UserRole(user_id=self.admin.id, role_id=admin_role.id)
        db.session.add(ur)
        db.session.commit()

        # Create Target User
        self.target = User(email='target@test.com', password='password')
        db.session.add(self.target)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_delete_user(self):
        # Simulate Admin Login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = self.admin.id
            sess['_fresh'] = True

        # Check pre-state
        target = User.query.get(self.target.id)
        self.assertFalse(target.is_deleted)

        # Call DELETE
        resp = self.client.delete(f'/api/admin/users/{self.target.id}')
        self.assertEqual(resp.status_code, 200)
        
        # Check post-state
        target = User.query.get(self.target.id)
        self.assertTrue(target.is_deleted)
        self.assertIsNotNone(target.deleted_at)

        # Check Audit Log
        log = AuthAuditLog.query.filter_by(event_type='admin_user_delete').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_data['target_user_id'], self.target.id)

    def test_self_delete_prevention(self):
        # Simulate Admin Login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = self.admin.id
            sess['_fresh'] = True

        resp = self.client.delete(f'/api/admin/users/{self.admin.id}')
        self.assertEqual(resp.status_code, 403)
        
        admin = User.query.get(self.admin.id)
        self.assertFalse(admin.is_deleted)

    def test_delete_already_deleted(self):
        # Simulate Admin Login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = self.admin.id
            sess['_fresh'] = True

        # Manually delete first
        self.target.is_deleted = True
        db.session.commit()

        # Call DELETE again
        resp = self.client.delete(f'/api/admin/users/{self.target.id}')
        self.assertEqual(resp.status_code, 204)

if __name__ == '__main__':
    unittest.main()
