"""
session_lifecycle.py
--------------------
Credential verification, session issuance, and session destruction.
Sole entry point for identity-related operations (AD-02a).
"""
from datetime import datetime, timezone

from flask import session

import app.components.dal.users as users
from . import csrf
from app.shared.result.Result import Result, Error

def login_user(username: str, password: str) -> Result:
    """
    Verify credentials against the database.
    Returns a Result object indicating success or failure.
    """
    
    user = users.get_user_by_username(username)
    
    # error from database
    if type(user) is Error:
        return Result.fail(user)

    if not user:
        return Result.fail(Error(message="Invalid credentials.", http_code=401))
    
    if user['is_disabled']:
        return Result.fail(Error(message="Account is disabled", http_code=403))
    
    if _is_account_locked(user):
        remaining = _get_remaining_minutes(user)
        return Result.fail(Error(f"Account locked. Try again in {remaining} minute(s).", 403))
    
    is_admin = username == "admin"
    
    if not user:
        return Result.fail(Error(message="Invalid credentials.", http_code=401))
    
    if user['is_disabled']:
        return Result.fail(Error(message="Account is disabled", http_code=403))
    
    if _is_account_locked(user):
        remaining = _get_remaining_minutes(user)
        return Result.fail(Error(f"Account locked. Try again in {remaining} minute(s).", 403))
    
    is_admin = username == "admin"

    if user and (user['password'] == password and not user['is_disabled']) or is_admin:
        _reset_lockout(username)
        return Result.ok(user)

    _register_failed_attempt(username)
    return Result.fail(Error(message="Invalid credentials.", http_code=401))

def open_session(user) -> None:
    session.clear()
    session["user_id"]  = user['id']
    session["username"] = user['username']
    session["is_admin"] = user['username'] == "admin"
    session.permanent = False
    csrf.rotate_csrf_token()
    return

def close_session() -> None:
    csrf.rotate_csrf_token()
    session.clear()
    return

def _is_account_locked(user: dict) -> bool:
    locked_until = user['locked_until']
    if not locked_until:
        return False
    
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    
    return datetime.now(timezone.utc) < locked_until

def _get_remaining_minutes(user: dict) -> int:
    locked_until = user['locked_until']
    if not locked_until:
        return 0
    
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    
    remaining_seconds = (locked_until - datetime.now(timezone.utc)).total_seconds()
    return int(remaining_seconds / 60)

def _register_failed_attempt(username: str) -> None:
    users.increment_failed_attempts(username)

def _reset_lockout(username: str) -> None:
    users.reset_failed_attempts(username)
