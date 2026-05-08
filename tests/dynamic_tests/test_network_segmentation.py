import subprocess
import pytest
import os

PROJECT = "doc-mgmt-platform"

def nc_test(network, host, port, timeout=3):
    """
    Returns True if the connection was successfull
    Returns False if failed or timed out (connection blocked)
    """
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", f"{PROJECT}_{network}",
                "nicolaka/netshoot",
                "sh", "-c", f"nc -zv -w{timeout} {host} {port}"
            ],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def curl_test(network, url, timeout=3):
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", f"{PROJECT}_{network}",
                "nicolaka/netshoot",
                "sh", "-c", f"curl -s --max-time {timeout} {url}"
            ],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def host_nc_test(host, port, timeout=3):
    try:
        result = subprocess.run(
            ["sh", "-c", f"nc -zv -w{timeout} {host} {port}"],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


# ─────────────────────────────────────────────────────────────
# Allowed Communication
# ─────────────────────────────────────────────────────────────

class TestAllowedConnections:

    def test_nginx_to_flask(self):
        """nginx (private_flask) → Flask port 8000: MUST work."""
        assert nc_test("private_flask", "web", 8000), \
            "nginx cannot reach Flask on port 8000"

    def test_flask_to_db(self):
        """Flask (private_db) → DB port 5432: MUST work."""
        assert nc_test("private_db", "db", 5432), \
            "Flask cannot reach DB on port 5432"

    def test_host_to_nginx_80(self):
        """Host → nginx port 80: MUST work."""
        assert host_nc_test("localhost", 80), \
            "Port 80 not accessible on the host"

    def test_host_to_nginx_443(self):
        """Host → nginx port 443: MUST work."""
        assert host_nc_test("localhost", 443), \
            "Port 443 not accessible on the host"


# ─────────────────────────────────────────────────────────────
# BLOCKED Communication (segmentation violations)
# ─────────────────────────────────────────────────────────────

class TestBlockedConnections:

    def test_public_cannot_reach_flask(self):
        """public network MUST NOT reach Flask directly."""
        assert not nc_test("public", "web", 8000), \
            "VIOLATION: public network can reach Flask!"

    def test_public_cannot_reach_db(self):
        """public network MUST NOT reach DB."""
        assert not nc_test("public", "db", 5432), \
            "VIOLATION: public network can reach DB!"

    def test_flask_network_cannot_reach_db(self):
        """private_flask network MUST NOT reach DB."""
        assert not nc_test("private_flask", "db", 5432), \
            "VIOLATION: private_flask can reach DB!"

    def test_db_network_cannot_reach_nginx(self):
        """private_db network MUST NOT reach nginx."""
        assert not nc_test("private_db", "nginx-web", 443), \
            "VIOLATION: private_db can reach nginx!"

    def test_host_cannot_reach_db(self):
        """Host MUST NOT reach DB (port 5432 not exposed)."""
        assert not host_nc_test("localhost", 5432), \
            "VIOLATION: port 5432 is exposed on the host!"

    def test_host_cannot_reach_flask_directly(self):
        """Host MUST NOT reach Flask directly."""
        assert not host_nc_test("localhost", 8000), \
            "VIOLATION: Flask port 8000 is exposed on the host!"


# ─────────────────────────────────────────────────────────────
# Internet Isolation (internal: true)
# ─────────────────────────────────────────────────────────────

class TestInternetIsolation:

    def test_private_flask_no_internet(self):
        """private_flask network MUST NOT have internet access."""
        assert not curl_test("private_flask", "https://1.1.1.1"), \
            "VIOLATION: private_flask has internet access!"

    def test_private_db_no_internet(self):
        """private_db network MUST NOT have internet access."""
        assert not curl_test("private_db", "https://1.1.1.1"), \
            "VIOLATION: private_db has internet access!"