# tests/dynamic_tests/test_auth_session.py
"""
Tests for §1.2: Authentication Session Flow.
Dynamic tests — run against a live deployed API instance.

Done tests sourced from test_delivery_auth_flow.py.
"""

import os
import requests
import pytest
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")


@pytest.fixture
def session():
    s = requests.Session()
    s.verify = False
    return s


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


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
    )

    assert login_resp.status_code in (302, 303), (
        f"Login failed unexpectedly: {login_resp.status_code}"
    )

    # Access protected page
    documents_resp = session.get(
        _url("/documents"),
        allow_redirects=False,
        timeout=10,
    )

    assert documents_resp.status_code == 200, (
        "Authenticated user cannot access /documents"
    )

    # Logout
    logout_resp = session.get(
        _url("/logout"),
        allow_redirects=False,
        timeout=10,
    )

    assert logout_resp.status_code in (302, 303), (
        f"Logout failed unexpectedly: {logout_resp.status_code}"
    )

    # Verify session is invalidated
    after_logout = session.get(
        _url("/documents"),
        allow_redirects=False,
        timeout=10,
    )

    assert after_logout.status_code in (302, 303), (
        "Protected page still accessible after logout"
    )
