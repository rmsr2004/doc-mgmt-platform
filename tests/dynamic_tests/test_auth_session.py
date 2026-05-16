# tests/dynamic_tests/test_auth_session.py
"""
Tests for §1.2: Authentication Session Flow.
Dynamic tests — run against a live deployed API instance.

Done tests sourced from test_delivery_auth_flow.py.
"""

import os
import re
import requests
import pytest
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

from .headers import NO_RATE_LIMIT_HEADERS as headers

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")


@pytest.fixture
def session():
    s = requests.Session()
    s.verify = False
    return s


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _csrf_token(html: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html
    )
    return match.group(1) if match else ""


def _login_as(username: str, password: str) -> requests.Session:
    s = requests.Session()
    s.verify = False
    login_page = s.get(_url("/login"), headers=headers)
    csrf = _csrf_token(login_page.text)
    s.post(_url("/login"),
           data={"username": username, "password": password, "csrf_token": csrf},
           allow_redirects=True,
           headers=headers)
    return s


def test_login_logout_flow(session):
    """
    Verifies the full authentication flow against a running deployment:
    1. Login with valid credentials
    2. Access a protected page
    3. Logout
    4. Verify access is revoked
    """

    # Login
    login_resp = session.post(
        _url("/login"),
        data={
            "username": "alice",
            "password": "tth1mJj5?£58",
        },
        allow_redirects=False,
        timeout=10,
        headers=headers,
    )

    assert login_resp.status_code in (302, 303), (
        f"Login failed unexpectedly: {login_resp.status_code}"
    )

    # Access protected page
    documents_resp = session.get(
        _url("/documents"),
        allow_redirects=False,
        headers=headers,
        timeout=10,
    )

    assert documents_resp.status_code == 200, (
        "Authenticated user cannot access /documents"
    )

    # Logout
    logout_resp = session.get(
        _url("/logout"),
        allow_redirects=False,
        headers=headers,
        timeout=10,
    )

    assert logout_resp.status_code in (302, 303), (
        f"Logout failed unexpectedly: {logout_resp.status_code}"
    )

    # Verify session is invalidated
    after_logout = session.get(
        _url("/documents"),
        allow_redirects=False,
        headers=headers,
        timeout=10,
    )

    assert after_logout.status_code in (302, 303), (
        "Protected page still accessible after logout"
    )


def test_login_page_loads():
    """GET /login returns 200 with a login form."""
    resp = requests.get(_url("/login"), verify=False, headers=headers)
    assert resp.status_code == 200
    assert 'name="username"' in resp.text
    assert 'name="password"' in resp.text


def test_invalid_credentials_rejected():
    """POST /login with wrong password stays on login page (200 or 401)."""
    s = requests.Session()
    s.verify = False
    login_page = s.get(_url("/login"), headers=headers)
    csrf = _csrf_token(login_page.text)
    resp = s.post(
        _url("/login"),
        data={"username": "alice", "password": "wrongpassword", "csrf_token": csrf},
        allow_redirects=True,
        headers=headers,
    )
    assert resp.status_code in (200, 401)
    assert "Invalid credentials" in resp.text


def test_session_cookie_flags():
    """Session cookie returned after login must carry HttpOnly, Secure and SameSite=Strict."""
    s = requests.Session()
    s.verify = False
    login_page = s.get(_url("/login"), headers=headers)
    csrf = _csrf_token(login_page.text)
    resp = s.post(
        _url("/login"),
        data={"username": "alice", "password": "tth1mJj5?£58", "csrf_token": csrf},
        allow_redirects=False,
        headers=headers,
    )
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=Strict" in set_cookie


def test_tampered_cookie_rejected():
    """A forged session cookie must redirect to /login."""
    resp = requests.get(
        _url("/documents"),
        cookies={"session": "forged.invalid.cookie"},
        verify=False,
        allow_redirects=False,
        headers=headers,
    )
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", "")


def test_disabled_account_cannot_login():
    """Admin disables bob; login as bob is rejected; bob is re-enabled."""
    admin = _login_as("admin", "L|fP1D%327mB")

    # Discover bob's user ID via the document users endpoint
    users_resp = admin.get(_url("/documents/users"), headers=headers)
    bob_id = next(u["id"] for u in users_resp.json() if u["username"] == "bob")

    # Disable bob (need fresh CSRF from admin page)
    admin_page = admin.get(_url("/admin/users"), headers=headers)
    csrf = _csrf_token(admin_page.text)
    admin.post(_url(f"/admin/users/{bob_id}/disable"), data={"csrf_token": csrf}, headers=headers)

    try:
        s = requests.Session()
        s.verify = False
        login_page = s.get(_url("/login"), headers=headers)
        csrf = _csrf_token(login_page.text)
        resp = s.post(
            _url("/login"),
            data={"username": "bob", "password": "De586:Iq6}?!", "csrf_token": csrf},
            allow_redirects=True,
            headers=headers,
        )
        assert resp.status_code in (403, 200)
        assert "Account is disabled" in resp.text
    finally:
        admin_page = admin.get(_url("/admin/users"), headers=headers)
        csrf = _csrf_token(admin_page.text)
        admin.post(_url(f"/admin/users/{bob_id}/enable"), data={"csrf_token": csrf}, headers=headers)
