import pytest
import time
from unittest.mock import patch

from app.app import create_app

app = create_app()
app.config.update({
    "TESTING": True,
    "SESSION_COOKIE_SECURE": False,
})
app.secret_key = "super-secret-test-key"

@patch("app.routes.users.users.get_all_users")
@patch("app.components.dal.users.get_user_by_id")
def test_list_users_success_as_admin(mock_get_user_by_id, mock_get_all_users):
    """Test that an admin gets a sanitized list of users."""
    client = app.test_client()

    # Mock the DB user lookup done by the authentication/RBAC decorators
    mock_get_user_by_id.return_value = {"id": 1, "username": "admin", "is_disabled": False}

    # Mock the DAL response, mimicking extra fields that should be filtered out
    mock_get_all_users.return_value = [
        {"id": 1, "username": "admin", "password_hash": "hash1", "is_disabled": False},
        {"id": 2, "username": "bob", "password_hash": "hash2", "is_disabled": False}
    ]

    # Simulate an authenticated admin session
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = True
        sess["last_active"] = time.time()

    response = client.get("/users")
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Assert we only get the id and username keys, as enforced by the route logic
    assert len(data) == 2
    assert data[0] == {"id": 1, "username": "admin"}
    assert data[1] == {"id": 2, "username": "bob"}
    
    mock_get_all_users.assert_called_once()

@patch("app.routes.users.users.get_all_users")
@patch("app.components.dal.users.get_user_by_id")
def test_list_users_forbidden_for_non_admin(mock_get_user_by_id, mock_get_all_users):
    """Test that a non-admin user cannot access the route."""
    client = app.test_client()

    # Mock the DB user lookup done by the authentication/RBAC decorators
    mock_get_user_by_id.return_value = {"id": 2, "username": "bob", "is_disabled": False}

    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["is_admin"] = False
        sess["last_active"] = time.time()

    response = client.get("/users")
    
    # Depending on the decorator's behavior, it might return 403 Forbidden or 302 Redirect
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    mock_get_all_users.assert_not_called()