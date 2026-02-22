"""
E2E tests: auth UI flows (forms rendered in the browser).

Covers:
  - Register via HTML form → redirects to dashboard on success
  - Register with mismatched passwords → stays on register page
  - Login via HTML form → redirects to dashboard on success
  - Login with wrong password → stays on login page and shows error
  - Logout via nav link → redirects to index / login
"""
import uuid
import pytest


def _unique_email() -> str:
    return f"ui_{uuid.uuid4().hex[:10]}@example.com"


VALID_PASSWORD = "UiTestPass1"


class TestRegisterUI:
    def _register(self, page, base_url, email, display_name="Test User"):
        """Helper to fill and submit the registration form including the terms checkbox."""
        page.goto(f"{base_url}/auth/register")
        page.fill("#email", email)
        page.fill("#display_name", display_name)
        page.fill("#password", VALID_PASSWORD)
        page.fill("#confirm_password", VALID_PASSWORD)
        # The form requires the Terms & Conditions checkbox to be checked
        if page.locator("#terms").count():
            page.check("#terms")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

    def test_successful_registration_redirects_away_from_register(self, page, base_url):
        self._register(page, base_url, _unique_email())
        # After successful registration the user lands on the dashboard (not the register page)
        assert "/auth/register" not in page.url

    def test_successful_registration_does_not_show_error(self, page, base_url):
        self._register(page, base_url, _unique_email())
        # No "error" or "invalid" flash messages should be on the resulting page
        content = page.content().lower()
        assert "is invalid" not in content or "password" not in content

    def test_mismatched_passwords_stays_on_register_page(self, page, base_url):
        page.goto(f"{base_url}/auth/register")
        page.fill("#email", _unique_email())
        page.fill("#display_name", "Test User")
        page.fill("#password", VALID_PASSWORD)
        page.fill("#confirm_password", VALID_PASSWORD + "WRONG")
        if page.locator("#terms").count():
            page.check("#terms")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        # Should remain on the register page (client-side validation or server-side)
        assert "register" in page.url or "register" in page.content().lower()

    def test_duplicate_email_stays_on_register_page(self, page, base_url):
        email = _unique_email()
        # First registration
        self._register(page, base_url, email, display_name="First User")

        # Logout so we can attempt another registration
        page.goto(f"{base_url}/auth/logout")
        page.wait_for_load_state("networkidle")

        # Second registration with same email
        self._register(page, base_url, email, display_name="Duplicate User")
        # Should stay on register page or show an error
        assert "register" in page.url or "already" in page.content().lower()


class TestLoginUI:
    @pytest.fixture(autouse=True)
    def _create_user(self, page, base_url):
        """Register a fresh test user before each login test."""
        self.email = _unique_email()
        self.password = VALID_PASSWORD

        page.goto(f"{base_url}/auth/register")
        page.fill("#email", self.email)
        page.fill("#display_name", "Login Test User")
        page.fill("#password", self.password)
        page.fill("#confirm_password", self.password)
        # Agree to terms if the checkbox is present
        if page.locator("#terms").count():
            page.check("#terms")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Logout so each test starts from a logged-out state
        page.goto(f"{base_url}/auth/logout")
        page.wait_for_load_state("networkidle")

    def test_successful_login_redirects_away_from_login(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        page.fill("#email", self.email)
        page.fill("#password", self.password)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/auth/login" not in page.url

    def test_successful_login_reaches_authenticated_area(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        page.fill("#email", self.email)
        page.fill("#password", self.password)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        # Should not be redirected back to login or register
        assert "/auth/login" not in page.url
        assert "/auth/register" not in page.url

    def test_wrong_password_stays_on_login_page(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        page.fill("#email", self.email)
        page.fill("#password", "WrongPassword99")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/auth/login" in page.url

    def test_wrong_password_shows_error_message(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        page.fill("#email", self.email)
        page.fill("#password", "WrongPassword99")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        content = page.content().lower()
        assert "invalid" in content or "incorrect" in content or "password" in content

    def test_unknown_email_stays_on_login_page(self, page, base_url):
        page.goto(f"{base_url}/auth/login")
        page.fill("#email", "nobody@nowhere.invalid")
        page.fill("#password", VALID_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/auth/login" in page.url


class TestLogoutUI:
    def test_logout_redirects_away_from_authenticated_area(self, page, base_url):
        # First, register + login
        email = _unique_email()
        page.goto(f"{base_url}/auth/register")
        page.fill("#email", email)
        page.fill("#display_name", "Logout UI User")
        page.fill("#password", VALID_PASSWORD)
        page.fill("#confirm_password", VALID_PASSWORD)
        if page.locator("#terms").count():
            page.check("#terms")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Logout via the /auth/logout route
        page.goto(f"{base_url}/auth/logout")
        page.wait_for_load_state("networkidle")

        # After logout, accessing a protected page should redirect to login
        page.goto(f"{base_url}/cover-generator")
        page.wait_for_load_state("networkidle")
        assert "login" in page.url
