# tests/api_tests/test_rate_limiting.py
"""
Tests for SR-07 / AD-07 / AD-03c: Rate Limiting, Account Lockout,
and File Size Enforcement.

Merged from:
  - test_ad-03c_file_size_limiter_and_rate_limiter.py
  - test_sr-07_ad07_rate_limiting_and_lockout.py

Unit-style tests using Flask test_client() and direct function calls.
"""
import io
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask

from app.components.auth_session.auth_rate_limiter import limiter as auth_limiter, init_auth_rate_limiter
from app.components.upload_guard.upload_rate_limiter import limiter as upload_limiter, init_upload_rate_limiter
from app.components.auth_session.session_lifecycle import _is_account_locked, _get_remaining_minutes, _register_failed_attempt, _reset_lockout

from app.config import LOCKOUT_DURATION, LOCKOUT_THRESHOLD

MAX_UPLOAD_MB = 10
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024  # 10 MB


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

@pytest.fixture
def file_size_app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    flask_app.config["TESTING"] = True
    flask_app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    init_upload_rate_limiter(flask_app)

    @flask_app.route("/documents/upload", methods=["POST"])
    def mock_upload():
        from flask import request, redirect
        f = request.files.get("document")

        if not f or f.filename == "":
            return "no file", 400

        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        if size == 0:
            return redirect("/documents")  # 302

        return "ok", 200

    return flask_app

@pytest.fixture
def file_size_client(file_size_app):
    return file_size_app.test_client()


def make_file(size_bytes: int, filename="test.pdf") -> dict:
    data = {"document": (io.BytesIO(b"A" * size_bytes), filename)}
    return data

def login_file_size(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["csrf_token"] = "test-csrf"


# ===========================================================================
# 1. Upload Rate Limit Key
# ===========================================================================

class TestUploadRateLimitKey:

    def test_authenticated_user_returns_user_key(self, file_size_app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with file_size_app.test_request_context("/"):
            session["user_id"] = 42
            key = upload_rate_limit_key()
            assert key == "user:42"

    def test_unauthenticated_falls_back_to_ip(self, file_size_app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key

        with file_size_app.test_request_context("/", environ_base={"REMOTE_ADDR": "1.2.3.4"}):
            key = upload_rate_limit_key()
            assert key == "ip:1.2.3.4"

    def test_different_users_produce_different_keys(self, file_size_app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with file_size_app.test_request_context("/"):
            session["user_id"] = 1
            key_a = upload_rate_limit_key()

        with file_size_app.test_request_context("/"):
            session["user_id"] = 2
            key_b = upload_rate_limit_key()

        assert key_a != key_b

    def test_same_user_different_ips_produce_same_key(self, file_size_app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with file_size_app.test_request_context("/", environ_base={"REMOTE_ADDR": "1.1.1.1"}):
            session["user_id"] = 7
            key1 = upload_rate_limit_key()

        with file_size_app.test_request_context("/", environ_base={"REMOTE_ADDR": "9.9.9.9"}):
            session["user_id"] = 7
            key2 = upload_rate_limit_key()

        assert key1 == key2 == "user:7"


# ===========================================================================
# 2. Login Rate Limit (SR-07a + AD-07a)
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
# 3. Upload Rate Limit (AD-07b)
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
# 4. Rate Limit Enforcement (generic limiter behaviour)
# ===========================================================================

class TestRateLimitEnforcement:

    def test_requests_within_limit_pass(self, file_size_app):

        @file_size_app.route("/test-rl-pass", methods=["POST"])
        @upload_limiter.limit("5 per minute")
        def route_pass():
            return "ok", 200

        with file_size_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 10

            for i in range(5):
                r = c.post("/test-rl-pass")
                assert r.status_code == 200, f"Request {i+1} devia passar"

    def test_excess_request_returns_429(self, file_size_app):

        @file_size_app.route("/test-rl-block", methods=["POST"])
        @upload_limiter.limit("3 per minute")
        def route_block():
            return "ok", 200

        with file_size_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 20

            for _ in range(3):
                c.post("/test-rl-block")

            r = c.post("/test-rl-block")
            assert r.status_code == 429

    def test_different_users_have_independent_limits(self, file_size_app):

        @file_size_app.route("/test-rl-indep", methods=["POST"])
        @upload_limiter.limit("2 per minute")
        def route_indep():
            return "ok", 200

        with file_size_app.test_client() as ca:
            with ca.session_transaction() as sess:
                sess["user_id"] = 30
            ca.post("/test-rl-indep")
            ca.post("/test-rl-indep")
            assert ca.post("/test-rl-indep").status_code == 429

        with file_size_app.test_client() as cb:
            with cb.session_transaction() as sess:
                sess["user_id"] = 31
            assert cb.post("/test-rl-indep").status_code == 200

    def test_unauthenticated_limit_applies_per_ip(self, file_size_app):

        @file_size_app.route("/test-rl-ip", methods=["POST"])
        @upload_limiter.limit("2 per minute")
        def route_ip():
            return "ok", 200

        with file_size_app.test_client() as c:
            for _ in range(2):
                c.post("/test-rl-ip", environ_base={"REMOTE_ADDR": "5.5.5.5"})
            r = c.post("/test-rl-ip", environ_base={"REMOTE_ADDR": "5.5.5.5"})
            assert r.status_code == 429


# ===========================================================================
# 5. File Size Validation
# ===========================================================================

class TestFileSizeValidation:

    def test_file_within_limit_is_accepted(self, file_size_client):
        login_file_size(file_size_client)
        data = make_file(1 * 1024 * 1024)  # 1 MB
        r = file_size_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 200

    def test_file_at_exact_limit_is_accepted(self, file_size_client):
        login_file_size(file_size_client)
        data = make_file(MAX_CONTENT_LENGTH-1024)
        r = file_size_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 200

    def test_file_exceeding_limit_returns_413(self, file_size_client):
        login_file_size(file_size_client)
        data = make_file(MAX_CONTENT_LENGTH + 1)
        r = file_size_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 413

    def test_empty_file_returns_400(self, file_size_client):
        login_file_size(file_size_client)
        r = file_size_client.post(
            "/documents/upload",
            data={},
            content_type="multipart/form-data"
        )
        assert r.status_code == 400

    def test_zero_byte_file_is_rejected(self, file_size_client):
        login_file_size(file_size_client)
        data = make_file(0)
        r = file_size_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=False
        )
        assert r.status_code == 302
        assert "/documents" in r.headers["Location"]

    def test_413_handler_returns_json(self, file_size_app, file_size_client):
        from werkzeug.exceptions import RequestEntityTooLarge

        @file_size_app.errorhandler(413)
        def handle_413(e):
            from flask import jsonify
            return jsonify({"error": "Ficheiro demasiado grande", "max_mb": MAX_UPLOAD_MB}), 413

        login_file_size(file_size_client)
        data = make_file(MAX_CONTENT_LENGTH + 1)
        r = file_size_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 413
        assert r.get_json()["max_mb"] == MAX_UPLOAD_MB


# ===========================================================================
# 6. Account Lockout (SR-07b)
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
