"""
E2E tests: public routes (no authentication required).

Covers:
  - /health  → JSON { status: "healthy" }
  - /        → index page renders
  - /auth/login    → login form renders
  - /auth/register → register form renders
  - /lyrics-extraction → accessible without login
"""
import pytest


class TestHealthCheck:
    def test_health_endpoint_returns_200(self, page, base_url):
        resp = page.request.get(f"{base_url}/health")
        assert resp.status == 200

    def test_health_endpoint_returns_healthy_status(self, page, base_url):
        resp = page.request.get(f"{base_url}/health")
        body = resp.json()
        assert body.get("status") == "healthy"

    def test_health_endpoint_includes_timestamp(self, page, base_url):
        resp = page.request.get(f"{base_url}/health")
        body = resp.json()
        assert "timestamp" in body


class TestIndexPage:
    def test_index_page_loads(self, page, base_url):
        resp = page.goto(f"{base_url}/")
        assert resp.status == 200

    def test_index_page_has_html_content(self, page, base_url):
        page.goto(f"{base_url}/")
        # Page should be actual HTML, not an error page
        assert page.title() != ""
        assert page.content().strip().startswith("<!") or "<html" in page.content().lower()


class TestLoginPage:
    def test_login_page_loads(self, page, base_url):
        resp = page.goto(f"{base_url}/auth/login")
        assert resp.status == 200

    def test_login_page_has_email_field(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        assert page.locator("#email").count() == 1

    def test_login_page_has_password_field(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        assert page.locator("#password").count() == 1

    def test_login_page_has_submit_button(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        assert page.locator('button[type="submit"]').count() >= 1


class TestRegisterPage:
    def test_register_page_loads(self, page, base_url):
        resp = page.goto(f"{base_url}/auth/register")
        assert resp.status == 200

    def test_register_page_has_email_field(self, page, base_url):
        page.goto(f"{base_url}/auth/register")
        assert page.locator("#email").count() == 1

    def test_register_page_has_password_field(self, page, base_url):
        page.goto(f"{base_url}/auth/register")
        assert page.locator("#password").count() == 1

    def test_register_page_has_confirm_password_field(self, page, base_url):
        page.goto(f"{base_url}/auth/register")
        assert page.locator("#confirm_password").count() == 1

    def test_register_page_has_submit_button(self, page, base_url):
        page.goto(f"{base_url}/auth/register")
        assert page.locator('button[type="submit"]').count() >= 1


class TestLyricsExtractionPage:
    """Lyrics extraction page should be visible without authentication."""

    def test_lyrics_extraction_accessible_without_login(self, page, base_url):
        resp = page.goto(f"{base_url}/lyrics-extraction")
        assert resp.status == 200
