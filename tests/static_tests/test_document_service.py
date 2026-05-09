import pytest
import time
from unittest.mock import patch
from io import BytesIO

from app.app import create_app

app = create_app()
app.config.update({
    "TESTING": True,
    "SESSION_COOKIE_SECURE": False,
    "WTF_CSRF_ENABLED": False,  # Commonly disabled during static tests unless testing CSRF explicitly
})
app.secret_key = "super-secret-test-key"

@patch("app.components.dal.users.get_user_by_id")
def test_unauthenticated_user_cannot_access_documents(mock_get_user_by_id):
    """Test that a user without a session is redirected to the login page."""
    client = app.test_client()

    response = client.get("/documents")
    
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    mock_get_user_by_id.assert_not_called()

@patch("app.components.dal.documents.get_shared_documents_for_user")
@patch("app.components.dal.documents.get_documents_for_user")
@patch("app.components.dal.users.get_user_by_id")
def test_authenticated_user_can_access_documents(mock_get_user_by_id, mock_get_docs, mock_get_shared):
    """Test that an authenticated user can successfully list their documents."""
    client = app.test_client()

    # Mock the DB user lookup done by the authentication/RBAC decorators
    mock_get_user_by_id.return_value = {"id": 2, "username": "alice", "is_disabled": False}
    mock_get_docs.return_value = [{"id": 1, "title": "My Plan", "filename": "plan.pdf", "owner_id": 2, "uploaded_at": "2023-10-01 12:00:00"}]
    mock_get_shared.return_value = []

    # Simulate an authenticated session
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["is_admin"] = False
        sess["last_active"] = time.time()

    response = client.get("/documents")
    
    assert response.status_code == 200
    mock_get_user_by_id.assert_called_once_with(2)

@patch("app.components.dal.documents.get_document_by_uuid")
@patch("app.components.dal.documents.upload_document")
@patch("app.components.dal.users.get_user_by_id")
def test_document_upload_success(mock_get_user_by_id, mock_upload_document, mock_get_doc_by_uuid):
    """Test file upload endpoint logic with a valid dummy file."""
    client = app.test_client()
    
    mock_get_user_by_id.return_value = {"id": 2, "username": "alice", "is_disabled": False}

    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["is_admin"] = False
        sess["last_active"] = time.time()
        sess["csrf_token"] = "dummy-csrf-token"

    # Mock successful DB insert
    mock_upload_document.return_value = 1
    mock_get_doc_by_uuid.return_value = {"id": 1}

    data = {
        "document": (BytesIO(b"%PDF-1.4 dummy pdf content"), "test_file.pdf"),
        "csrf_token": "dummy-csrf-token"
    }
    response = client.post("/documents/upload", data=data, content_type="multipart/form-data", headers={"X-CSRFToken": "dummy-csrf-token"})
    
    # Usually successful uploads will redirect back to the documents page (302) or return a 200/201 response.
    assert response.status_code in (200, 201, 302)