import os
import re
import warnings

import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")
TEST_USERNAME = "alice"
TEST_PASSWORD = "tth1mJj5?£58"


@pytest.fixture
def session():
    client = requests.Session()
    client.verify = False
    return client


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _extract_csrf_token(html: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        html,
    )
    assert match is not None, "csrf_token hidden field not found"
    return match.group(1)


def _login(session: requests.Session) -> str:
    login_page = session.get(_url("/login"), timeout=10)
    assert login_page.status_code == 200

    login_token = _extract_csrf_token(login_page.text)
    login_resp = session.post(
        _url("/login"),
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": login_token,
        },
        allow_redirects=False,
        timeout=10,
    )

    assert login_resp.status_code in (302, 303), (
        f"Login failed unexpectedly: {login_resp.status_code}"
    )
    assert "/documents" in login_resp.headers.get("Location", ""), (
        "Login did not redirect to the documents page"
    )

    documents_page = session.get(_url("/documents"), timeout=10)
    assert documents_page.status_code == 200

    return _extract_csrf_token(documents_page.text)


def test_dynamic_security_controls_are_enforced(session):
    upload_token = _login(session)

    documents_resp = session.get(_url("/documents"), allow_redirects=False, timeout=10)
    assert documents_resp.status_code == 200

    admin_resp = session.get(_url("/admin/users"), allow_redirects=False, timeout=10)
    assert admin_resp.status_code in (302, 303)
    assert admin_resp.headers.get("Location", "") == "/"

    invalid_upload_resp = session.post(
        _url("/documents/upload"),
        data={
            "csrf_token": upload_token,
            "title": "A" * 256,
        },
        allow_redirects=False,
        timeout=10,
    )

    assert invalid_upload_resp.status_code in (302, 303), (
        f"Invalid upload was not rejected: {invalid_upload_resp.status_code}"
    )
    assert "/documents" in invalid_upload_resp.headers.get("Location", ""), (
        "Invalid upload did not redirect back to the documents page"
    )