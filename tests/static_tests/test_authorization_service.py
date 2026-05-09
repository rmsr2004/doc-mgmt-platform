import pytest
from unittest.mock import patch
from flask import Flask, session

from app.shared.result.Result import Error
from app.components.authorization.service import verify_document_access, verify_if_admin


# ---------------------------------------------------------------------------
# verify_document_access Tests
# ---------------------------------------------------------------------------
class TestVerifyDocumentAccess:

    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_document_not_found(self, mock_get_owner):
        """Test access is denied with 404 when the document does not exist."""
        mock_get_owner.return_value = None
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert not result.success
        assert result.error.http_code == 404
        assert result.error.message == "Document not found"

    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_document_owner_dal_error(self, mock_get_owner):
        """Test that DAL errors are gracefully propagated back to the caller."""
        db_error = Error(message="Database timeout", http_code=500)
        mock_get_owner.return_value = db_error
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert not result.success
        assert result.error == db_error

    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_user_is_owner_access_granted(self, mock_get_owner):
        """Test access is granted if the user is the owner of the document."""
        mock_get_owner.return_value = {"owner_id": 100}
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert result.success
        assert result.value is None  # ok(None)

    @patch("app.components.authorization.service.documents.get_document_share")
    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_user_is_shared_access_granted(self, mock_get_owner, mock_get_share):
        """Test access is granted if user is not the owner but a share record exists."""
        mock_get_owner.return_value = {"owner_id": 200}  # Someone else's document
        mock_get_share.return_value = {"document_id": 1, "shared_with": 100}
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert result.success

    @patch("app.components.authorization.service.documents.get_document_share")
    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_share_dal_error(self, mock_get_owner, mock_get_share):
        """Test that DAL errors during the share check are gracefully propagated."""
        mock_get_owner.return_value = {"owner_id": 200}
        db_error = Error(message="Database timeout", http_code=500)
        mock_get_share.return_value = db_error
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert not result.success
        assert result.error == db_error

    @patch("app.components.authorization.service.documents.get_document_share")
    @patch("app.components.authorization.service.documents.get_document_owner")
    def test_user_not_owner_not_shared_access_denied(self, mock_get_owner, mock_get_share):
        """Test access is denied with 403 when user is neither owner nor shared."""
        mock_get_owner.return_value = {"owner_id": 200}
        mock_get_share.return_value = None  # No share record found
        
        result = verify_document_access(document_id=1, user_id=100)
        
        assert not result.success
        assert result.error.http_code == 403
        assert result.error.message == "You do not have permission to access this document"


# ---------------------------------------------------------------------------
# verify_if_admin Tests
# ---------------------------------------------------------------------------
class TestVerifyIfAdmin:
    
    @pytest.mark.parametrize("is_admin_val, expected", [(True, True), (False, False), (None, None)])
    def test_verify_if_admin_checks_session(self, is_admin_val, expected):
        app = Flask(__name__)
        app.secret_key = "test-secret-key"
        with app.test_request_context():
            session["is_admin"] = is_admin_val
            assert verify_if_admin(user_id=100) is expected