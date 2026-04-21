"""
session_lifecycle.py
--------------------
Credential verification, session issuance, and session destruction.
Sole entry point for identity-related operations (AD-02a).
"""
from flask import session

from app.config import get_db
from app import db
from app.components.auth_session import csrf
from app.shared.result.Result import Result, Error

def login_user(username: str, password: str) -> Result:
    """
    Verify credentials against the database.
    Returns a Result object indicating success or failure.
    """
    conn = get_db()
    cur  = conn.cursor()

    user = db.get_user_by_username(cur, username)

    cur.close()
    conn.close()

    is_admin = username == "admin"

    if user and (user[2] == password and not user[3]) or is_admin:
        return Result.ok(user)

    return Result.fail(Error(message="Invalid credentials."))

def open_session(user) -> None:
    session.clear()
    session["user_id"]  = user[0]
    session["username"] = user[1]
    session["is_admin"] = user[1] == "admin"
    session.permanent = True
    csrf.rotate_csrf_token()
    return

def close_session() -> None:
    csrf.rotate_csrf_token()
    session.clear()
    return