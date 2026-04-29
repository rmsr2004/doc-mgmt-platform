"""
auth_session/
-------------
Implements AD-02: Dedicated authentication and session management component.

Responsible for:
  - Session cookie security configuration (SR-02)
  - Session lifecycle: login and logout (SR-13)
  - Authentication enforcement on protected routes (SR-13)
  - CSRF protection for state-changing operations (SR-11b, AD-02c)
  - Route definitions for /login and /logout

Modules:
  - session_config.py    : Cookie security flags configuration (SR-02, SR-11a)
  - session_lifecycle.py : Credential verification, login_user(), logout_user()
  - decorators.py        : login_required and admin_required decorators (SR-13, SR-08)
  - routes.py            : /login, /logout endpoints
  - csrf.py              : CSRF token generation and rotation
  - csrf_filter.py       : CSRF Filter at the Single Access Point (AD-02c, SR-11b)
"""

from .routes import auth_bp
