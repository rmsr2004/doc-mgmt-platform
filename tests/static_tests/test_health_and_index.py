from unittest.mock import patch, MagicMock

from app.app import create_app


def test_health_returns_ok():
    app = create_app()
    client = app.test_client()

    with patch("app.routes.health.get_db") as mock_db:
        mock_db.return_value = MagicMock()

        response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_health_db_failure_returns_error():
    app = create_app()
    client = app.test_client()

    with patch("app.routes.health.get_db") as mock_db:
        mock_db.side_effect = Exception("DB failure")

        response = client.get("/health")

    assert response.status_code == 500
    data = response.get_json()
    assert data["status"] == "error"


def test_index_authenticated_redirects_to_documents():
    app = create_app()
    client = app.test_client()

    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.get("/")

    assert response.status_code == 302
    assert "/documents" in response.location


def test_index_unauthenticated_redirects_to_login():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.location