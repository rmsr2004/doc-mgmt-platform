"""
routes.py — admin_service
--------------------------
Flask Blueprint exposing /admin/users/* endpoints.

Audit logging (SR-06-M):
  Every enable/disable account operation is recorded via
  app.components.audit_log, capturing:
    - administrator identity (actor_id / actor_username)
    - target user (target_user_id)
    - action performed ('user_enabled' / 'user_disabled')
    - outcome ('success' / 'failure')
    - timestamp (set automatically in the DB)
    - source IP
"""
from flask import Blueprint, redirect, render_template, url_for, session, flash, request

from app.components.auth_session.decorators import login_required, admin_required
from app.components.audit_log import log_admin_event

from . import service

admin_bp = Blueprint("admin", __name__)
    
@admin_bp.route("/admin/users", methods=["GET"])
@login_required
@admin_required
def admin_page():
    result = service.get_all_users()
    
    if result.is_failure():
        flash(result.error.message, "error")
        return render_template("users.html", users=[]), result.error.http_code
        
    return render_template("users.html", users=result.value)

@admin_bp.route("/admin/users/<int:user_id>/enable", methods=["POST"])
@login_required
@admin_required
def enable_user_account(user_id):
    if user_id == session["user_id"]:
        flash("You cannot enable your own account.", "error")
        return redirect(url_for("admin.admin_page"))
    
    result = service.update_user_status(user_id, False)
    
    # SR-06-M: log regardless of outcome
    log_admin_event(
        action="user_enabled",
        admin_id=session["user_id"],
        admin_username=session["username"],
        target_user_id=user_id,
        outcome="failure" if result.is_failure() else "success",
        source_ip=request.remote_addr,
    )

    if result.is_failure():
        flash(result.error.message, "error")
        return redirect(url_for("admin.admin_page")), result.error.http_code
    
    flash("User status updated successfully.", "success")
    return redirect(url_for("admin.admin_page"))

@admin_bp.route("/admin/users/<int:user_id>/disable", methods=["POST"])
@login_required
@admin_required
def disable_user_account(user_id):
    if user_id == session["user_id"]:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("admin.admin_page"))
    
    result = service.update_user_status(user_id, True)
    
    # SR-06-M: log regardless of outcome
    log_admin_event(
        action="user_disabled",
        admin_id=session["user_id"],
        admin_username=session["username"],
        target_user_id=user_id,
        outcome="failure" if result.is_failure() else "success",
        source_ip=request.remote_addr,
    )

    if result.is_failure():
        flash(result.error.message, "error")
        return redirect(url_for("admin.admin_page"))
    
    flash("User status updated successfully.", "success")
    return redirect(url_for("admin.admin_page"))
