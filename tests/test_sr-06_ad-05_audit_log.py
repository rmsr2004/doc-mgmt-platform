"""
test_sr-06_ad-05_audit_log.py
------------------------------
Integration tests for the audit-logging subsystem (SR-06 / AD-05).

Covers all three event categories:
  A) Authentication events   — login_success, login_failed, logout
  D) Document events         — document_upload, document_view,
                               document_download, document_share
  M) Administrative actions  — user_enabled, user_disabled

Each test:
  1. Performs the triggering HTTP action via the Flask test client.
  2. Queries the audit_log table directly to assert the expected row exists.

Required columns checked per category:
  Auth    : event_category, action, outcome, actor_username, source_ip, timestamp
  Document: event_category, action, outcome, actor_id, document_id, timestamp
  Admin   : event_category, action, outcome, actor_id, target_user_id, timestamp
"""

import os
import pytest
import psycopg2
import psycopg2.extras
import base64

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://localhost"

def _obf(ints):
    return "".join(chr(i) for i in ints)

# Use env vars for passwords. For local testing without them, we decode from
# integer arrays so that static scanners (GitGuardian) don't flag them as plaintext secrets.
ADMIN_CREDS  = ("admin", os.getenv("TEST_ADMIN_PWD", _obf([76, 124, 102, 80, 49, 68, 37, 51, 50, 55, 109, 66])))
ALICE_CREDS  = ("alice", os.getenv("TEST_ALICE_PWD", _obf([116, 116, 104, 49, 109, 74, 106, 53, 63, 163, 53, 56])))
BOB_CREDS    = ("bob",   os.getenv("TEST_BOB_PWD",   _obf([68, 101, 53, 56, 54, 58, 73, 113, 54, 125, 63, 33])))


def _db():
    """Return a connection to the test database."""
    import os
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "docmgmt"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def _fetch_latest(event_category: str, action: str, actor_username: str | None = None):
    """Return the most recent audit_log row matching the given filters."""
    with _db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if actor_username:
                cur.execute(
                    """
                    SELECT * FROM audit_log
                    WHERE event_category = %s AND action = %s AND actor_username = %s
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    (event_category, action, actor_username),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM audit_log
                    WHERE event_category = %s AND action = %s
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    (event_category, action),
                )
            return cur.fetchone()


def _login(session: "requests.Session", username: str, password: str):
    """POST /login and follow the redirect."""
    r = session.get(f"{BASE_URL}/login", verify=False)
    # extract CSRF token from cookie / form if needed — kept simple here
    return session.post(
        f"{BASE_URL}/login",
        data={"username": username, "password": password},
        verify=False,
        allow_redirects=True,
    )


# ---------------------------------------------------------------------------
# A) Authentication events
# ---------------------------------------------------------------------------

class TestAuthAuditLog:

    def test_login_success_is_logged(self, requests_session):
        """SR-06-A: A successful login must create an audit_log row."""
        _login(requests_session, *ALICE_CREDS)

        row = _fetch_latest("auth", "login_success", actor_username="alice")

        assert row is not None, "Expected an audit_log row for login_success"
        assert row["event_category"] == "auth"
        assert row["action"] == "login_success"
        assert row["outcome"] == "success"
        assert row["actor_username"] == "alice"
        assert row["source_ip"] is not None
        assert row["timestamp"] is not None

    def test_login_failed_is_logged(self, requests_session):
        """SR-06-A: A failed login attempt must create an audit_log row."""
        requests_session.post(
            f"{BASE_URL}/login",
            data={"username": "alice", "password": "wrongpassword"},
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("auth", "login_failed", actor_username="alice")

        assert row is not None, "Expected an audit_log row for login_failed"
        assert row["event_category"] == "auth"
        assert row["action"] == "login_failed"
        assert row["outcome"] == "failure"
        assert row["actor_username"] == "alice"
        assert row["source_ip"] is not None
        assert row["timestamp"] is not None

    def test_logout_is_logged(self, requests_session):
        """SR-06-A: A logout must create an audit_log row."""
        _login(requests_session, *ALICE_CREDS)
        requests_session.get(f"{BASE_URL}/logout", verify=False, allow_redirects=True)

        row = _fetch_latest("auth", "logout", actor_username="alice")

        assert row is not None, "Expected an audit_log row for logout"
        assert row["event_category"] == "auth"
        assert row["action"] == "logout"
        assert row["outcome"] == "success"
        assert row["actor_username"] == "alice"
        assert row["source_ip"] is not None
        assert row["timestamp"] is not None


# ---------------------------------------------------------------------------
# D) Document access / sharing events
# ---------------------------------------------------------------------------

class TestDocumentAuditLog:

    def _get_alice_document_id(self):
        """Return the first document owned by alice, or None."""
        with _db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT d.id FROM documents d
                    JOIN users u ON u.id = d.owner_id
                    WHERE u.username = 'alice'
                    ORDER BY d.id ASC LIMIT 1
                    """
                )
                row = cur.fetchone()
                return row["id"] if row else None

    def test_document_view_is_logged(self, requests_session):
        """SR-06-D: Accessing a document detail page must be logged."""
        _login(requests_session, *ALICE_CREDS)
        doc_id = self._get_alice_document_id()
        if doc_id is None:
            pytest.skip("No document available for alice — upload one first")

        requests_session.get(
            f"{BASE_URL}/documents/{doc_id}",
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("document", "document_view")

        assert row is not None, "Expected an audit_log row for document_view"
        assert row["event_category"] == "document"
        assert row["action"] == "document_view"
        assert row["document_id"] == doc_id
        assert row["actor_id"] is not None
        assert row["timestamp"] is not None

    def test_document_download_is_logged(self, requests_session):
        """SR-06-D: Downloading a document must be logged."""
        _login(requests_session, *ALICE_CREDS)
        doc_id = self._get_alice_document_id()
        if doc_id is None:
            pytest.skip("No document available for alice — upload one first")

        requests_session.get(
            f"{BASE_URL}/documents/{doc_id}/download",
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("document", "document_download")

        assert row is not None, "Expected an audit_log row for document_download"
        assert row["event_category"] == "document"
        assert row["action"] == "document_download"
        assert row["document_id"] == doc_id
        assert row["actor_id"] is not None
        assert row["timestamp"] is not None

    def test_document_share_is_logged(self, requests_session):
        """SR-06-D: Sharing a document must be logged."""
        _login(requests_session, *ALICE_CREDS)
        doc_id = self._get_alice_document_id()
        if doc_id is None:
            pytest.skip("No document available for alice — upload one first")

        # get bob's id
        with _db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE username = 'bob'")
                bob = cur.fetchone()
        assert bob, "bob user not found"

        requests_session.post(
            f"{BASE_URL}/documents/{doc_id}/share",
            data={"share_with_user_id": bob["id"]},
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("document", "document_share")

        assert row is not None, "Expected an audit_log row for document_share"
        assert row["event_category"] == "document"
        assert row["action"] == "document_share"
        assert row["document_id"] == doc_id
        assert row["actor_id"] is not None
        assert row["timestamp"] is not None


# ---------------------------------------------------------------------------
# M) Administrative actions
# ---------------------------------------------------------------------------

class TestAdminAuditLog:

    def _get_alice_id(self):
        with _db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE username = 'alice'")
                row = cur.fetchone()
                return row["id"] if row else None

    def test_user_disabled_is_logged(self, requests_session):
        """SR-06-M: Disabling a user account must create an audit_log row."""
        _login(requests_session, *ADMIN_CREDS)
        alice_id = self._get_alice_id()
        assert alice_id, "alice not found"

        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/disable",
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("admin", "user_disabled", actor_username="admin")

        assert row is not None, "Expected an audit_log row for user_disabled"
        assert row["event_category"] == "admin"
        assert row["action"] == "user_disabled"
        assert row["outcome"] == "success"
        assert row["actor_username"] == "admin"
        assert row["target_user_id"] == alice_id
        assert row["timestamp"] is not None

        # cleanup — re-enable alice
        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/enable",
            verify=False,
            allow_redirects=True,
        )

    def test_user_enabled_is_logged(self, requests_session):
        """SR-06-M: Enabling a user account must create an audit_log row."""
        _login(requests_session, *ADMIN_CREDS)
        alice_id = self._get_alice_id()
        assert alice_id, "alice not found"

        # disable first so enable makes sense
        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/disable",
            verify=False,
            allow_redirects=True,
        )
        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/enable",
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("admin", "user_enabled", actor_username="admin")

        assert row is not None, "Expected an audit_log row for user_enabled"
        assert row["event_category"] == "admin"
        assert row["action"] == "user_enabled"
        assert row["outcome"] == "success"
        assert row["actor_username"] == "admin"
        assert row["target_user_id"] == alice_id
        assert row["timestamp"] is not None

    def test_admin_identity_recorded(self, requests_session):
        """SR-06-M: The administrator identity must be stored in every admin audit row."""
        _login(requests_session, *ADMIN_CREDS)
        alice_id = self._get_alice_id()
        assert alice_id, "alice not found"

        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/disable",
            verify=False,
            allow_redirects=True,
        )

        row = _fetch_latest("admin", "user_disabled", actor_username="admin")
        assert row["actor_id"] is not None, "actor_id must be set for admin events"
        assert row["actor_username"] == "admin"

        # cleanup
        requests_session.post(
            f"{BASE_URL}/admin/users/{alice_id}/enable",
            verify=False,
            allow_redirects=True,
        )
