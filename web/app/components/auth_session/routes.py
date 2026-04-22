"""
routes.py
---------
Flask Blueprint exposing /login and /logout as part of the
auth_session component. Registered in create_app() via auth_bp.
"""
from flask import Blueprint, request, flash, render_template, redirect, url_for, session

from app.components.auth_session import session_lifecycle

auth_bp = Blueprint("auth_session", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        result = session_lifecycle.login_user(username, password)
        
        if result.is_failure():
            flash(result.error.message, "error")
            return render_template("login.html")
            
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
