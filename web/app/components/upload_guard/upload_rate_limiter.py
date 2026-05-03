from flask import session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def upload_rate_limit_key() -> str:
    user_id = session.get("user_id")
    if user_id is not None:
        return f"user:{user_id}"
    return f"ip:{get_remote_address()}"


limiter = Limiter(
    key_func=upload_rate_limit_key,
    default_limits=[],
    storage_uri="memory://",
)

def init_upload_rate_limiter(app):
    limiter.init_app(app)
