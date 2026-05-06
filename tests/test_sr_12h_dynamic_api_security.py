import os
import re

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")


def _get_csrf_token(session: requests.Session, path: str) -> str:
    """Extract CSRF token from form page."""
    response = session.get(f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}", timeout=10)
    match = re.search(r'value=["\']([^"\']+)["\'].*csrf_token', response.text)
    return match.group(1) if match else ""


def _login(session: requests.Session, username: str, password: str) -> bool:
    """Login user and return True if successful."""
    token = _get_csrf_token(session, "/login")
    response = session.post(
        f"{BASE_URL.rstrip('/')}/login",
        data={"username": username, "password": password, "csrf_token": token},
        allow_redirects=False,
        timeout=10,
    )
    return response.status_code in (302, 303)


def test_unauthenticated_access_denied() -> None:
    """Verify unauthenticated users are redirected to login."""
    session = requests.Session()
    session.verify = False
    
    response = session.get(f"{BASE_URL}/documents", allow_redirects=False, timeout=10)
    assert response.status_code in (301, 302, 303), "Should redirect to login"
    assert "/login" in response.headers.get("Location", ""), "Should redirect to /login"


def test_non_admin_cannot_access_admin() -> None:
    """Verify non-admin users cannot access admin endpoints."""
    session = requests.Session()
    session.verify = False
    
    assert _login(session, "alice", "tth1mJj5?£58"), "Login failed"
    
    response = session.get(f"{BASE_URL}/admin/users", allow_redirects=False, timeout=10)
    assert response.status_code in (301, 302, 303), "Should reject admin access"
    assert "/" in response.headers.get("Location", ""), "Should redirect to home"


def test_invalid_file_upload_rejected() -> None:
    """Verify invalid file uploads are rejected by input validation."""
    session = requests.Session()
    session.verify = False
    
    assert _login(session, "alice", "tth1mJj5?£58"), "Login failed"
    
    token = _get_csrf_token(session, "/documents")
    response = session.post(
        f"{BASE_URL}/documents/upload",
        data={"csrf_token": token, "title": "Test"},
        files={"document": ("payload.pdf", b"<?php echo 'pwned'; ?>")},
        allow_redirects=False,
        timeout=10,
    )
    assert response.status_code in (301, 302, 303), "Should reject malicious file"


def test_oversized_title_rejected() -> None:
    """Verify oversized titles are rejected by input validation."""
    session = requests.Session()
    session.verify = False
    
    assert _login(session, "alice", "tth1mJj5?£58"), "Login failed"
    
    token = _get_csrf_token(session, "/documents")
    response = session.post(
        f"{BASE_URL}/documents/upload",
        data={"csrf_token": token, "title": "A" * 300},
        files={"document": ("test.pdf", b"%PDF-1.4")},
        allow_redirects=False,
        timeout=10,
    )
    assert response.status_code in (301, 302, 303), "Should reject oversized title"