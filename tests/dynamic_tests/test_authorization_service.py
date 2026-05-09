import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.environ.get("BASE_URL", "https://localhost")

def login(username, password):
    """Helper to establish an authenticated session and retrieve a CSRF token."""
    session = requests.Session()
    session.verify = False
    
    resp = session.get(f"{BASE_URL}/login")
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        resp.text,
    )
    csrf_token = match.group(1) if match else ""
    
    session.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_token,
        },
        allow_redirects=False
    )
    return session, csrf_token

def test_unauthenticated_user_cannot_access_documents():
    """Test that a missing session redirects to login or denies access."""
    response = requests.get(f"{BASE_URL}/documents", verify=False, allow_redirects=False)
    assert response.status_code in (302, 401, 403)

def test_user_cannot_access_another_users_document():
    """Test that Bob cannot view or download a document he does not own or have access to."""
    bob_session, _ = login("bob", "De586:Iq6}?!")
    
    # Assuming Document 1 exists and belongs to someone else (e.g., alice or admin)
    response = bob_session.get(f"{BASE_URL}/documents/1", allow_redirects=False)
    assert response.status_code in (302, 403, 404)

    response_dl = bob_session.get(f"{BASE_URL}/documents/1/download", allow_redirects=False)
    assert response_dl.status_code in (302, 403, 404)

def test_user_cannot_share_another_users_document():
    """Test that Bob cannot share a document that he doesn't own."""
    bob_session, bob_csrf = login("bob", "De586:Iq6}?!")
    
    response = bob_session.post(
        f"{BASE_URL}/documents/1/share",
        data={"csrf_token": bob_csrf, "share_with_user_id": 1},
        allow_redirects=False
    )
    assert response.status_code in (403, 404, 302)
