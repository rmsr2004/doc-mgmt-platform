from flask import Flask

from app.config import SECRET_KEY, UPLOAD_FOLDER, BASE_DIR
from app.routes import index, documents, download, share, admin, health
from app.components.auth_session.session_config import configure_session
from app.components.auth_session.routes import auth_bp

def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.secret_key = SECRET_KEY
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    
    # Configure session management for authentication (Authentication & Session)
    configure_session(app)
    
    app.register_blueprint(auth_bp)

    app.register_blueprint(index.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(download.bp)
    app.register_blueprint(share.bp)
    app.register_blueprint(admin.bp)
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