import time
from unittest.mock import patch

from app.app import create_app
from app.shared.result.Result import Result

app = create_app()
app.config.update({
    "TESTING": True,
    "SESSION_COOKIE_SECURE": False,
})

VALID_USER = {"id": 2, "username": "alice", "is_disabled": False}
DISABLED_USER = {"id": 2, "username": "alice", "is_disabled": True}
ADMIN_USER = {"id": 1, "username": "admin", "is_disabled": False}


def _set_session(client, *, user_id, is_admin=False, last_active=None):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["is_admin"] = is_admin
        sess["csrf_token"] = "test-csrf-token"
        if last_active is not None:
            sess["last_active"] = last_active


def test_login_required_no_session_redirects():
    client = app.test_client()
    with patch("app.components.dal.users.get_user_by_id") as mock_get_user:
        response = client.get("/documents")
        mock_get_user.assert_not_called()
    assert response.status_code == 302
    assert "/login" in response.location


def test_login_required_expired_session_redirects():
    client = app.test_client()
    _set_session(client, user_id=2, last_active=time.time() - 9999)
    with patch("app.components.dal.users.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = VALID_USER
        response = client.get("/documents")
    assert response.status_code == 302
    assert "/login" in response.location


def test_login_required_disabled_user_redirects():
    client = app.test_client()
    _set_session(client, user_id=2, last_active=time.time())
    with patch("app.components.dal.users.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = DISABLED_USER
        response = client.get("/documents")
    assert response.status_code == 302
    assert "/login" in response.location


@patch("app.components.dal.documents.get_shared_documents_for_user", return_value=[])
@patch("app.components.dal.documents.get_documents_for_user", return_value=[])
@patch("app.components.dal.users.get_user_by_id")
def test_login_required_valid_session_passes(mock_get_user, _mock_docs, _mock_shared):
    client = app.test_client()
    mock_get_user.return_value = VALID_USER
    _set_session(client, user_id=2, last_active=time.time())
    response = client.get("/documents")
    assert response.status_code == 200


@patch("app.components.dal.documents.get_shared_documents_for_user", return_value=[])
@patch("app.components.dal.documents.get_documents_for_user", return_value=[])
@patch("app.components.dal.users.get_user_by_id")
def test_login_required_refreshes_last_active(mock_get_user, _mock_docs, _mock_shared):
    client = app.test_client()
    mock_get_user.return_value = VALID_USER
    old_last_active = time.time() - 60
    _set_session(client, user_id=2, last_active=old_last_active)
    client.get("/documents")
    with client.session_transaction() as sess:
        assert sess["last_active"] > old_last_active


@patch("app.components.dal.documents.get_shared_documents_for_user", return_value=[])
@patch("app.components.dal.documents.get_documents_for_user", return_value=[])
@patch("app.components.dal.users.get_user_by_id")
def test_login_required_sets_no_cache_headers(mock_get_user, _mock_docs, _mock_shared):
    client = app.test_client()
    mock_get_user.return_value = VALID_USER
    _set_session(client, user_id=2, last_active=time.time())
    response = client.get("/documents")
    cache_control = response.headers.get("Cache-Control", "")
    assert "no-cache" in cache_control
    assert "no-store" in cache_control


def test_admin_required_non_admin_redirects():
    client = app.test_client()
    _set_session(client, user_id=2, is_admin=False, last_active=time.time())
    with patch("app.components.dal.users.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = VALID_USER
        response = client.get("/admin/users")
    assert response.status_code == 302
    assert "/login" not in response.location


@patch("app.components.admin_service.service.get_all_users")
@patch("app.components.dal.users.get_user_by_id")
def test_admin_required_admin_passes(mock_get_user, mock_get_all_users):
    client = app.test_client()
    mock_get_user.return_value = ADMIN_USER
    mock_get_all_users.return_value = Result.ok([])
    _set_session(client, user_id=1, is_admin=True, last_active=time.time())
    response = client.get("/admin/users")
    assert response.status_code == 200
