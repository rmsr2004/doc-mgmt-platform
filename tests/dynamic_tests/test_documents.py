import os
import re
import requests
import urllib3

# Suppress insecure request warnings for local HTTPS testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .headers import NO_RATE_LIMIT_HEADERS as headers

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

def _login_as(username, password):
    """Helper to establish an authenticated session by parsing the CSRF token."""
    session = requests.Session()
    session.verify = False
    
    # Get the login page to extract the CSRF token
    resp = session.get(f"{BASE_URL}/login", headers=headers)
    match = re.search(r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text)
    csrf_token = match.group(1) if match else ""
    
    # Perform the actual login
    session.post(
        f"{BASE_URL}/login",
        data={"username": username, "password": password, "csrf_token": csrf_token},
        allow_redirects=True,
        headers=headers
    )
    return session

def test_unauthenticated_user_cannot_access_documents():
    """Ensure unauthenticated users are blocked or redirected."""
    response = requests.get(f"{BASE_URL}/documents", verify=False, allow_redirects=False, headers=headers)
    
    # Unauthenticated should redirect to /login (302) or return Unauthorized/Forbidden
    assert response.status_code in (302, 401, 403)

def test_authenticated_user_can_access_documents():
    """Ensure a valid user can view their document list."""
    # Using Alice's credentials from the README
    session = _login_as("alice", "tth1mJj5?£58")
    response = session.get(f"{BASE_URL}/documents", headers=headers)
    
    assert response.status_code == 200

def test_user_cannot_access_non_existent_or_unowned_document():
    """Ensure users cannot access documents that don't belong to them or don't exist."""
    session = _login_as("alice", "tth1mJj5?£58")
    
    # Assuming document ID 99999 does not exist or belongs strictly to another user
    response = session.get(f"{BASE_URL}/documents/99999", allow_redirects=False, headers=headers)
    
    assert response.status_code in (302, 403, 404)

def test_malicious_document_path_rejected():
    """Test for path traversal prevention (SR-10)."""
    session = _login_as("alice", "tth1mJj5?£58")
    
    # Attempt a basic path traversal payload on the download endpoint
    response = session.get(f"{BASE_URL}/documents/..%2F..%2Fetc%2Fpasswd/download", headers=headers)
    
    assert response.status_code in (400, 403, 404)