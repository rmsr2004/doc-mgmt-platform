# tests/dynamic_tests/test_csrf_filter.py
"""
Tests for AD-02c: CSRF Filter at the Single Access Point
SR-11a: SameSite=Strict on session cookie
SR-11b: Synchronizer Token Pattern on state-changing requests

Dynamic tests — run against a live deployed API instance.

Relocated from test_ad-02c_csrf.py.
"""
import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.environ.get("BASE_URL", "https://localhost")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_session_with_csrf() -> tuple[requests.Session, str]:
    """
    Opens a session, hits GET /login to initialise the session
    and retrieve the CSRF token from the cookie/response.
    Returns the session and the CSRF token.
    """
    s = requests.Session()
    s.verify = False

    resp = s.get(f"{BASE_URL}/login")
    assert resp.status_code == 200

    # Extract CSRF token from the hidden input in the HTML response
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        resp.text,
    )
    token = match.group(1) if match else ""
    return s, token


def login() -> tuple[requests.Session, str]:
    """
    Logs in as admin and returns the authenticated session
    and the new CSRF token valid for subsequent requests.
    """
    s, token = get_session_with_csrf()

    resp = s.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "L|fP1D%327mB",
        "csrf_token": token,
    }, allow_redirects=False)

    # After login, fetch the new CSRF token from the next page
    resp2 = s.get(f"{BASE_URL}/", allow_redirects=False)
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        resp2.text,
    )
    new_token = match.group(1) if match else token
    return s, new_token


# ---------------------------------------------------------------------------
# SR-11a — SameSite=Strict cookie attribute
# ---------------------------------------------------------------------------

class TestSR11a:
    def test_session_cookie_has_samesite_strict(self):
        """SR-11a: session cookie must carry SameSite=Strict."""
        resp = requests.get(f"{BASE_URL}/login", verify=False)
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in set_cookie, (
            f"SameSite=Strict not found in Set-Cookie: {set_cookie}"
        )

    def test_session_cookie_has_httponly(self):
        """SR-02 / SR-11a: HttpOnly flag must be set."""
        resp = requests.get(f"{BASE_URL}/login", verify=False)
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "HttpOnly" in set_cookie, (
            f"HttpOnly not found in Set-Cookie: {set_cookie}"
        )


# ---------------------------------------------------------------------------
# SR-11b — Synchronizer Token Pattern
# ---------------------------------------------------------------------------

class TestSR11b:
    def test_csrf_token_present_in_login_form(self):
        """SR-11b: login form must contain a csrf_token hidden field."""
        resp = requests.get(f"{BASE_URL}/login", verify=False)
        assert resp.status_code == 200
        match = re.search(
            r'<input[^>]*name=["\']csrf_token["\']',
            resp.text,
        )
        assert match is not None, "csrf_token hidden field not found in login form"

    def test_post_without_csrf_token_is_rejected(self):
        """SR-11b: authenticated POST without CSRF token must return 403."""
        s, _ = login()
        resp = s.post(
            f"{BASE_URL}/documents/upload",
            data={},        # no csrf_token
            allow_redirects=False,
        )
        assert resp.status_code == 403

    def test_post_with_wrong_csrf_token_is_rejected(self):
        """SR-11b: authenticated POST with wrong CSRF token must return 403."""
        s, _ = login()
        resp = s.post(
            f"{BASE_URL}/documents/upload",
            data={"csrf_token": "totally-wrong-token"},
            allow_redirects=False,
        )
        assert resp.status_code == 403

    def test_post_with_valid_csrf_token_passes_filter(self):
        """SR-11b: POST with valid CSRF token must not return 403."""
        s, token = login()
        resp = s.post(
            f"{BASE_URL}/documents/upload",
            data={"csrf_token": token},
            allow_redirects=False,
        )
        assert resp.status_code != 403

    def test_get_request_does_not_require_csrf(self):
        """Safe methods (GET) must never be blocked by the CSRF filter."""
        resp = requests.get(f"{BASE_URL}/health", verify=False)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# AD-02c — Integration: CSRF filter works end-to-end
# ---------------------------------------------------------------------------

class TestAD02c:
    def test_share_document_rejected_without_csrf(self):
        """AD-02c: document share without CSRF token must be rejected."""
        s, _ = login()
        resp = s.post(
            f"{BASE_URL}/documents/1/share",
            data={"reviewer_id": 2},
            allow_redirects=False,
        )
        assert resp.status_code == 403

    def test_admin_toggle_rejected_without_csrf(self):
        """AD-02c: admin action without CSRF token must be rejected."""
        s, _ = login()
        resp = s.post(
            f"{BASE_URL}/admin/users/2/toggle",
            data={},
            allow_redirects=False,
        )
        assert resp.status_code == 403

    def test_full_flow_share_with_valid_csrf(self):
        """
        AD-02c: full flow — login, get token, share with valid token.
        Filter must pass (business logic may return 4xx for other reasons).
        """
        s, token = login()
        resp = s.post(
            f"{BASE_URL}/documents/1/share",
            data={
                "csrf_token": token,
                "reviewer_id": 2,
            },
            allow_redirects=False,
        )
        assert resp.status_code != 403
