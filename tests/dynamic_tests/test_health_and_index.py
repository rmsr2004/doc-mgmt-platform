# tests/dynamic_tests/test_health_and_index.py
"""
Tests for §11.2: Health & Index Routes.
Dynamic tests — run against a live deployed API instance.

Done tests sourced from test_smoke.py.
"""
import os
import time

import requests


BASE_URL = os.environ.get("BASE_URL", "https://localhost:443")


def wait_for_service(url: str, timeout: int = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, verify=False, timeout=2)
            if response.ok:
                return response
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service not available at {url}")


def test_health_endpoint():
    response = wait_for_service(f"{BASE_URL}/health")
    assert response.json()["status"] == "ok"
