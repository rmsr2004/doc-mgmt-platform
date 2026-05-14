"""
Dynamic integration tests for the Admin Service.
Run against a live deployed instance at https://localhost:443.
"""
import os
import re
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "L|fP1D%327mB"
USER_USERNAME = "alice"
USER_PASSWORD = "tth1mJj5?£58"
BOB_USERNAME = "bob"
BOB_PASSWORD = "De586:Iq6}?!"


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


def _get_user_id(admin_session: requests.Session, username: str) -> int:
    resp = admin_session.get(_url("/documents/users"))
    return next(u["id"] for u in resp.json() if u["username"] == username)


def _get_user_id_from_admin_page(admin_session: requests.Session, username: str) -> int:
    """Parse user ID from /admin/users HTML (includes the admin account)."""
    page = admin_session.get(_url("/admin/users"))
    match = re.search(
        r'<td>(\d+)</td>\s*<td>' + re.escape(username) + r'</td>',
        page.text,
    )
    if not match:
        raise ValueError(f"User '{username}' not found on admin page")
    return int(match.group(1))


def test_admin_page_loads_for_admin():
    """Admin user can GET /admin/users and receives a 200 response."""
    admin = _login_as(ADMIN_USERNAME, ADMIN_PASSWORD)
    resp = admin.get(_url("/admin/users"), timeout=10)
    assert resp.status_code == 200


def test_admin_page_denied_for_regular_user():
    """Non-admin authenticated user is redirected away from GET /admin/users."""
    user = _login_as(USER_USERNAME, USER_PASSWORD)
    resp = user.get(_url("/admin/users"), allow_redirects=False, timeout=10)
    assert resp.status_code == 302
    assert "/login" not in resp.headers.get("Location", "")


def test_disable_user_flow():
    """Admin disables a user account; that user's login attempt is then rejected."""
    admin = _login_as(ADMIN_USERNAME, ADMIN_PASSWORD)
    bob_id = _get_user_id(admin, BOB_USERNAME)

    admin_page = admin.get(_url("/admin/users"))
    csrf = _csrf_token(admin_page.text)
    admin.post(_url(f"/admin/users/{bob_id}/disable"), data={"csrf_token": csrf})

    try:
        s = requests.Session()
        s.verify = False
        login_page = s.get(_url("/login"))
        csrf = _csrf_token(login_page.text)
        resp = s.post(
            _url("/login"),
            data={"username": BOB_USERNAME, "password": BOB_PASSWORD, "csrf_token": csrf},
            allow_redirects=True,
        )
        assert resp.status_code in (200, 403)
        assert "Account is disabled" in resp.text
    finally:
        admin_page = admin.get(_url("/admin/users"))
        csrf = _csrf_token(admin_page.text)
        admin.post(_url(f"/admin/users/{bob_id}/enable"), data={"csrf_token": csrf})


def test_enable_user_flow():
    """Admin re-enables a disabled user account; that user can then log in successfully."""
    admin = _login_as(ADMIN_USERNAME, ADMIN_PASSWORD)
    bob_id = _get_user_id(admin, BOB_USERNAME)

    # Setup: disable bob first
    admin_page = admin.get(_url("/admin/users"))
    csrf = _csrf_token(admin_page.text)
    admin.post(_url(f"/admin/users/{bob_id}/disable"), data={"csrf_token": csrf})

    # Re-enable bob
    admin_page = admin.get(_url("/admin/users"))
    csrf = _csrf_token(admin_page.text)
    admin.post(_url(f"/admin/users/{bob_id}/enable"), data={"csrf_token": csrf})

    s = requests.Session()
    s.verify = False
    login_page = s.get(_url("/login"))
    csrf = _csrf_token(login_page.text)
    resp = s.post(
        _url("/login"),
        data={"username": BOB_USERNAME, "password": BOB_PASSWORD, "csrf_token": csrf},
        allow_redirects=False,
    )
    assert resp.status_code in (302, 303)


def test_admin_cannot_toggle_self():
    """Admin receives an error when attempting to disable their own account."""
    admin = _login_as(ADMIN_USERNAME, ADMIN_PASSWORD)
    admin_id = _get_user_id_from_admin_page(admin, ADMIN_USERNAME)

    admin_page = admin.get(_url("/admin/users"))
    csrf = _csrf_token(admin_page.text)
    resp = admin.post(
        _url(f"/admin/users/{admin_id}/disable"),
        data={"csrf_token": csrf},
        allow_redirects=True,
        timeout=10,
    )
    assert resp.status_code == 200
    assert "cannot disable your own account" in resp.text.lower()
