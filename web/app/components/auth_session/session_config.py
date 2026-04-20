"""
session_config.py
-----------------
Implements SR-02: Enforce HttpOnly and Secure flags on authentication cookies.

Configures Flask session cookies with the following security flags:
  - HttpOnly : prevents client-side JavaScript from accessing the session cookie,
               mitigating session hijacking via XSS attacks.
  - Secure   : ensures the session cookie is only transmitted over HTTPS,
               mitigating interception over unencrypted channels.
"""
import os

def configure_session(app):
    app.config["SESSION_COOKIE_HTTPONLY"] = True    
    app.config["SESSION_COOKIE_SECURE"]   = os.getenv("FLASK_ENV") == "production" 
    return
