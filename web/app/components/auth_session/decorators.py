"""
decorators.py
----------------
Decorators-based enforcement of authentication on protected routes.
"""

import functools
from time import time
import flask
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
        if "user_id" not in flask.session:
            flask.flash("Please log in first.", "error")
            return flask.redirect(flask.url_for("auth_session.login"))
        
        # checks if the user still exists and is active
        user = get_user_by_id(flask.session["user_id"])
        if user is None or not user["active"]:
            flask.session.clear()
            flask.flash("Your account has been disabled.", "error")
            return flask.redirect(flask.url_for("auth_session.login"))
        
        # checks if the session has expired
        expires_at = flask.session.get("expires_at")
        if expires_at and time.time() > expires_at:
            flask.session.clear()
            flask.flash("Your session has expired. Please log in again.", "error")
            return flask.redirect(flask.url_for("auth_session.login"))
        
        return fn(*args, **kwargs)

    return wrapper