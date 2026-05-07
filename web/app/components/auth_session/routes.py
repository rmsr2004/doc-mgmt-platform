"""
routes.py
---------
Flask Blueprint exposing /login and /logout as part of the
auth_session component. Registered in create_app() via auth_bp.

Audit logging (SR-06-A):
  Every login attempt — successful or failed — and every logout
  is recorded via app.components.audit_log.
"""
from flask import Blueprint, request, flash, render_template, redirect, url_for, session, current_app

from . import session_lifecycle, auth_rate_limiter
from app.components.audit_log import log_auth_event

auth_bp = Blueprint("auth_session", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
@auth_rate_limiter.limiter.limit("10 per minute")
def login():
    error = request.args.get("error")
    if error:
        current_app.logger.info("Error Too Many Requests")
        flash("Too Many Requests", "error")
        return render_template("login.html")
    
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        source_ip = request.remote_addr

        result = session_lifecycle.login_user(username, password)
        
        if result.is_failure():
            # SR-06-A: record every failed authentication attempt
            log_auth_event(
                action="login_failed",
                outcome="failure",
                source_ip=source_ip,
                actor_id=None,        # identity not yet verified
                actor_username=username,
            )
            flash(result.error.message, "error")
            return render_template("login.html"), result.error.http_code
            
        user = result.value
        session_lifecycle.open_session(user)

        # SR-06-A: record successful login
        log_auth_event(
            action="login_success",
            outcome="success",
            source_ip=source_ip,
            actor_id=user["id"],
            actor_username=user["username"],
        )
        
        if session["is_admin"]:
            return redirect(url_for("admin.admin_page"))
        
        return redirect(url_for("documents.documents_page"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    # SR-06-A: record logout before the session is cleared
    actor_id       = session.get("user_id")
    actor_username = session.get("username")
    source_ip      = request.remote_addr

    session_lifecycle.close_session()

    log_auth_event(
        action="logout",
        outcome="success",
        source_ip=source_ip,
        actor_id=actor_id,
        actor_username=actor_username,
    )

    return redirect(url_for("auth_session.login"))
