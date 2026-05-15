from flask import Blueprint, current_app
from app.config import get_db

bp = Blueprint("health", __name__)

@bp.route("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "ratelimit_enabled": current_app.config.get("RATELIMIT_ENABLED", True)}, 200
    except Exception:
        return {"status": "error"}, 500