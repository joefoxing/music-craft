"""
E2E tests: JSON auth API  (/api/auth/*)

Covers:
  - GET  /api/auth/csrf          → returns a CSRF token
  - POST /api/auth/register      → creates a user, returns 201
  - POST /api/auth/login         → authenticates, returns 200
  - POST /api/auth/login (bad)   → returns 4xx on wrong credentials
  - POST /api/auth/logout        → ends the session
  - POST /api/auth/register (dup) → 409 on duplicate email
"""
import uuid
import pytest


def _unique_email() -> str:
    return f"e2e_{uuid.uuid4().hex[:10]}@example.com"


def _json_headers(csrf_token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
    }


def _get_csrf(page, base_url: str) -> str:
    resp = page.request.get(f"{base_url}/api/auth/csrf")
    return resp.json().get("csrf_token", "")


class TestCsrfEndpoint:
    def test_csrf_endpoint_returns_200(self, page, base_url):
        resp = page.request.get(f"{base_url}/api/auth/csrf")
        assert resp.status == 200

    def test_csrf_endpoint_returns_token(self, page, base_url):
        resp = page.request.get(f"{base_url}/api/auth/csrf")
        body = resp.json()
        assert "csrf_token" in body
        assert isinstance(body["csrf_token"], str)
        assert len(body["csrf_token"]) > 0


class TestRegisterAPI:
    def test_register_new_user_returns_201(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": _unique_email(), "password": "TestPass1"},
            headers=_json_headers(csrf),
        )
        assert resp.status == 201

    def test_register_response_contains_user(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        email = _unique_email()
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": email, "password": "TestPass1"},
            headers=_json_headers(csrf),
        )
        body = resp.json()
        assert body.get("success") is True
        assert "user" in body

    def test_register_duplicate_email_returns_409(self, page, base_url):
        email = _unique_email()
        # First registration (auto-logs-in the user)
        csrf = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": email, "password": "TestPass1"},
            headers=_json_headers(csrf),
        )
        # Log out so the session is anonymous before the duplicate attempt
        csrf_out = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/logout",
            headers=_json_headers(csrf_out),
        )
        # Second registration with the same email
        csrf2 = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": email, "password": "TestPass1"},
            headers=_json_headers(csrf2),
        )
        assert resp.status == 409

    def test_register_missing_fields_returns_400(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": _unique_email()},  # no password
            headers=_json_headers(csrf),
        )
        assert resp.status == 400

    def test_register_weak_password_returns_400(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": _unique_email(), "password": "short"},
            headers=_json_headers(csrf),
        )
        assert resp.status == 400

    def test_register_invalid_email_returns_400(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": "not-an-email", "password": "TestPass1"},
            headers=_json_headers(csrf),
        )
        assert resp.status == 400


class TestLoginAPI:
    @pytest.fixture(autouse=True)
    def _setup_user(self, page, base_url):
        """Register a fresh user for each test in this class."""
        self.email = _unique_email()
        self.password = "LoginPass9"
        csrf = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": self.email, "password": self.password},
            headers=_json_headers(csrf),
        )
        # Logout so we start from an unauthenticated state
        csrf2 = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/logout",
            headers=_json_headers(csrf2),
        )

    def test_login_valid_credentials_returns_200(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"email": self.email, "password": self.password},
            headers=_json_headers(csrf),
        )
        assert resp.status == 200

    def test_login_response_contains_user(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"email": self.email, "password": self.password},
            headers=_json_headers(csrf),
        )
        body = resp.json()
        assert "user" in body

    def test_login_wrong_password_returns_4xx(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"email": self.email, "password": "WrongPass99"},
            headers=_json_headers(csrf),
        )
        assert resp.status >= 400

    def test_login_unknown_email_returns_4xx(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"email": "nobody@nowhere.invalid", "password": "TestPass1"},
            headers=_json_headers(csrf),
        )
        assert resp.status >= 400

    def test_login_missing_fields_returns_400(self, page, base_url):
        csrf = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"email": self.email},  # missing password
            headers=_json_headers(csrf),
        )
        assert resp.status == 400


class TestLogoutAPI:
    def test_logout_after_login_succeeds(self, page, base_url):
        email = _unique_email()
        # Register
        csrf = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": email, "password": "LogoutPass1"},
            headers=_json_headers(csrf),
        )
        # Logout
        csrf2 = _get_csrf(page, base_url)
        resp = page.request.post(
            f"{base_url}/api/auth/logout",
            headers=_json_headers(csrf2),
        )
        assert resp.status == 200

    def test_protected_route_after_logout_requires_auth(self, page, base_url):
        email = _unique_email()
        # Register → auto-logged-in
        csrf = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/register",
            data={"email": email, "password": "LogoutPass1"},
            headers=_json_headers(csrf),
        )
        # Logout
        csrf2 = _get_csrf(page, base_url)
        page.request.post(
            f"{base_url}/api/auth/logout",
            headers=_json_headers(csrf2),
        )
        # Attempt to access protected page
        resp = page.goto(f"{base_url}/cover-generator")
        # Should either be 401 or redirect to login (final URL contains /auth/login or /login)
        assert resp.status in (200, 302, 401) and (
            resp.status == 401
            or "login" in page.url
        )
