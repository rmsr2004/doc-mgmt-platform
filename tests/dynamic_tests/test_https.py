# tests/dynamic_tests/test_https.py
"""
Tests for AD-02b: HTTPS enforcement and HSTS.
Dynamic tests — run against a live deployed API instance.

Relocated from test_ad-02b_https.py.
"""
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HTTP_BASE = "http://localhost"
HTTPS_BASE = "https://localhost"

def test_http_root_redirects_to_https():
    response = requests.get(f"{HTTP_BASE}/", allow_redirects=False, timeout=5)
    assert response.status_code in (301, 308)
    assert response.headers["Location"].startswith("https://")

def test_http_health_redirects_to_https():
    response = requests.get(f"{HTTP_BASE}/health", allow_redirects=False, timeout=5)
    assert response.status_code in (301, 308)
    assert response.headers["Location"].startswith("https://")
    assert response.headers["Location"].endswith("/health")

def test_https_health_is_reachable():
    response = requests.get(f"{HTTPS_BASE}/health", verify=False, timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "error")

def test_hsts_header_present_on_https():
    response = requests.get(f"{HTTPS_BASE}/health", verify=False, timeout=5)
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=" in response.headers["Strict-Transport-Security"]

def test_http_redirect_does_not_return_plaintext_content():
    response = requests.get(f"{HTTP_BASE}/health", allow_redirects=False, timeout=5)
    assert response.status_code in (301, 308)
    assert response.text == "" or "https://" in response.headers.get("Location", "")
