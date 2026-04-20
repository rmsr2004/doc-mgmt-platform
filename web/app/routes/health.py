from flask import Blueprint
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
        return {"status": "ok"}, 200
    except Exception:
        return {"status": "error"}, 500