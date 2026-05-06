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


def test_unauthenticated_access_denied(session):
    """Verify unauthenticated users cannot access protected pages."""
    response = session.get(_url("/documents"), allow_redirects=False, timeout=10)
    assert response.status_code in (302, 303), (
        f"Expected redirect, got {response.status_code}"
    )


def test_non_admin_cannot_access_admin(session):
    """Verify non-admin users cannot access admin area."""
    # Login as non-admin user
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
        f"Login failed: {login_resp.status_code}"
    )
    
    # Try to access admin area
    admin_resp = session.get(_url("/admin/users"), allow_redirects=False, timeout=10)
    assert admin_resp.status_code in (302, 303, 403), (
        f"Expected denial, got {admin_resp.status_code}"
    )


def test_malicious_file_rejected(session):
    """Verify malicious file uploads are rejected."""
    # Login
    session.post(
        _url("/login"),
        data={
            "username": "alice",
            "password": "tth1mJj5?£58",
        },
        allow_redirects=False,
        timeout=10,
    )
    
    # Try to upload malicious file
    upload_resp = session.post(
        _url("/documents/upload"),
        data={
            "title": "Malicious",
        },
        files={"document": ("payload.php", b"<?php echo 'pwned'; ?>")},
        allow_redirects=False,
        timeout=10,
    )
    
    assert upload_resp.status_code in (302, 303, 400, 403, 422), (
        f"Expected rejection, got {upload_resp.status_code}"
    )


def test_oversized_input_rejected(session):
    """Verify oversized input is rejected by validation."""
    # Login
    session.post(
        _url("/login"),
        data={
            "username": "alice",
            "password": "tth1mJj5?£58",
        },
        allow_redirects=False,
        timeout=10,
    )
    
    # Try to upload with oversized title
    upload_resp = session.post(
        _url("/documents/upload"),
        data={
            "title": "A" * 300,
        },
        files={"document": ("test.pdf", b"%PDF-1.4")},
        allow_redirects=False,
        timeout=10,
    )
    
    assert upload_resp.status_code in (302, 303, 400, 413, 422), (
        f"Expected rejection, got {upload_resp.status_code}"
    )
