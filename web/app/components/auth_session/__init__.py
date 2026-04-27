"""
auth_session/
-------------
Implements AD-02: dedicated authentication and session management component.

Responsible for:
  - Session cookie security configuration (SR-02)
  - Session lifecycle: login and logout (SR-13)
  - Authentication enforcement on protected routes (SR-13)
  - Route definitions for /login and /logout

Modules:
  - session_config.py    : cookie security flags (SR-02)
  - session_lifecycle.py : login_user(), logout_user()
  - auth_required.py     : login_required decorator (SR-13)
  - routes.py            : /login, /logout endpoints
"""

from .routes import auth_bp