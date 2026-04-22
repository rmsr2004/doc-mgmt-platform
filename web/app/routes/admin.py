from flask import Blueprint, render_template
from collections import namedtuple

from app.components.auth_session.decorators import login_required
from app.config import get_db

admin_bp = Blueprint("admin", __name__)

UserRow = namedtuple("UserRow", ["id", "username", "is_disabled"])

def get_all_users(cur):
    query = """
        SELECT id, username, is_disabled
        FROM users
        ORDER BY id ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    return [UserRow(r[0], r[1], r[2]) for r in rows]
    
@admin_bp.route("/admin", methods=["GET"])
@login_required
def admin_page():
    conn = get_db()
    cur = conn.cursor()
    
    users = get_all_users(cur)
    return render_template("users.html", users=users)

# Not implemented, just a placeholder to show the missing authorization check in the template
@admin_bp.route("/admin/disable_user/<int:user_id>", methods=["POST"])
@login_required
def disable_user(user_id):
    return True