"""
Dynamic integration tests for rate limiting (SR-07 / AD-07b).
Run against a live deployed instance at https://localhost:443.
"""
import io
import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

_PDF_MAGIC = b"%PDF-1.4\n"


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
    login_page = s.get(_url("/login"))
    csrf = _csrf_token(login_page.text)
    s.post(
        _url("/login"),
        data={"username": username, "password": password, "csrf_token": csrf},
        allow_redirects=True,
    )
    return s


def test_login_rate_limit_triggers_429():
    """Rapid-fire POST /login (bad creds) must eventually return 429."""
    s = requests.Session()
    s.verify = False
    status_codes = []
    # nginx: login_limit rate=10r/m burst=15 nodelay → need >16 requests to trigger 429
    for _ in range(20):
        resp = s.post(
            _url("/login"),
            data={"username": "nobody", "password": "wrong"},
            allow_redirects=False,
        )
        status_codes.append(resp.status_code)
        if resp.status_code == 429:
            break
    assert 429 in status_codes, (
        f"Expected 429 from login rate limit, got codes: {status_codes}"
    )


def test_upload_rate_limit_triggers_429():
    """Rapid-fire POST /documents/upload must eventually return 429."""
    s = _login_as("alice", "tth1mJj5?£58")
    # Fetch CSRF once; it stays valid for the whole session
    csrf = _csrf_token(s.get(_url("/documents")).text)
    status_codes = []
    # Upload limit is 5/min per user; fire up to 8 to guarantee hitting it
    for _ in range(8):
        resp = s.post(
            _url("/documents/upload"),
            data={"title": "RateLimitProbe", "csrf_token": csrf},
            files={"document": ("probe.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
            allow_redirects=False,
        )
        status_codes.append(resp.status_code)
        if resp.status_code == 429:
            break
    assert 429 in status_codes, (
        f"Expected 429 from upload rate limit, got codes: {status_codes}"
    )
