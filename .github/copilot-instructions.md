# Copilot Instructions for Music Craft Repository

## Project Overview

**Music Craft** is a web-based Music Cover Generator (v1.0.0) that enables users to upload audio files and transform them into new musical styles using AI. The application integrates with the Kie AI API for music generation and includes features like lyrics extraction, template management, and user activity tracking.

### Technology Stack

- **Backend**: Python 3.9+ with Flask 2.3.3 web framework
- **Database**: PostgreSQL 15 (production), SQLite (development fallback)
- **ORM**: SQLAlchemy 2.0 with Alembic for migrations
- **Authentication**: Flask-Login, Flask-Bcrypt, OAuth (Google/GitHub via Authlib)
- **AI/Audio**: Kie AI API, OpenAI Whisper, Demucs 4.0, Mutagen
- **Frontend**: Vanilla JavaScript with responsive UI
- **Deployment**: Docker/Docker Compose, Gunicorn, Caddy reverse proxy
- **CI/CD**: GitHub Actions for automated deployments

### Architecture Patterns

The application follows a **modular Flask architecture** with clear separation of concerns:

```
app/
├── __init__.py          # App factory pattern with create_app()
├── config.py            # Centralized configuration (40+ settings)
├── models.py            # SQLAlchemy database models
├── forms.py             # WTForms for form validation
├── routes/              # Blueprint-based route handlers
│   ├── api.py           # Main API endpoints
│   ├── auth.py          # Authentication routes
│   ├── callback.py      # Kie API callbacks
│   └── main.py          # Frontend routes
├── services/            # Business logic layer
│   ├── callback_service.py
│   ├── template_service.py
│   └── history_service.py
├── core/                # Core utilities and API clients
└── static/              # CSS, JS, uploads, templates.json
```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for local development)
- PostgreSQL 15 (if not using Docker)
- Kie API key from https://kie.ai/api-key

### Quick Start

1. **Clone and setup environment**:
   ```bash
   git clone <repo-url>
   cd music-craft
   cp .env.example .env
   # Edit .env and add your KIE_API_KEY
   ```

2. **Using Docker (recommended)**:
   ```bash
   make up      # Start services (db + app)
   make logs    # View logs
   make shell   # Access container bash
   make down    # Stop services
   make reset   # Clean reset with volume deletion
   ```

3. **Local Python development**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python run.py
   ```
   **Note**: Access the app at http://localhost:5000

### Environment Configuration

Key environment variables in `.env`:

```bash
# Flask
SECRET_KEY=your-secret-key
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/music_cover_generator
# Or for development: sqlite:///app.db

# Kie API
KIE_API_KEY=your-api-key
USE_MOCK=false

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# OAuth
OAUTH_ENABLED=false
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GITHUB_OAUTH_CLIENT_ID=your-client-id
```

See `.env.example` for complete configuration options (100+ settings).

## Common Commands

### Testing

**Important**: The project uses `pytest` for testing, but tests are primarily manual/integration tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_admin_delete.py

# Run with verbose output
pytest -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=app
```

**Known Test Files**:
- `tests/test_admin_delete.py` - Admin deletion functionality
- `tests/test_uppercase_line_breaks.py` - Lyrics formatting
- `tests/test_vietnamese_lyrics.py` - Vietnamese text handling
- `tests/test_word_based_lyrics_formatting.py` - Word-based lyrics

### Linting & Code Quality

```bash
# Code formatting with Black
black .

# Check code without formatting
black --check .
```

### Database Management

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# View migration history
alembic history

# Using Docker
docker compose exec app alembic upgrade head
```

### Docker Operations

```bash
# Build images
make build
docker compose build

# View logs
make logs
docker compose logs -f app

# Access shell
make shell
docker compose exec app /bin/bash

# Restart services
docker compose restart app

# Clean volumes (WARNING: deletes data)
make reset
docker compose down -v
```

## Coding Standards & Patterns

### Python/Flask Guidelines

1. **Follow existing patterns**: The codebase uses established Flask patterns. Don't introduce new architectural approaches without justification.

2. **Use blueprints for routes**: All route handlers should be organized into blueprints under `app/routes/`.

3. **Business logic in services**: Keep route handlers thin. Business logic goes in `app/services/`.

4. **Configuration via Config class**: All configuration should use `app/config.py`. Never hardcode values.

5. **Use SQLAlchemy ORM**: Direct SQL queries should be avoided. Use the ORM defined in `app/models.py`.

6. **Input validation**: Always validate user inputs. Use WTForms for form validation.

7. **Error handling**: Return consistent JSON error responses:
   ```python
   return jsonify({'error': 'Description', 'details': details}), 400
   ```

8. **Logging**: Use structured logging. Never log secrets or sensitive data:
   ```python
   app.logger.info('Processing request', extra={'user_id': user.id})
   ```

9. **Type hints**: Use Python type hints where appropriate for better code clarity.

10. **Docstrings**: Add docstrings to functions and classes following the existing style.

### Database Patterns

1. **Model definitions**: All models in `app/models.py` use SQLAlchemy declarative base.

2. **Relationships**: Use SQLAlchemy relationships for foreign keys:
   ```python
   user = db.relationship('User', backref='history_items')
   ```

3. **Migrations**: Always create Alembic migrations for schema changes. Never modify the database directly.

4. **Sessions**: Use Flask-SQLAlchemy's session management:
   ```python
   db.session.add(item)
   db.session.commit()
   ```

5. **Queries**: Use SQLAlchemy query API:
   ```python
   user = User.query.filter_by(email=email).first()
   ```

### Frontend Guidelines

1. **Vanilla JavaScript**: The project uses vanilla JS. Don't introduce React, Vue, or other frameworks.

2. **Responsive design**: Maintain mobile-first responsive design patterns.

3. **Templates**: Use Jinja2 templates in `app/templates/`.

4. **Static assets**: CSS, JS, and images go in `app/static/`.

5. **AJAX patterns**: Follow existing patterns for AJAX calls with proper error handling.

## API Integration

### Kie AI API Client

The main integration is in `app/kie_client.py`:

```python
from app.kie_client import KieAPIClient

client = KieAPIClient()
result = client.generate_music(audio_file, prompt, **params)
```

**Key methods**:
- `generate_music()` - Submit music generation task
- `get_task_status()` - Poll task status
- `get_task_result()` - Retrieve completed task

### Callback System

Callbacks are handled in `app/routes/callback.py` and `app/services/callback_service.py`:

- **Callback types**: text, first, complete, error
- **Status codes**: Interpreted for user-friendly messages
- **History tracking**: All callbacks stored with JSON payloads

## Common Issues & Workarounds

### 1. Dependency Installation Failures

**Issue**: `ModuleNotFoundError: No module named 'pkg_resources'` when installing requirements.

**Root Cause**: Some packages (like `demucs`, `openai-whisper`) have legacy setup.py files that require setuptools' pkg_resources, which is deprecated in newer Python versions.

**Workarounds**:

**Option A** (Recommended for development):
```bash
# Install critical dependencies first, skip problematic ones temporarily
pip install Flask==2.3.3 Flask-CORS==4.0.0 requests python-dotenv
pip install Flask-Login Flask-WTF Flask-Mail Flask-Limiter Flask-Bcrypt
pip install SQLAlchemy==2.0.45 psycopg[binary]==3.2.3 Flask-SQLAlchemy alembic
pip install gunicorn

# Skip audio processing packages if not needed for your changes
# (openai-whisper, demucs are only needed for lyrics extraction)
```

**Option B** (Use Docker):
```bash
# Docker has all dependencies pre-installed
make up
make shell
```

**Option C** (Install setuptools legacy support):
```bash
pip install --upgrade pip setuptools
pip install setuptools-rust  # Sometimes needed for audio packages
```

**When working on code changes**:
- If your changes don't involve lyrics extraction or audio processing, you can skip installing `openai-whisper` and `demucs`
- The app will gracefully handle missing optional dependencies
- Use `USE_MOCK=true` in `.env` to bypass external API calls during testing

### 2. Database Connection Issues

**Issue**: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`

**Solution**:
```bash
# Ensure the directory exists
mkdir -p instance

# Or use PostgreSQL via Docker
docker compose up -d db
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/music_craft
```

### 3. Missing Environment Variables

**Issue**: `KeyError: 'KIE_API_KEY'` or similar errors.

**Solution**:
```bash
# Always copy .env.example first
cp .env.example .env
# Edit .env with your actual values

# Load environment in Python
from dotenv import load_dotenv
load_dotenv(override=True)
```

### 4. CSRF Token Errors

**Issue**: 403 errors on form submissions with "CSRF token missing or incorrect".

**Solution**:
- Ensure forms include `{{ form.hidden_tag() }}` in Jinja2 templates
- API endpoints should be exempted with `@csrf.exempt` decorator
- For AJAX requests, include CSRF token in headers

### 5. File Upload Issues

**Issue**: Files not uploading or "File too large" errors.

**Solution**:
```python
# Check MAX_CONTENT_LENGTH in config
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Ensure upload folder exists
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
```

### 6. Docker Port Conflicts

**Issue**: `Error starting userland proxy: listen tcp4 0.0.0.0:5000: bind: address already in use`

**Solution**:
```bash
# Find and kill process using port
lsof -ti:5000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "5001:5000"
```

### 7. Migration Conflicts

**Issue**: Alembic detects unexpected schema changes.

**Solution**:
```bash
# Check current revision
alembic current

# If out of sync, stamp to current
alembic stamp head

# Create new migration
alembic revision --autogenerate -m "Description"

# Review the generated migration file before applying
```

## CI/CD & Deployment

### GitHub Actions Workflows

**`.github/workflows/deploy.yml`**:
- **Trigger**: Push to `main` branch or manual workflow dispatch
- **Jobs**:
  1. `build-and-push`: Builds Docker image, pushes to GHCR
  2. `deploy-staging`: Auto-deploys to staging environment
  3. `deploy-production`: Manual deploy to production (requires SHA tag)

**`.github/workflows/migrate.yml`**:
- **Trigger**: Manual workflow dispatch
- **Purpose**: Run database migrations on staging or production
- **Usage**: Select environment, runs `alembic upgrade head`

### Deployment Workflow

1. **Staging**: Automatically deploys on merge to `main`
   ```bash
   # Changes to main trigger:
   # - Docker build with SHA tag
   # - Push to GHCR
   # - SSH to staging server
   # - Pull latest code
   # - Update IMAGE_TAG in .env.staging
   # - Run scripts/deploy-staging.sh
   ```

2. **Production**: Manual workflow dispatch with SHA tag
   ```bash
   # In GitHub Actions:
   # - Select "Run workflow"
   # - Choose "production"
   # - Enter image SHA (from staging build)
   # - Workflow SSHs to production and deploys
   ```

3. **Rollback**:
   ```bash
   # On server
   cd ~/app
   bash scripts/rollback.sh
   # Or for staging
   bash scripts/rollback-staging.sh
   ```

### Required Secrets & Variables

**Repository Secrets**:
- `SSH_PRIVATE_KEY` - SSH key for deployment access
- `GHCR_TOKEN` - GitHub Container Registry token

**Environment Variables**:
- `STAGING_HOST`, `STAGING_USER`, `STAGING_DOMAIN`
- `PROD_HOST`, `PROD_USER`, `DOMAIN`

## Testing Strategy

### Unit Tests

Focus on business logic in services:
```bash
pytest tests/test_admin_delete.py
pytest tests/test_word_based_lyrics_formatting.py
```

### Integration Tests

Test complete workflows:
```bash
# Example: Test full music generation flow
pytest tests/test_flask_integration.py -v
```

### Manual Testing

1. **Start the application**:
   ```bash
   python run.py
   # Or with Docker
   make up
   ```

2. **Test key workflows**:
   - User registration and login
   - Audio file upload
   - Music generation (both Simple and Custom modes)
   - Callback processing
   - History viewing
   - Template application

3. **Check logs**:
   ```bash
   # Local
   tail -f logs/app.log
   
   # Docker
   make logs
   ```

### Test Database

For testing with a separate database:
```bash
export DATABASE_URL=sqlite:///test.db
export FLASK_ENV=testing
pytest
```

## Documentation

### Key Documentation Files

- **README.md** - Main project documentation, setup instructions
- **API_ENDPOINTS_SPECIFICATION.md** - Complete API reference
- **CI_CD_RUNBOOK.md** - Deployment procedures
- **PRODUCTION_AND_STAGING_RUNBOOK.md** - Operations guide
- **COMPREHENSIVE_SYSTEM_DOCUMENTATION.md** - System architecture
- **docs/AI_RULES.md** - AI assistant guidelines (minimal diffs, no refactoring)
- **CHANGELOG.md** - Version history

### Documentation Standards

1. **Update README.md** when adding new features
2. **Create migration guides** for breaking changes
3. **Document API changes** in API_ENDPOINTS_SPECIFICATION.md
4. **Update CHANGELOG.md** following semantic versioning
5. **Add inline comments** for complex logic (but sparingly)
6. **Write docstrings** for public functions and classes

## Security Considerations

### Authentication & Authorization

1. **User authentication**: Flask-Login with bcrypt password hashing
2. **OAuth support**: Google and GitHub via Authlib
3. **Email verification**: Required for new accounts
4. **Rate limiting**: Applied to login, register, and password reset routes

### API Security

1. **CSRF protection**: Enabled for all form submissions
2. **CORS**: Configured per environment in .env
3. **Input validation**: Required for all user inputs
4. **SQL injection**: Protected via SQLAlchemy ORM (never use raw SQL)

### Secrets Management

1. **Environment variables**: All secrets in `.env`, never committed
2. **API keys**: Stored in environment, accessed via `app.config`
3. **Production secrets**: Managed via deployment scripts
4. **Logging**: Never log sensitive data (passwords, API keys, tokens)

### File Uploads

1. **Size limits**: Enforced via `MAX_CONTENT_LENGTH`
2. **File type validation**: Check MIME types and extensions
3. **Storage**: Uploaded files isolated in `UPLOAD_FOLDER`
4. **Cleanup**: Implement periodic cleanup of old files

## Best Practices for Making Changes

### 1. Understanding Before Modifying

- **Explore first**: Use `view`, `grep`, `glob` tools to understand existing code
- **Check related files**: Look at similar implementations in the codebase
- **Review tests**: Understand what the tests are validating
- **Read documentation**: Check relevant .md files in the repo

### 2. Minimal Changes

- **Surgical edits**: Change only what's necessary to fix the issue
- **Preserve patterns**: Follow existing code style and architecture
- **Don't refactor**: Unless explicitly requested, don't refactor unrelated code
- **Keep interfaces stable**: Don't change public APIs without good reason

### 3. Testing Your Changes

```bash
# 1. Run relevant tests first
pytest tests/test_relevant_module.py

# 2. Make your changes

# 3. Test again
pytest tests/test_relevant_module.py -v

# 4. Check formatting
black --check app/

# 5. Manual testing (if UI changes)
python run.py
# Test in browser at localhost:5000
```

### 4. Iterative Development

- Make small, incremental changes
- Test after each change
- Commit frequently with clear messages
- Use `report_progress` to push changes to PR

### 5. Error Handling

Always handle errors gracefully:
```python
try:
    result = risky_operation()
    return jsonify({'success': True, 'data': result}), 200
except SpecificException as e:
    app.logger.error(f'Operation failed: {str(e)}')
    return jsonify({'error': 'User-friendly message'}), 400
except Exception as e:
    app.logger.exception('Unexpected error')
    return jsonify({'error': 'Internal server error'}), 500
```

## Project-Specific Quirks

### 1. Multiple Dockerfiles

The project has several Dockerfile variants:
- `Dockerfile` - Legacy/basic app container
- `Dockerfile.api` - Main API service (production-ready)
- `Dockerfile.web` - Web service variant
- `Dockerfile.lyrics` - Separate lyrics extraction service

**When to use which**:
- Development: Use `docker-compose.yml` (references Dockerfile.api)
- Production: Use `docker-compose.prod.yml`
- Lyrics microservice: Use `docker-compose.lyrics.yml`

### 2. Configuration Files

Multiple environment-specific configs:
- `.env.example` - Template for local development
- `.env.staging.example` - Staging environment template
- `.env.prod.example` - Production environment template
- `.env.lyrics.example` - Lyrics service configuration

### 3. Legacy Routes

Some routes are in both `app/routes.py` (monolithic file) and `app/routes/*.py` (modular blueprints). The modular approach is preferred for new routes.

### 4. Static Files Handling

- `app/static/uploads/` - User-uploaded audio files
- `app/static/templates.json` - Template library data (loaded dynamically)
- Files in `uploads/` should be excluded from version control via `.gitignore`

### 5. Lyrics Extraction Modes

The app supports three lyrics extraction strategies:
1. **In-process Whisper** - Direct integration (default)
2. **LRCLIB API** - External service fallback
3. **Microservice** - Separate Docker service (production)

Configuration via `LYRICS_USE_MICROSERVICE` and `LYRICS_MICROSERVICE_URL`.

## Quick Reference

### Most Common Tasks

| Task | Command |
|------|---------|
| Start app locally | `python run.py` |
| Start with Docker | `make up` |
| View logs | `make logs` |
| Run tests | `pytest` |
| Format code | `black .` |
| Create migration | `alembic revision --autogenerate -m "msg"` |
| Apply migrations | `alembic upgrade head` |
| Access container | `make shell` |
| Reset database | `make reset` |

### Important File Locations

| Purpose | Location |
|---------|----------|
| Main app factory | `app/__init__.py` |
| Configuration | `app/config.py` |
| Database models | `app/models.py` |
| Route blueprints | `app/routes/*.py` |
| Business logic | `app/services/*.py` |
| API client | `app/kie_client.py` |
| Templates | `app/templates/` |
| Static assets | `app/static/` |
| Tests | `tests/` |
| Migrations | `migrations/versions/` |

### Key URLs (Local Development)

- **Main app**: http://localhost:5000
- **Health check**: http://localhost:5000/health
- **API base**: http://localhost:5000/api
- **Callback endpoint**: http://localhost:5000/callback

## Support & Resources

- **GitHub Repository**: joefoxing/music-craft
- **Kie AI Documentation**: https://kie.ai/docs
- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/

## Notes for AI Assistants

1. **Read docs/AI_RULES.md** for additional guidelines specific to AI assistants
2. **Prefer minimal diffs** - Don't refactor unless explicitly requested
3. **Keep interfaces stable** - Don't change public APIs without justification
4. **Avoid new dependencies** - Use existing libraries unless necessary
5. **Follow existing patterns** - Maintain consistency with the codebase
6. **Test your changes** - Always validate that changes work as expected
7. **Update documentation** - Keep docs in sync with code changes
8. **Use Docker for testing** - If dependency issues arise, use Docker environment

---

**Last Updated**: 2026-02-18
**Version**: 1.0.0
**Maintainer**: joefoxing
