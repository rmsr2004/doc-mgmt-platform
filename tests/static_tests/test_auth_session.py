import re
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest

from app.app import create_app
from app.components.auth_session.auth_rate_limiter import init_auth_rate_limiter, limiter as _auth_limiter

from app.app import create_app
from app.components.auth_session.auth_rate_limiter import init_auth_rate_limiter

app = create_app()
app.config.update({
    "TESTING": True,
    "SESSION_COOKIE_SECURE": False,
    "RATELIMIT_ENABLED": False,
})
init_auth_rate_limiter(app)  # bind limiter to app so RATELIMIT_ENABLED=False is respected


@pytest.fixture(autouse=True)
def _disable_rate_limiter():
    # Other test modules collected later call create_app(), which resets
    # auth_limiter.enabled back to True via the shared singleton. This fixture
    # guarantees the limiter stays off for every test in this module regardless
    # of collection order.
    _auth_limiter.enabled = False
    yield
    _auth_limiter.enabled = True

ALICE = {"id": 2, "username": "alice", "password": "tth1mJj5?£58",
         "is_disabled": False, "locked_until": None}
ADMIN = {"id": 1, "username": "admin", "password": "L|fP1D%327mB",
         "is_disabled": False, "locked_until": None}
DISABLED = {"id": 3, "username": "bob", "password": "De586:Iq6}?!",
            "is_disabled": True, "locked_until": None}
LOCKED = {"id": 4, "username": "locked_user", "password": "pw",
          "is_disabled": False,
          "locked_until": datetime.now(timezone.utc) + timedelta(minutes=10)}

_PATCH_GET_USER = "app.components.dal.users.get_user_by_username"
_PATCH_RESET    = "app.components.dal.users.reset_failed_attempts"
_PATCH_INC      = "app.components.dal.users.increment_failed_attempts"
_PATCH_LOG      = "app.components.auth_session.routes.log_auth_event"


def _csrf_token(html: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html
    )
    return match.group(1) if match else ""


def _do_login(client, username, password):
    login_page = client.get("/login")
    csrf = _csrf_token(login_page.data.decode())
    return client.post("/login", data={"username": username, "password": password,
                                       "csrf_token": csrf})


def test_login_get_renders_form():
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200
    html = response.data.decode()
    assert 'name="username"' in html
    assert 'name="password"' in html


def test_login_valid_credentials():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "tth1mJj5?£58")
    assert response.status_code == 302


def test_login_invalid_password():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_INC), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "wrongpassword")
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data


def test_login_nonexistent_user():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=None), patch(_PATCH_LOG):
        response = _do_login(client, "nobody", "pw")
    assert response.status_code == 401


def test_login_disabled_account():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=DISABLED), patch(_PATCH_LOG):
        response = _do_login(client, "bob", "De586:Iq6}?!")
    assert response.status_code == 403
    assert b"Account is disabled" in response.data


def test_login_locked_account():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=LOCKED), patch(_PATCH_LOG):
        response = _do_login(client, "locked_user", "pw")
    assert response.status_code == 403
    assert b"Account locked" in response.data


def test_login_sets_session_keys():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        _do_login(client, "alice", "tth1mJj5?£58")
    with client.session_transaction() as sess:
        assert sess["user_id"] == ALICE["id"]
        assert sess["username"] == "alice"
        assert sess["is_admin"] is False


def test_login_admin_redirects_to_admin_page():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ADMIN), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "admin", "L|fP1D%327mB")
    assert response.status_code == 302
    assert "/admin" in response.location


def test_login_regular_user_redirects_to_documents():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "tth1mJj5?£58")
    assert response.status_code == 302
    assert "/documents" in response.location


def test_logout_clears_session():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["is_admin"] = False
    with patch(_PATCH_LOG):
        response = client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.location
    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "username" not in sess


def test_logout_rotates_csrf_token():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["is_admin"] = False
        sess["csrf_token"] = "known-token-before-logout"
    with patch(_PATCH_LOG):
        client.get("/logout")
    login_page = client.get("/login")
    new_token = _csrf_token(login_page.data.decode())
    assert new_token != "known-token-before-logout"
    assert new_token != ""


def test_session_cookie_httponly():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "tth1mJj5?£58")
    set_cookie = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in set_cookie


def test_session_cookie_samesite_strict():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "tth1mJj5?£58")
    set_cookie = response.headers.get("Set-Cookie", "")
    assert "SameSite=Strict" in set_cookie


def test_session_cookie_secure():
    # Use a fresh app that preserves the production SESSION_COOKIE_SECURE=True setting
    secure_app = create_app()
    secure_app.config.update({"TESTING": True, "RATELIMIT_ENABLED": False})
    client = secure_app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET), patch(_PATCH_LOG):
        response = _do_login(client, "alice", "tth1mJj5?£58")
    set_cookie = response.headers.get("Set-Cookie", "")
    assert "Secure" in set_cookie


def test_failed_login_increments_attempts():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_INC) as mock_inc, patch(_PATCH_LOG):
        _do_login(client, "alice", "wrongpassword")
    mock_inc.assert_called_once_with("alice")


def test_successful_login_resets_attempts():
    client = app.test_client()
    with patch(_PATCH_GET_USER, return_value=ALICE), \
         patch(_PATCH_RESET) as mock_reset, patch(_PATCH_LOG):
        _do_login(client, "alice", "tth1mJj5?£58")
    mock_reset.assert_called_once_with("alice")
