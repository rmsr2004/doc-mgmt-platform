# tests/dynamic_tests/test_auth_decorators.py
"""
Tests for SR-13: Session validation on every protected request.
Dynamic tests — run against a live deployed API instance.

Relocated from test_sr-13_auth.py.
"""
import re
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_URL = os.environ.get("BASE_URL", "https://localhost")

PROTECTED_ENDPOINTS = [
    ("POST", "/documents/upload"),
    ("GET",  "/documents"),
    ("GET",  "/documents/1"),
]

class TestSR13:
    def test_missing_session_redirects_to_login(self):
        """SR-13: request with no session must redirect to login."""
        for method, path in PROTECTED_ENDPOINTS:
            resp = requests.request(
                method,
                f"{BASE_URL}{path}",
                verify=False,
                allow_redirects=False,
            )
            assert resp.status_code == 302, (
                f"{method} {path} returned {resp.status_code}, expected 302"
            )
            assert "/login" in resp.headers.get("Location", ""), (
                f"{method} {path} redirect location does not contain /login"
            )

    def test_tampered_session_redirects_to_login(self):
        """SR-13: request with a tampered session cookie must redirect to login."""
        for method, path in PROTECTED_ENDPOINTS:
            resp = requests.request(
                method,
                f"{BASE_URL}{path}",
                cookies={"session": "invalid.tampered.cookie"},
                verify=False,
                allow_redirects=False,
            )
            assert resp.status_code == 302, (
                f"{method} {path} returned {resp.status_code}, expected 302"
            )
            assert "/login" in resp.headers.get("Location", "")

    def test_valid_session_is_not_redirected(self):
        """SR-13: valid authenticated session must not be redirected to login."""
        s = requests.Session()
        s.verify = False

        resp = s.get(f"{BASE_URL}/login")
        match = re.search(
            r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
            resp.text,
        )
        token = match.group(1) if match else ""

        s.post(f"{BASE_URL}/login", data={
            "username": "admin",
            "password": "L|fP1D%327mB",
            "csrf_token": token,
        }, allow_redirects=False)

        resp = s.get(f"{BASE_URL}/documents/upload", allow_redirects=False)
        assert resp.status_code != 302 or "/login" not in resp.headers.get("Location", "")
