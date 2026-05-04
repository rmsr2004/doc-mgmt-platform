"""
routes.py
---------
Flask Blueprint exposing /login and /logout as part of the
auth_session component. Registered in create_app() via auth_bp.
"""
from flask import Blueprint, request, flash, render_template, redirect, url_for, session, current_app

from . import session_lifecycle, auth_rate_limiter

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

        result = session_lifecycle.login_user(username, password)
        
        if result.is_failure():
            flash(result.error.message, "error")
            return render_template("login.html"), result.error.http_code
            
        user = result.value
        session_lifecycle.open_session(user)
        
        if session["is_admin"]:
            return redirect(url_for("admin.admin_page"))
        
        return redirect(url_for("documents.documents_page"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session_lifecycle.close_session()
    return redirect(url_for("auth_session.login"))
