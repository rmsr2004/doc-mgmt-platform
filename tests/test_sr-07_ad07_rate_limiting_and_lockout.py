import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import time
from flask import Flask

from app.components.auth_session.auth_rate_limiter import limiter as auth_limiter, init_auth_rate_limiter
from app.components.upload_guard.upload_rate_limiter import limiter as upload_limiter, init_upload_rate_limiter
from app.components.auth_session.session_lifecycle import _is_account_locked, _get_remaining_minutes, _register_failed_attempt, _reset_lockout

from app.config import LOCKOUT_DURATION, LOCKOUT_THRESHOLD


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def auth_app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    flask_app.config["TESTING"] = True
    init_auth_rate_limiter(flask_app)

    @flask_app.route("/login", methods=["GET", "POST"])
    @auth_limiter.limit("10 per minute")
    def mock_login():
        return "ok", 200

    return flask_app

@pytest.fixture
def upload_app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    flask_app.config["TESTING"] = True
    init_upload_rate_limiter(flask_app)

    @flask_app.route("/documents/upload", methods=["POST"])
    @upload_limiter.limit("5 per minute")
    def mock_upload():
        return "ok", 200

    return flask_app

# ===========================================================================
# SR-07a + AD-07a — Rate limiting om login (per IP)
# ===========================================================================

class TestLoginRateLimit:
    def test_requests_within_limit_pass(self, auth_app):
        with auth_app.test_client() as c:
            for i in range(10):
                r = c.post("/login")
                assert r.status_code == 200, f"Request {i+1} devia passar"

    def test_excess_request_returns_429(self, auth_app):
        with auth_app.test_client() as c:
            for _ in range(10):
                c.post("/login")
            r = c.post("/login")
            assert r.status_code == 429

    def test_different_ips_have_independent_limits(self, auth_app):
        with auth_app.test_client() as c1:
            for _ in range(10):
                c1.post("/login", environ_base={"REMOTE_ADDR": "1.1.1.1"})
            r = c1.post("/login", environ_base={"REMOTE_ADDR": "1.1.1.1"})
            assert r.status_code == 429

        with auth_app.test_client() as c2:
            r = c2.post("/login", environ_base={"REMOTE_ADDR": "2.2.2.2"})
            assert r.status_code == 200


# ===========================================================================
# AD-07b — Rate limiting on upload (per user_id / IP)
# ===========================================================================

class TestUploadRateLimit:

    def test_requests_within_limit_pass(self, upload_app):
        with upload_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
            for i in range(5):
                r = c.post("/documents/upload")
                assert r.status_code == 200, f"Request {i+1} devia passar"

    def test_excess_request_returns_429(self, upload_app):
        with upload_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
            for _ in range(5):
                c.post("/documents/upload")
            r = c.post("/documents/upload")
            assert r.status_code == 429

    def test_different_users_have_independent_limits(self, upload_app):
        with upload_app.test_client() as c1:
            with c1.session_transaction() as sess:
                sess["user_id"] = 10
            for _ in range(5):
                c1.post("/documents/upload")
            assert c1.post("/documents/upload").status_code == 429

        with upload_app.test_client() as c2:
            with c2.session_transaction() as sess:
                sess["user_id"] = 11
            assert c2.post("/documents/upload").status_code == 200


# ===========================================================================
# SR-07b — Account lockout after consecutive fails
# ===========================================================================

class TestAccountLockout:

    def test_no_lockout_returns_false(self):
        user = {"locked_until": None}
        assert _is_account_locked(user) is False

    def test_locked_until_in_future_returns_true(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        user = {"locked_until": future}
        assert _is_account_locked(user) is True

    def test_locked_until_in_past_returns_false(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        user = {"locked_until": past}
        assert _is_account_locked(user) is False

    def test_naive_datetime_is_handled(self):
        future_naive = datetime.utcnow() + timedelta(minutes=10)
        user = {"locked_until": future_naive}
        assert _is_account_locked(user) is True

    def test_remaining_minutes_correct(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=14, seconds=30)
        user = {"locked_until": future}
        assert _get_remaining_minutes(user) == 14

    def test_remaining_minutes_no_lockout(self):
        user = {"locked_until": None}
        assert _get_remaining_minutes(user) == 0

    def test_register_failed_attempt_calls_increment(self):
        with patch("app.components.auth_session.session_lifecycle.users") as mock_users:
            _register_failed_attempt("alice")
            mock_users.increment_failed_attempts.assert_called_once_with("alice")

    def test_reset_lockout_calls_reset(self):
        with patch("app.components.auth_session.session_lifecycle.users") as mock_users:
            _reset_lockout("alice")
            mock_users.reset_failed_attempts.assert_called_once_with("alice")
