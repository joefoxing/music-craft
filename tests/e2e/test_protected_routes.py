"""
E2E tests: protected routes.

When an unauthenticated user visits a login-required page, Flask should
redirect to /auth/login (or return 401 for JSON requests).

Covers every @login_required route in main_bp:
  - /cover-generator
  - /music-generator
  - /history
  - /library
  - /admin
  - /playlist/<id>
"""
import pytest


PROTECTED_ROUTES = [
    "/cover-generator",
    "/music-generator",
    "/history",
    "/library",
    "/admin",
    "/playlist/00000000-0000-0000-0000-000000000001",
]


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_unauthenticated_redirects_to_login(page, base_url, route):
    """Every protected page must send an unauthenticated visitor to the login page."""
    page.goto(f"{base_url}{route}")
    page.wait_for_load_state("networkidle")
    assert "login" in page.url, (
        f"Expected /auth/login after visiting {route}, but got {page.url}"
    )


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_unauthenticated_does_not_render_protected_content(page, base_url, route):
    """Visiting a protected page without being logged in must NOT render that page."""
    page.goto(f"{base_url}{route}")
    page.wait_for_load_state("networkidle")
    # The final URL should contain "login", meaning we were redirected
    assert "login" in page.url


class TestAuthenticatedAccess:
    """After logging in, protected pages should be reachable."""

    def test_cover_generator_accessible_after_login(self, authenticated_page, base_url):
        authenticated_page.goto(f"{base_url}/cover-generator")
        authenticated_page.wait_for_load_state("networkidle")
        assert "login" not in authenticated_page.url

    def test_music_generator_accessible_after_login(self, authenticated_page, base_url):
        authenticated_page.goto(f"{base_url}/music-generator")
        authenticated_page.wait_for_load_state("networkidle")
        assert "login" not in authenticated_page.url

    def test_history_accessible_after_login(self, authenticated_page, base_url):
        authenticated_page.goto(f"{base_url}/history")
        authenticated_page.wait_for_load_state("networkidle")
        assert "login" not in authenticated_page.url

    def test_library_accessible_after_login(self, authenticated_page, base_url):
        authenticated_page.goto(f"{base_url}/library")
        authenticated_page.wait_for_load_state("networkidle")
        assert "login" not in authenticated_page.url
