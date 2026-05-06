"""
decorators.py
----------------
Decorators-based enforcement of authentication on protected routes.
"""

import functools
import time
from flask import session, flash, redirect, url_for, make_response, request, current_app

import app.components.dal.users as users
from app.shared.result.Result import Error

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # If the browser sent a cookie but the session is empty, Flask automatically
            # destroyed it because it exceeded PERMANENT_SESSION_LIFETIME.
            cookie_name = current_app.config.get("SESSION_COOKIE_NAME", "session")
            if request.cookies.get(cookie_name):
                flash("Your session has expired. Please log in again.", "error")
            else:
                flash("Please log in first.", "error")
                
            return redirect(url_for("auth_session.login"))
        
        # checks if the user still exists and is active
        user = users.get_user_by_id(session["user_id"])
        
        if type(user) is Error:
            session.clear()
            flash("An error occurred while fetching your user data. Please log in again.", "error")
            return redirect(url_for("auth_session.login"))
        
        if user is None or user["is_disabled"]:
            session.clear()
            flash("Your account has been disabled.", "error")
            return redirect(url_for("auth_session.login"))
                
        # Reset the timer to keep the user logged in as long as they keep clicking around the application
        last_active = session.get("last_active")
        timeout_seconds = current_app.config.get("PERMANENT_SESSION_LIFETIME").total_seconds()
        
        if last_active and (time.time() - last_active > timeout_seconds):
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for("auth_session.login"))
            
        # Update last activity timestamp to reset the idle timeout
        session["last_active"] = time.time()
        
        # Wrap response to prevent browser caching of protected pages
        response = make_response(fn(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response

    return wrapper

def admin_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session["is_admin"]:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("index.index"))
        return fn(*args, **kwargs)
    
    return wrapper
