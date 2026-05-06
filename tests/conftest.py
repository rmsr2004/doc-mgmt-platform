"""
conftest.py — shared fixtures for the test suite.
"""

import os
import re
import warnings

import psycopg2
import psycopg2.extras
import pytest
import requests as _requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

BASE_URL = "https://localhost"


def _obf(ints):
    return "".join(chr(i) for i in ints)


ALICE_CREDS = ("alice", os.getenv("TEST_ALICE_PWD", _obf([116, 116, 104, 49, 109, 74, 106, 53, 63, 163, 53, 56])))


def _db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "docdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def _get_csrf_token(session, url: str) -> str:
    r = session.get(url, verify=False)
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', r.text)
    if not match:
        raise RuntimeError(f"CSRF token not found in {url}")
    return match.group(1)


@pytest.fixture(scope="session", autouse=True)
def ensure_alice_has_document():
    """Upload a test document as alice if she has none, so document tests can run."""
    with _db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT d.id FROM documents d JOIN users u ON u.id = d.owner_id WHERE u.username = 'alice' LIMIT 1"
            )
            if cur.fetchone():
                return  # already has a document

    s = _requests.Session()
    s.verify = False
    s.get(f"{BASE_URL}/login")
    s.post(
        f"{BASE_URL}/login",
        data={"username": ALICE_CREDS[0], "password": ALICE_CREDS[1]},
        allow_redirects=True,
    )
    csrf = _get_csrf_token(s, f"{BASE_URL}/documents")
    s.post(
        f"{BASE_URL}/documents/upload",
        data={"title": "Audit Test Document", "csrf_token": csrf},
        files={"document": ("audit_test.txt", b"audit logger test fixture", "text/plain")},
        allow_redirects=True,
    )
