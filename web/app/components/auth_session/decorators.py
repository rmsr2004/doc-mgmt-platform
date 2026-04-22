"""
decorators.py
----------------
Decorators-based enforcement of authentication on protected routes.
"""

import functools
from time import time
import flask

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in flask.session:
            flask.flash("Please log in first.", "error")
            return flask.redirect(flask.url_for("auth_session.login"))
        
        expires_at = flask.session.get("expires_at")
        if expires_at and time.time() > expires_at:
            flask.session.clear()
            flask.flash("Your session has expired. Please log in again.", "error")
            return flask.redirect(flask.url_for("auth_session.login"))
        
        return fn(*args, **kwargs)

    return wrapper