"""
session_config.py
-----------------
Implements SR-02: Enforce HttpOnly and Secure flags on authentication cookies.
Implements SR-11a: SameSite=Strict prevents cookie from being sent on cross-site requests (passive CSRF defence).

Configures Flask session cookies with the following security flags:
    - HttpOnly : prevents client-side JavaScript from accessing the session cookie, mitigating session hijacking via XSS attacks.
    - Secure   : ensures the session cookie is only transmitted over HTTPS, mitigating interception over unencrypted channels.
    - SameSite=Strict : prevents the session cookie from being sent on cross-site requests, mitigating CSRF attacks.
    - Permanent session lifetime of 8 hours, balancing security and usability.
               
"""
from datetime import timedelta
import os

def configure_session(app):
    app.config["SESSION_COOKIE_HTTPONLY"] = True    
    app.config["SESSION_COOKIE_SECURE"]   = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    return
