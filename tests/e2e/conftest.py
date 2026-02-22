"""
E2E test configuration.

Starts a live Flask test server (session-scoped) and wires it up as
the Playwright base_url so every page.goto("/some/path") resolves
against the test server.
"""
import os
import sys
import tempfile
import pytest

# Make sure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app import create_app, db as _db  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_config(db_path: str) -> dict:
    return {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
        },
        "WTF_CSRF_ENABLED": False,
        "AUTO_CREATE_DB": True,
        "SECRET_KEY": "e2e-test-secret-key",
        # Suppress all email delivery
        "MAIL_SUPPRESS_SEND": True,
        "MAIL_DEFAULT_SENDER": "test@test.local",
        # Disable rate limiting so auth tests don't trip limits
        "RATELIMIT_ENABLED": False,
        "LOGIN_RATE_LIMIT": "10000 per minute",
        "REGISTER_RATE_LIMIT": "10000 per hour",
        # Don't set SERVER_NAME so url_for works without a host prefix
        "SERVER_NAME": None,
    }


# ---------------------------------------------------------------------------
# App & DB fixtures  (session scope → shared across all E2E tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """Create a Flask test application backed by a temp SQLite file."""
    db_dir = tmp_path_factory.mktemp("e2e_db")
    db_path = str(db_dir / "e2e_test.db")

    flask_app = create_app(_make_test_config(db_path))

    # The AUTO_CREATE_DB flag already creates all tables inside create_app,
    # but we push a context explicitly so fixtures can use flask.g / db.
    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    # Teardown: drop everything
    with flask_app.app_context():
        _db.drop_all()


# ---------------------------------------------------------------------------
# live_server scope (tell pytest-flask to keep the server alive for the
# whole session instead of restarting it per test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def live_server_scope():
    """Keep the live server running for the entire test session."""
    return "session"


# ---------------------------------------------------------------------------
# Override pytest-playwright's base_url with the live server URL
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url(live_server):
    """Point Playwright at the live Flask test server."""
    return live_server.url()


# ---------------------------------------------------------------------------
# Convenience: an authenticated page fixture
# A new Playwright browser context is created, the user is registered
# and logged-in via the API, and the authenticated cookies are stored.
# ---------------------------------------------------------------------------

@pytest.fixture()
def authenticated_page(page, base_url):
    """
    Return a Playwright page that is already logged in as a test user.

    Uses the JSON API endpoints to register + login so that the session
    cookie is set in the Playwright browser context.
    """
    import uuid
    unique = uuid.uuid4().hex[:8]
    email = f"e2e_{unique}@example.com"
    password = "TestPass1"

    # Get CSRF token (needed for the JSON API auth endpoints)
    csrf_resp = page.request.get(f"{base_url}/api/auth/csrf")
    csrf_token = csrf_resp.json().get("csrf_token", "")

    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
    }

    # Register
    page.request.post(
        f"{base_url}/api/auth/register",
        data={"email": email, "password": password},
        headers=headers,
    )

    # Login (re-fetch CSRF token – it may rotate after register)
    csrf_resp2 = page.request.get(f"{base_url}/api/auth/csrf")
    csrf_token2 = csrf_resp2.json().get("csrf_token", "")
    headers["X-CSRFToken"] = csrf_token2

    page.request.post(
        f"{base_url}/api/auth/login",
        data={"email": email, "password": password},
        headers=headers,
    )

    yield page
