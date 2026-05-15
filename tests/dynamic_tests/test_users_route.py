import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.environ.get("BASE_URL", "https://localhost")

def login(username, password):
    """Helper to establish an authenticated session with a CSRF token."""
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
    return session

def test_unauthenticated_user_cannot_access_users():
    """Test that a missing session redirects to login or denies access."""
    response = requests.get(f"{BASE_URL}/documents/users", verify=False, allow_redirects=False)
    assert response.status_code in (302, 401, 403)

def test_non_admin_can_access_users():
    """Test that an authenticated user without admin privileges can access the route."""
    # Using known non-admin credentials from the test suite context
    session = login("alice", "tth1mJj5?£58")
    response = session.get(f"{BASE_URL}/documents/users", allow_redirects=False)
    assert response.status_code == 200
