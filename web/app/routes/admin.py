#
# IMPORTANT: We should create the component Admin Service that will have the file with the routes (admin.py)
#            and one with the database functions (service.py)
#

from flask import Blueprint, redirect, render_template, url_for, session, flash

from app.components.auth_session.decorators import login_required, admin_required
import app.components.dal.users as users
from app.shared.result.Result import Error

admin_bp = Blueprint("admin", __name__)
    
@admin_bp.route("/admin", methods=["GET"])
@login_required
@admin_required
def admin_page():
    users_list = users.get_all_users()
    if type(users_list) is Error:
        flash(users_list.message, "error")
        
    return render_template("users.html", users=users_list)

@admin_bp.route("/admin/toggle_user_status/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user_status(user_id):
    if user_id == session["user_id"]:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("admin.admin_page"))
    
    users.update_user_status(user_id)
    
    return redirect(url_for("admin.admin_page"))