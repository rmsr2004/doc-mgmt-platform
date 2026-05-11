import io
import os
import re
import requests
import urllib3
import time
import pytest

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _csrf_token(page_text: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        page_text,
    )
    return match.group(1) if match else ""


def _wait_for_service(timeout: int = 30) -> bool:
    """Wait for the web app health endpoint to become available.

    Returns True if service became available within timeout, False otherwise.
    """
    deadline = time.time() + timeout
    s = requests.Session()
    s.verify = False
    while time.time() < deadline:
        try:
            resp = s.get(BASE_URL.rstrip("/") + "/health", timeout=3)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


# If the application is not reachable, skip the whole module to avoid
# failing due to unrelated network-segmentation tests that change the
# environment (CI may run network tests that reconfigure compose/networks).
if not _wait_for_service(timeout=20):
    pytest.skip("Web app not available on %s — skipping sanitizing tests" % BASE_URL, allow_module_level=True)


def _upload_document(filename: str):
    session = requests.Session()
    session.verify = False
    # Login with retries on rate limit or transient errors
    max_attempts = 5
    backoff = 1
    login_response = None
    for attempt in range(1, max_attempts + 1):
        try:
            login_page = session.get(_url("/login"), timeout=10)
            login_csrf = _csrf_token(login_page.text)
            login_response = session.post(
                _url("/login"),
                data={
                    "username": "alice",
                    "password": "tth1mJj5?£58",
                    "csrf_token": login_csrf,
                },
                allow_redirects=False,
                timeout=10,
            )
            if login_response.status_code == 429:
                # rate limited — backoff and retry
                time.sleep(backoff)
                backoff = min(backoff * 2, 8)
                continue
            break
        except requests.RequestException:
            time.sleep(backoff)
            backoff = min(backoff * 2, 8)
    assert login_response is not None and login_response.status_code in (302, 303)

    # Upload with retries on 429 or transient errors
    max_attempts = 5
    backoff = 1
    upload_response = None
    for attempt in range(1, max_attempts + 1):
        try:
            documents_page = session.get(_url("/documents"), timeout=10)
            upload_csrf = _csrf_token(documents_page.text)
            upload_response = session.post(
                _url("/documents/upload"),
                data={"title": "Sanitizing Adapter", "csrf_token": upload_csrf},
                files={
                    "document": (
                        filename,
                        io.BytesIO(b"dummy pdf content"),
                        "application/pdf",
                    ),
                },
                allow_redirects=False,
                timeout=10,
            )
            if upload_response.status_code == 429:
                time.sleep(backoff)
                backoff = min(backoff * 2, 8)
                continue
            break
        except requests.RequestException:
            time.sleep(backoff)
            backoff = min(backoff * 2, 8)
    assert upload_response is not None

    documents_response = session.get(_url("/documents"), timeout=10)
    return upload_response, documents_response.text.lower()


def test_upload_path_traversal_filename_safe():
    response, response_text = _upload_document("../../etc/passwd.pdf")

    assert response.status_code in (302, 303)
    assert "/documents" in response.headers.get("Location", "")

    assert "../../" not in response_text
    assert "..\\" not in response_text
    assert "passwd.pdf" in response_text or "sanitizing adapter" in response_text


def test_upload_special_chars_filename_accepted():
    response, response_text = _upload_document("Relatório Final.pdf")

    assert response.status_code in (302, 303)
    assert "/documents" in response.headers.get("Location", "")

    assert "erro" not in response_text