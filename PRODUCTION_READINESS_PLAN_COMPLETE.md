# Music Cover Generator - Production Readiness Plan

## Current State Analysis

**Application Type**: Flask-based web application for AI music cover generation
**Current Features**:
- Audio file upload (MP3, WAV, OGG, M4A, FLAC)
- Kie API integration for music generation
- Dual generation modes (Simple/Custom)
- Multiple AI model support (V5, V4_5PLUS, V4_5, V4_5ALL, V4)
- Real-time status tracking and callbacks
- Ngrok integration for public tunnels
- Basic history/callback tracking

**Missing Production Features**:
- User authentication & authorization
- Billing/subscription management
- Admin dashboard
- Production security hardening
- Database persistence
- Monitoring & alerting
- CI/CD pipeline

---

## Milestone 1: Complete User Authentication & Registration

### User Stories & Acceptance Criteria

**US1: Email/Password Registration**
- As a new user, I want to register with email/password
- **AC1**: Registration form with email, password, confirm password
- **AC2**: Email validation (format, uniqueness)
- **AC3**: Password strength requirements (8+ chars, mixed case, numbers)
- **AC4**: Success confirmation and auto-login

**US2: Email Verification**
- As a registered user, I want to verify my email
- **AC1**: Verification email sent upon registration
- **AC2**: Verification link expires in 24h
- **AC3**: Verified status visible in profile
- **AC4**: Resend verification email option

**US3: Login/Logout**
- As a user, I want to login/logout securely
- **AC1**: Login form with email/password
- **AC2**: Remember me functionality
- **AC3**: Secure session management
- **AC4**: Logout clears all session data

**US4: Password Reset**
- As a user, I want to reset my password
- **AC1**: "Forgot password" flow
- **AC2**: Reset email with secure token
- **AC3**: Token expiration (1h)
- **AC4**: Password change confirmation

**US5: OAuth Integration (Optional)**
- As a user, I want to login with Google/GitHub
- **AC1**: OAuth buttons on login/register
- **AC2**: Account linking for existing users
- **AC3**: Profile data sync from OAuth provider

**US6: Profile Management**
- As a user, I want to manage my profile
- **AC1**: Profile page with editable info
- **AC2**: Avatar upload
- **AC3**: Email change with re-verification
- **AC4**: Password change with current password verification

### Database Schema Changes

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    display_name VARCHAR(100),
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    verification_token_expires_at TIMESTAMP,
    reset_token VARCHAR(100),
    reset_token_expires_at TIMESTAMP,
    last_login_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OAuth connections
CREATE TABLE oauth_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google', 'github'
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    profile_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

-- Audit logs for auth events
CREATE TABLE auth_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'register', 'password_reset', etc.
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_verification_token ON users(verification_token);
CREATE INDEX idx_users_reset_token ON users(reset_token);
CREATE INDEX idx_auth_audit_logs_user_id ON auth_audit_logs(user_id);
CREATE INDEX idx_auth_audit_logs_created_at ON auth_audit_logs(created_at);
```

### API Routes & UI Pages

**API Routes**:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify-email/:token` - Email verification
- `POST /api/auth/resend-verification` - Resend verification email
- `POST /api/auth/forgot-password` - Initiate password reset
- `POST /api/auth/reset-password/:token` - Complete password reset
- `POST /api/auth/change-password` - Change password (authenticated)
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `GET /api/auth/sessions` - List active sessions
- `DELETE /api/auth/sessions/:session_id` - Revoke session

**OAuth Routes**:
- `GET /api/auth/oauth/:provider` - Initiate OAuth flow
- `GET /api/auth/oauth/:provider/callback` - OAuth callback

**UI Pages**:
- `/register` - Registration page
- `/login` - Login page
- `/verify-email` - Email verification status
- `/forgot-password` - Password reset request
- `/reset-password/:token` - Password reset form
- `/profile` - User profile management
- `/settings` - Account settings

### Middleware & Security Controls

**Authentication Middleware**:
```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

**Security Controls**:
1. **Rate Limiting**: 
   - 5 failed login attempts → 15min lockout
   - 100 requests/hour per IP for auth endpoints
2. **CSRF Protection**: Flask-WTF CSRF tokens
3. **Secure Cookies**: 
   - `HttpOnly`, `Secure`, `SameSite=Strict`
   - Session timeout: 7 days (with remember me)
4. **Password Security**:
   - bcrypt with 12+ rounds
   - Minimum 8 characters, mixed case, numbers
5. **Email Validation**:
   - DNS MX record validation
   - Disposable email detection
6. **Audit Logging**: All auth events logged with IP/user agent

### Implementation Notes (Flask Patterns)

**Suggested Libraries**:
- `Flask-Login` for session management
- `Flask-WTF` for forms and CSRF
- `Flask-Mail` for email sending
- `Flask-Limiter` for rate limiting
- `authlib` for OAuth integration
- `bcrypt` for password hashing
- `itsdangerous` for secure tokens

**Email Service Integration**:
```python
# Use SendGrid/Mailgun/Amazon SES
# Template-based emails for:
# - Verification
# - Password reset
# - Welcome email
# - Security alerts
```

**Estimated Effort**: 3-4 weeks
**Risk Level**: Medium (security critical, requires careful implementation)

---

## Milestone 2: Authorization & Admin System

### User Stories & Acceptance Criteria

**US1: Role-Based Access Control**
- As an admin, I want to assign roles to users
- **AC1**: Roles: user, admin, staff (optional)
- **AC2**: Permission-based access control
- **AC3**: Role assignment interface
- **AC4**: Permission inheritance

**US2: Admin Dashboard**
- As an admin, I want to manage users
- **AC1**: User list with search/filter
- **AC2**: User detail view with edit capabilities
- **AC3**: Role management interface
- **AC4**: User suspension/activation

**US3: Content Management**
- As an admin, I want to manage app configuration
- **AC1**: System settings interface
- **AC2**: Feature flag management
- **AC3**: Content moderation tools
- **AC4**: Announcement management

**US4: Admin Activity Logging**
- As an admin, I want to see admin actions
- **AC1**: All admin actions logged
- **AC2**: Searchable audit trail
- **AC3**: Export capabilities
- **AC4**: Real-time notifications for critical actions

**US5: Safe Admin Patterns**
- As a system, I want to prevent admin mistakes
- **AC1**: Confirmation dialogs for destructive actions
- **AC2**: Two-person approval for critical changes
- **AC3**: Change rollback capability
- **AC4**: Least privilege enforcement

### Database Schema Changes

```sql
-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL, -- 'user', 'admin', 'staff'
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL, -- 'manage_users', 'view_admin', 'manage_content'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- User-Role mapping
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Admin audit logs
CREATE TABLE admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100), -- 'user', 'content', 'settings'
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    data_type VARCHAR(50) DEFAULT 'string', -- 'string', 'number', 'boolean', 'array', 'object'
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_logs_created_at ON admin_audit_logs(created_at);
```

### API Routes & UI Pages

**Admin API Routes**:
- `GET /api/admin/users` - List users (paginated, filtered)
- `GET /api/admin/users/:user_id` - Get user details
- `PUT /api/admin/users/:user_id` - Update user
- `POST /api/admin/users/:user_id/roles` - Assign role
- `DELETE /api/admin/users/:user_id/roles/:role_id` - Remove role
- `GET /api/admin/roles` - List roles
- `GET /api/admin/permissions` - List permissions
- `GET /api/admin/audit-logs` - View admin audit logs
- `GET /api/admin/settings` - List system settings
- `PUT /api/admin/settings/:key` - Update system setting

**UI Pages**:
- `/admin` - Admin dashboard
- `/admin/users` - User management
- `/admin/users/:id` - User detail/edit
- `/admin/roles` - Role management
- `/admin/audit-logs` - Audit trail
- `/admin/settings` - System settings

### Middleware & Security Controls

**Admin Middleware**:
```python
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

**Permission Middleware**:
```python
def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission_name):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Security Controls**:
1. **Admin IP Whitelisting**: Optional restriction to specific IP ranges
2. **Session Timeout**: Admin sessions timeout after 2h inactivity
3. **Two-Factor Authentication**: Optional 2FA for admin accounts
4. **Change Approval Workflow**: Critical changes require approval
5. **Data Export Controls**: Sensitive data export requires audit

### Implementation Notes

**Suggested Libraries**:
- `Flask-Principal` for permission management
- `SQLAlchemy` for ORM (if not already using)
- `Flask-Admin` for admin interface (optional)

**Admin UI Patterns**:
- Use React/Vue for dynamic admin interface
- Real-time updates via WebSockets
- Export to CSV/JSON functionality
- Bulk operations with progress tracking

**Estimated Effort**: 2-3 weeks
**Risk Level**: Medium (security implications for admin access)

---

## Milestone 3: Billing & Subscriptions

### User Stories & Acceptance Criteria

**US1: Subscription Plans**
- As a user, I want to choose a subscription plan
- **AC1**: Plan display with features/limits
- **AC2**: Free tier with basic limits
- **AC3**: Pro tier with enhanced limits
- **AC4**: Enterprise tier with custom limits

**US2: Stripe Checkout**
- As a user, I want to subscribe via Stripe
- **AC1**: Stripe-hosted checkout
- **AC2**: Multiple payment methods
- **AC3**: Secure payment processing
- **AC4**: Receipt email confirmation

**US3: Customer Portal**
- As a subscriber, I want to manage my subscription
- **AC1**: View current plan and billing info
- **AC2**: Upgrade/downgrade/cancel subscription
- **AC3**: View/pay invoices
- **AC4**: Update payment method

**US4: Usage Tracking**
- As a user, I want to see my usage
- **AC1**: Usage dashboard with limits
- **AC2**: Real-time usage tracking
- **AC3**: Usage alerts (80%, 90%, 100%)
- **AC4**: Historical usage reports

**US5: Webhook Handling**
- As a system, I want to handle Stripe webhooks
- **AC1**: Idempotent webhook processing
- **AC2**: Signature verification
- **AC3**: Event logging and retry logic
- **AC4**: Failed webhook notification

**US6: Entitlement Enforcement**
- As a system, I want to enforce plan limits
- **AC1**: Middleware for API rate limiting
- **AC2**: Feature flag based on subscription
- **AC3**: Grace period for failed payments
- **AC4**: Automated downgrade on cancellation

### Database Schema Changes

```sql
-- Subscription plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_price_id VARCHAR(255) UNIQUE,
    name VARCHAR(100) NOT NULL, -- 'Free', 'Pro', 'Enterprise'
    description TEXT,
    price_monthly DECIMAL(10, 2), -- NULL for free tier
    price_yearly DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    features JSONB NOT NULL, -- {"max_generations": 10, "max_file_size": 100, ...}
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    plan_id UUID REFERENCES subscription_plans(id),
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'past_due', 'canceled', 'incomplete'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    trial_ends_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_invoice_id VARCHAR(255) UNIQUE,
    subscription_id UUID REFERENCES user_subscriptions(id),
    amount DECIMAL(10, 2) NOT