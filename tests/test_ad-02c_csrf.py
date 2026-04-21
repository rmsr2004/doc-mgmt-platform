# tests/test_ad02c_csrf.py
"""
Tests for AD-02c: CSRF Filter at the Single Access Point
SR-11a: SameSite=Strict on session cookie
SR-11b: Synchronizer Token Pattern on state-changing requests
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_csrf_token(client) -> str:
    """Extract the current CSRF token from the session."""
    with client.session_transaction() as sess:
        return sess.get("csrf_token", "")


def login(client, username="admin", password="L|fP1D%327mB"):
    """Log in and return the CSRF token generated for the new session."""
    client.get("/login")
    token = get_csrf_token(client)

    resp = client.post("/login", data={
        "username": username,
        "password": password,
        "csrf_token": token,
    }, follow_redirects=True)

    return resp, get_csrf_token(client)


# ---------------------------------------------------------------------------
# SR-11a — SameSite=Strict cookie attribute
# ---------------------------------------------------------------------------

class TestSR11a:
    def test_session_cookie_has_samesite_strict(self, client):
        """SR-11a: session cookie must carry SameSite=Strict."""
        resp = client.get("/login")
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in set_cookie

    def test_session_cookie_has_httponly(self, client):
        """SR-02 / SR-11a: HttpOnly flag must be set."""
        resp = client.get("/login")
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "HttpOnly" in set_cookie


# ---------------------------------------------------------------------------
# SR-11b — Synchronizer Token Pattern
# ---------------------------------------------------------------------------

class TestSR11b:
    def test_csrf_token_created_on_session_start(self, client):
        """A CSRF token must be created when a session is started."""
        client.get("/login")
        token = get_csrf_token(client)
        assert token != ""
        assert len(token) >= 32

    def test_csrf_token_rotates_on_login(self, client):
        """The CSRF token must be rotated on login (new session)."""
        client.get("/login")
        token_before = get_csrf_token(client)

        _, token_after = login(client)
        assert token_after != ""
        assert token_after != token_before

    def test_post_without_csrf_token_is_rejected(self, authenticated_client):
        """SR-11b: POST without CSRF token must return 403."""
        client, _ = authenticated_client
        resp = client.post("/documents/upload", data={})
        assert resp.status_code == 403

    def test_post_with_wrong_csrf_token_is_rejected(self, authenticated_client):
        """SR-11b: POST with incorrect CSRF token must return 403."""
        client, _ = authenticated_client
        resp = client.post("/documents/upload", data={
            "csrf_token": "totally-wrong-token",
        })
        assert resp.status_code == 403

    def test_post_with_valid_csrf_token_passes_filter(self, authenticated_client):
        """SR-11b: POST with valid CSRF token must pass the filter."""
        client, token = authenticated_client
        resp = client.post("/documents/upload", data={
            "csrf_token": token,
        })
        assert resp.status_code != 403

    def test_get_request_does_not_require_csrf(self, client):
        """Safe methods (GET) must never be blocked by the CSRF filter."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_unauthenticated_post_is_not_blocked_by_csrf(self, client):
        """
        Unauthenticated POST requests must not be blocked by the CSRF filter.
        They will be rejected by the authentication middleware instead.
        """
        resp = client.post("/documents/upload", data={})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AD-02c — Integration: CSRF filter works end-to-end
# ---------------------------------------------------------------------------

class TestAD02c:
    def test_share_document_rejected_without_csrf(self, authenticated_client):
        """AD-02c: document share without CSRF token must be rejected."""
        client, _ = authenticated_client
        resp = client.post("/documents/1/share", data={
            "reviewer_id": 2,
        })
        assert resp.status_code == 403

    def test_admin_toggle_rejected_without_csrf(self, authenticated_client):
        """AD-02c: admin action without CSRF token must be rejected."""
        client, _ = authenticated_client
        resp = client.post("/admin/users/2/toggle", data={})
        assert resp.status_code == 403

    def test_logout_rejected_without_csrf(self, authenticated_client):
        """AD-02c: logout POST without CSRF token must be rejected."""
        client, _ = authenticated_client
        resp = client.post("/logout", data={})
        assert resp.status_code == 403

    def test_full_flow_share_with_valid_csrf(self, authenticated_client):
        """
        AD-02c: full flow — login, get token, share with valid token.
        Filter must pass (actual result depends on business logic).
        """
        client, token = authenticated_client
        resp = client.post("/documents/1/share", data={
            "csrf_token": token,
            "reviewer_id": 2,
        })
        assert resp.status_code != 403