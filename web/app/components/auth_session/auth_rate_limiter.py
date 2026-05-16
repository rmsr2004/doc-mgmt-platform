import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask import current_app

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

def init_auth_rate_limiter(app):
    app.config["RATELIMIT_ENABLED"] = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
    limiter.init_app(app)
