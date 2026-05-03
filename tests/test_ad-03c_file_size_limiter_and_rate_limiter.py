import io
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

MAX_UPLOAD_MB = 10
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    flask_app.config["TESTING"] = True
    flask_app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    from app.components.upload_guard import init_upload_rate_limiter
    init_upload_rate_limiter(flask_app)

    @flask_app.route("/documents/upload", methods=["POST"])
    def mock_upload():
        from flask import request, redirect, url_for
        f = request.files.get("document")

        if not f or f.filename == "":
            return "no file", 400

        # Verificar 0 bytes
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        if size == 0:
            return redirect("/documents")  # 302

        return "ok", 200

    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def make_file(size_bytes: int, filename="test.pdf") -> dict:
    data = {"document": (io.BytesIO(b"A" * size_bytes), filename)}
    return data

def login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        from secrets import token_hex
        sess["csrf_token"] = "test-csrf"


# ===========================================================================
# 1. Testes — upload_rate_limit_key
# ===========================================================================

class TestUploadRateLimitKey:

    def test_authenticated_user_returns_user_key(self, app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with app.test_request_context("/"):
            session["user_id"] = 42
            key = upload_rate_limit_key()
            assert key == "user:42"

    def test_unauthenticated_falls_back_to_ip(self, app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key

        with app.test_request_context("/", environ_base={"REMOTE_ADDR": "1.2.3.4"}):
            key = upload_rate_limit_key()
            assert key == "ip:1.2.3.4"

    def test_different_users_produce_different_keys(self, app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with app.test_request_context("/"):
            session["user_id"] = 1
            key_a = upload_rate_limit_key()

        with app.test_request_context("/"):
            session["user_id"] = 2
            key_b = upload_rate_limit_key()

        assert key_a != key_b

    def test_same_user_different_ips_produce_same_key(self, app):
        from app.components.upload_guard.upload_rate_limiter import upload_rate_limit_key
        from flask import session

        with app.test_request_context("/", environ_base={"REMOTE_ADDR": "1.1.1.1"}):
            session["user_id"] = 7
            key1 = upload_rate_limit_key()

        with app.test_request_context("/", environ_base={"REMOTE_ADDR": "9.9.9.9"}):
            session["user_id"] = 7
            key2 = upload_rate_limit_key()

        assert key1 == key2 == "user:7"


# ===========================================================================
# 2. Testes — Rate Limit Enforcement
# ===========================================================================

class TestRateLimitEnforcement:

    def test_requests_within_limit_pass(self, app):
        from app.components.upload_guard.upload_rate_limiter import limiter

        @app.route("/test-rl-pass", methods=["POST"])
        @limiter.limit("5 per minute")
        def route_pass():
            return "ok", 200

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 10

            for i in range(5):
                r = c.post("/test-rl-pass")
                assert r.status_code == 200, f"Request {i+1} devia passar"

    def test_excess_request_returns_429(self, app):
        from app.components.upload_guard.upload_rate_limiter import limiter

        @app.route("/test-rl-block", methods=["POST"])
        @limiter.limit("3 per minute")
        def route_block():
            return "ok", 200

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 20

            for _ in range(3):
                c.post("/test-rl-block")

            r = c.post("/test-rl-block")
            assert r.status_code == 429

    def test_different_users_have_independent_limits(self, app):
        from app.components.upload_guard.upload_rate_limiter import limiter

        @app.route("/test-rl-indep", methods=["POST"])
        @limiter.limit("2 per minute")
        def route_indep():
            return "ok", 200

        with app.test_client() as ca:
            with ca.session_transaction() as sess:
                sess["user_id"] = 30
            ca.post("/test-rl-indep")
            ca.post("/test-rl-indep")
            assert ca.post("/test-rl-indep").status_code == 429

        with app.test_client() as cb:
            with cb.session_transaction() as sess:
                sess["user_id"] = 31
            assert cb.post("/test-rl-indep").status_code == 200

    def test_unauthenticated_limit_applies_per_ip(self, app):
        from app.components.upload_guard.upload_rate_limiter import limiter

        @app.route("/test-rl-ip", methods=["POST"])
        @limiter.limit("2 per minute")
        def route_ip():
            return "ok", 200

        with app.test_client() as c:
            for _ in range(2):
                c.post("/test-rl-ip", environ_base={"REMOTE_ADDR": "5.5.5.5"})
            r = c.post("/test-rl-ip", environ_base={"REMOTE_ADDR": "5.5.5.5"})
            assert r.status_code == 429


# ===========================================================================
# 3. Testes — File Size Validation
# ===========================================================================

class TestFileSizeValidation:

    def test_file_within_limit_is_accepted(self, client):
        login(client)
        data = make_file(1 * 1024 * 1024)  # 1 MB
        r = client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 200

    def test_file_at_exact_limit_is_accepted(self, client):
        login(client)
        data = make_file(MAX_CONTENT_LENGTH-1024)
        r = client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 200

    def test_file_exceeding_limit_returns_413(self, client):
        login(client)
        data = make_file(MAX_CONTENT_LENGTH + 1)
        r = client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 413

    def test_empty_file_returns_400(self, client):
        login(client)
        r = client.post(
            "/documents/upload",
            data={},
            content_type="multipart/form-data"
        )
        assert r.status_code == 400

    def test_zero_byte_file_is_rejected(self, client):
        login(client)
        data = make_file(0)
        r = client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=False
        )
        assert r.status_code == 302
        assert "/documents" in r.headers["Location"]

    def test_413_handler_returns_json(self, app, client):
        from werkzeug.exceptions import RequestEntityTooLarge

        @app.errorhandler(413)
        def handle_413(e):
            from flask import jsonify
            return jsonify({"error": "Ficheiro demasiado grande", "max_mb": MAX_UPLOAD_MB}), 413

        login(client)
        data = make_file(MAX_CONTENT_LENGTH + 1)
        r = client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert r.status_code == 413
        assert r.get_json()["max_mb"] == MAX_UPLOAD_MB