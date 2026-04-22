"""
decorators.py
----------------
Decorators-based enforcement of authentication on protected routes.
"""

import functools
from time import time
from flask import session, flash, redirect, url_for
from app.config import get_db

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    cur  = conn.cursor()
    
    query = """
        SELECT id, username, is_disabled
        FROM users
        WHERE id = %s
    """
    cur.execute(query, (user_id,))
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if row:
        return {"id": row[0], "username": row[1], "active": not row[2]}
    return None

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # checks if the user is logged in
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("auth_session.login"))
        
        # checks if the user still exists and is active
        user = get_user_by_id(session["user_id"])
        if user is None or not user["active"]:
            session.clear()
            flash("Your account has been disabled.", "error")
            return redirect(url_for("auth_session.login"))
        
        # checks if the session has expired
        expires_at = session.get("expires_at")
        if expires_at and time.time() > expires_at:
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for("auth_session.login"))
        
        return fn(*args, **kwargs)

    return wrapper

def admin_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session["is_admin"]:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("index.index"))
        return fn(*args, **kwargs)
    
    return wrapper
