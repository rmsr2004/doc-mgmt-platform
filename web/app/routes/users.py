
from flask import Blueprint

from app.components.auth_session.decorators import login_required
from app.components.dal import users

users_bp = Blueprint("users", __name__)

@users_bp.route("/users")
@login_required
def list_users():
    users_list = users.get_all_users()
    return [
        {
            "id": user["id"],
            "username": user["username"]
        }
        for user in users_list
    ]