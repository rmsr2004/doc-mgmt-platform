from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import SECRET_KEY, UPLOAD_FOLDER, BASE_DIR
from app.routes import index, health, admin
from app.components.auth_session.session_config import configure_session
from app.components.auth_session.routes import auth_bp
from app.components.auth_session import ( csrf, csrf_filter )
from app.components.document_service.routes import document_bp

app = None

def create_app(test_config=None):
    global app
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.secret_key = SECRET_KEY
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    
    # Configure session management for authentication (Authentication & Session)
    configure_session(app)
    
    # Trust exactly one reverse proxy in front of Flask
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Register the CSRF filter to enforce token validation on state-changing requests
    csrf_filter.register_csrf_filter(app)
    
    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf.get_or_create_csrf_token()}
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(document_bp)

    app.register_blueprint(index.bp)
    app.register_blueprint(health.bp)

    return app

    # ------------------------------------------------------------------
    # Planned / Not Yet Implemented Endpoints
    #
    # The following routes are part of the intended system interface and
    # are not implemented in the baseline version of the application.
    #
    # The expected behavior of these endpoints is summarized below.
    #
    # Document operations
    #
    #   GET  /documents/<id>/download
    #       Download the specified document.
    #       Success: returns file contents (HTTP 200)
    #       Errors: 404 if the document does not exist
    #
    #   POST /documents/<id>/share
    #       Share a document with another user.
    #       Form parameter:
    #           shared_with  -> target user id
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    # Shared documents
    #
    #   GET  /shared
    #       Display documents that were shared with the current user.
    #       Success: HTTP 200
    #
    #   GET  /shared/<id>/download
    #       Download a document that was shared with the current user.
    #       Success: returns file contents (HTTP 200)
    #
    # Administration
    #
    #   GET  /admin/users
    #       Display a list of users in the system.
    #       Success: HTTP 200
    #
    #   POST /admin/users/<id>/enable
    #       Enable a user account.
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    #   POST /admin/users/<id>/disable
    #       Disable a user account.
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    # ------------------------------------------------------------------