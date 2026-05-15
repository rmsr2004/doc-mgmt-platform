from flask import request, session, abort

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

EXEMPT_PATHS = {"/health"}

def register_csrf_filter(app) -> None:
    """
    AD-02c : CSRF Filter at the Single Access Point.
    SR-11b : Synchronizer Token Pattern for all state-changing
             operations (POST / PUT / DELETE).

    Validates that every state-changing request from an
    authenticated session carries a CSRF token that matches
    the one stored in the session.

    Token can be supplied via:
      - Form field  : csrf_token

    Requests from unauthenticated sessions are not checked
    here — they will be rejected by the auth middleware.
    """
    @app.before_request
    def csrf_protect():
        if request.method in SAFE_METHODS:
            return

        if request.path in EXEMPT_PATHS:
            return

        # Only protect authenticated sessions.
        # Unauthenticated requests will be rejected by
        # the authentication middleware before reaching routes.
        if "user_id" not in session:
            return

        expected = session.get("csrf_token")

        # Accept token from form body
        provided = request.form.get("csrf_token")

        if not expected or not provided or provided != expected:
            abort(403)
        return
    return