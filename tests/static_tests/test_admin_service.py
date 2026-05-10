from unittest.mock import patch

from app.app import create_app
from app.shared.result.Result import Error, Result


app = create_app()


def login_as_user(client, *, user_id, username, is_admin):
    with client.session_transaction() as session:
        session.update(
            {
                "user_id": user_id,
                "username": username,
                "is_admin": is_admin,
                "csrf_token": "test-csrf-token",
            }
        )


def login_as_admin(client):
    login_as_user(client, user_id=1, username="admin", is_admin=True)


def login_as_regular_user(client):
    login_as_user(client, user_id=2, username="alice", is_admin=False)


def get_session_flashes(client):
    with client.session_transaction() as session:
        return session.get("_flashes", [])


def test_admin_page_returns_users_list():
    client = app.test_client()

    login_as_admin(client)

    mock_users = [
        {"id": 1, "username": "admin"},
        {"id": 2, "username": "alice"},
    ]

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok(mock_users)

        response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"admin" in response.data
    assert b"alice" in response.data


def test_admin_page_non_admin_denied():
    client = app.test_client()

    login_as_regular_user(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = {"id": 2, "username": "alice", "is_disabled": False}
        response = client.get("/admin/users")

    assert response.status_code == 302
    assert "/login" in response.location or "/" in response.location


def test_admin_page_unauthenticated_denied():
    client = app.test_client()

    response = client.get("/admin/users")

    assert response.status_code == 302
    assert "/login" in response.location


def test_enable_user_success():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users, patch("app.components.admin_service.service.update_user_status") as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok([])
        mock_update.return_value = Result.ok(None)

        response = client.post(
            "/admin/users/2/enable",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"User status updated successfully." in response.data
    mock_update.assert_called_once_with(2, False)


def test_disable_user_success():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users, patch("app.components.admin_service.service.update_user_status") as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok([])
        mock_update.return_value = Result.ok(None)

        response = client.post(
            "/admin/users/2/disable",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"User status updated successfully." in response.data
    mock_update.assert_called_once_with(2, True)


def test_enable_own_account_rejected():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users, patch("app.components.admin_service.service.update_user_status") as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok([])
        response = client.post(
            "/admin/users/1/enable",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"cannot enable your own account" in response.data.lower()
    mock_update.assert_not_called()


def test_disable_own_account_rejected():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users, patch("app.components.admin_service.service.update_user_status") as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok([])
        response = client.post(
            "/admin/users/1/disable",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"cannot disable your own account" in response.data.lower()
    mock_update.assert_not_called()


def test_enable_nonexistent_user():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.update_user_status"
    ) as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_update.return_value = Result.fail(Error("User not found", 404))

        response = client.post(
            "/admin/users/999/enable",
            data={"csrf_token": "test-csrf-token"},
        )

    assert response.status_code == 404
    assert response.location.endswith("/admin/users")
    assert ("error", "User not found") in get_session_flashes(client)


def test_disable_nonexistent_user():
    client = app.test_client()

    login_as_admin(client)

    with patch("app.components.dal.users.get_user_by_id") as mock_get_user, patch(
        "app.components.admin_service.service.get_all_users"
    ) as mock_get_users, patch("app.components.admin_service.service.update_user_status") as mock_update:
        mock_get_user.return_value = {"id": 1, "username": "admin", "is_disabled": False}
        mock_get_users.return_value = Result.ok([])
        mock_update.return_value = Result.fail(Error("User not found", 404))

        response = client.post(
            "/admin/users/999/disable",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"User not found" in response.data
    mock_update.assert_called_once_with(999, True)