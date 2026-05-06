import os
import re
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _session() -> requests.Session:
    session = requests.Session()
    session.verify = False
    return session


def _csrf_token(response_text: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        response_text,
    )
    return match.group(1) if match else ""


def _login(username: str, password: str) -> requests.Session:
    session = _session()

    login_page = session.get(_url("/login"), timeout=10)
    assert login_page.status_code == 200

    token = _csrf_token(login_page.text)
    assert token, "CSRF token not found on login form"

    login_response = session.post(
        _url("/login"),
        data={
            "username": username,
            "password": password,
            "csrf_token": token,
        },
        allow_redirects=False,
        timeout=10,
    )

    assert login_response.status_code in (302, 303), (
        f"Login failed unexpectedly: {login_response.status_code}"
    )

    return session


def _assert_redirects_to(response: requests.Response, expected_path: str) -> None:
    location = response.headers.get("Location", "")
    assert response.status_code in (301, 302, 303, 307, 308), (
        f"Expected redirect, got {response.status_code}"
    )
    assert urlparse(location).path == expected_path, (
        f"Redirected to {location!r}, expected path {expected_path!r}"
    )


def test_unauthenticated_access_is_redirected_to_login() -> None:
    session = _session()

    for path in ("/documents", "/admin/users"):
        response = session.get(_url(path), allow_redirects=False, timeout=10)
        _assert_redirects_to(response, "/login")


def test_non_admin_cannot_access_admin_area() -> None:
    session = _login("alice", "tth1mJj5?£58")

    response = session.get(_url("/admin/users"), allow_redirects=False, timeout=10)
    _assert_redirects_to(response, "/")


def test_malicious_upload_is_rejected_by_runtime_validation() -> None:
    session = _login("alice", "tth1mJj5?£58")

    documents_page = session.get(_url("/documents"), timeout=10)
    assert documents_page.status_code == 200

    csrf_token = _csrf_token(documents_page.text)
    assert csrf_token, "CSRF token not found on documents page"

    malicious_upload = session.post(
        _url("/documents/upload"),
        data={
            "csrf_token": csrf_token,
            "title": "Runtime security check",
        },
        files={"document": ("payload.pdf", b"<?php echo 'pwned'; ?>")},
        allow_redirects=False,
        timeout=10,
    )

    _assert_redirects_to(malicious_upload, "/documents")


def test_overlong_title_is_rejected_by_runtime_validation() -> None:
    session = _login("alice", "tth1mJj5?£58")

    documents_page = session.get(_url("/documents"), timeout=10)
    assert documents_page.status_code == 200

    csrf_token = _csrf_token(documents_page.text)
    assert csrf_token, "CSRF token not found on documents page"

    overlong_title = "A" * 256
    invalid_title_upload = session.post(
        _url("/documents/upload"),
        data={
            "csrf_token": csrf_token,
            "title": overlong_title,
        },
        files={"document": ("safe.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n")},
        allow_redirects=False,
        timeout=10,
    )

    _assert_redirects_to(invalid_title_upload, "/documents")