import secrets
from flask import session

CSRF_SESSION_KEY = "csrf_token"

def get_or_create_csrf_token() -> str:
    """
    Returns the current CSRF token for the session.
    Creates one if it does not exist yet.
    Used to inject the token into templates.
    """
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token

def rotate_csrf_token() -> str:
    """
    Generates a new CSRF token and stores it in the session.
    Called on login and logout to prevent session fixation
    of the CSRF token.
    """
    token = secrets.token_urlsafe(32)
    session[CSRF_SESSION_KEY] = token
    return token