# tests/dynamic_tests/test_health_and_index.py
"""
Tests for §11.2: Health & Index Routes.
Dynamic tests — run against a live deployed API instance.

Done tests sourced from test_smoke.py.
"""
import os
import time
import re
import requests

from .headers import NO_RATE_LIMIT_HEADERS as headers

BASE_URL = os.environ.get("BASE_URL", "https://localhost:443")


def wait_for_service(url: str, timeout: int = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, verify=False, timeout=2, headers=headers)
            if response.ok:
                return response
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service not available at {url}")

def login(username, password):
    """Helper to establish an authenticated session with a CSRF token."""
    session = requests.Session()
    session.verify = False
    
    resp = session.get(f"{BASE_URL}/login", headers=headers)
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
        allow_redirects=False,
        headers=headers
    )
    return session

def test_health_endpoint():
    response = wait_for_service(f"{BASE_URL}/health")
    assert response.json()["status"] == "ok"


def test_index_unauthenticated_redirects_to_login():
    response = requests.get(f"{BASE_URL}/", verify=False, allow_redirects=False, headers=headers)
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")

def test_index_authenticated_redirects_to_documents():
    session = login("alice", "tth1mJj5?£58")
    response = session.get(f"{BASE_URL}/", allow_redirects=False, headers=headers)
    
    assert response.status_code == 302
    assert "/documents" in response.headers.get("Location", "")