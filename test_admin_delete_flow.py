
import unittest
import requests
import uuid
from app import create_app, db
from app.models import User, Role, UserRole, Permission

class TestAdminDelete(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False  # Disable CSRF for testing convenience
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create Permissions
        manage_users_perm = Permission(name='manage_users', description='Manage Users')
        db.session.add(manage_users_perm)
        
        # Create Roles
        self.admin_role = Role(name='admin', description='Admin')
        self.admin_role.permissions.append(manage_users_perm)
        db.session.add(self.admin_role)
        
        # Create Admin User
        self.admin_user = User(email='admin@test.com', password='password')
        db.session.add(self.admin_user)
        db.session.commit()
        
        # Assign Admin Role
        db.session.add(UserRole(user_id=self.admin_user.id, role_id=self.admin_role.id))
        
        # Create Target User
        self.target_user = User(email='target@test.com', password='password')
        db.session.add(self.target_user)
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', json={
            'email': email,
            'password': password
        })

    def test_delete_user_flow(self):
        # Login as admin
        with self.client:
            self.client.post('/auth/login', data={
                'email': 'admin@test.com',
                'password': 'password'
            })
            
            # 1. Try to delete self (should fail)
            resp = self.client.delete(f'/api/admin/users/{self.admin_user.id}')
            self.assertEqual(resp.status_code, 403)
            
            # 2. Delete target user
            resp = self.client.delete(f'/api/admin/users/{self.target_user.id}')
            self.assertEqual(resp.status_code, 200)
            
            # Verify soft delete
            user = User.query.get(self.target_user.id)
            self.assertTrue(user.is_deleted)
            self.assertIsNotNone(user.deleted_at)
            
            # 3. Delete again (idempotency)
            resp = self.client.delete(f'/api/admin/users/{self.target_user.id}')
            self.assertEqual(resp.status_code, 204)

if __name__ == '__main__':
    unittest.main()
