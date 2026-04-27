from flask import Blueprint, redirect, render_template, url_for, session, flash

from app.components.auth_session.decorators import login_required, admin_required

from . import service

admin_bp = Blueprint("admin", __name__)
    
@admin_bp.route("/admin", methods=["GET"])
@login_required
@admin_required
def admin_page():
    result = service.get_all_users()
    
    if result.is_failure():
        flash(result.error.message, "error")
        return render_template("users.html", users=[])
        
    return render_template("users.html", users=result.value)

@admin_bp.route("/admin/toggle_user_status/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user_status(user_id):
    if user_id == session["user_id"]:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("admin.admin_page"))
    
    result = service.update_user_status(user_id)
    
    if result.is_failure():
        flash(result.error.message, "error")
    
    return redirect(url_for("admin.admin_page"))