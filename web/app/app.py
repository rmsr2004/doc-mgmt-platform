from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import SECRET_KEY, UPLOAD_FOLDER, BASE_DIR
from app.routes import index, health, users
from app.components.auth_session import auth_bp, csrf, csrf_filter, session_config
from app.components.document_service import document_bp
from app.components.admin_service import admin_bp
from app.components.upload_guard.upload_rate_limiter import init_upload_rate_limiter
from app.components.auth_session.auth_rate_limiter import init_auth_rate_limiter

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
    app.jinja_env.autoescape = True
    
    # Trust exactly one reverse proxy in front of Flask
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure session management for authentication (Authentication & Session)
    session_config.configure_session(app)
    
    # Trust exactly one reverse proxy in front of Flask
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Register the CSRF filter to enforce token validation on state-changing requests
    csrf_filter.register_csrf_filter(app)
    
    init_upload_rate_limiter(app)
    init_auth_rate_limiter(app)
    
    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf.get_or_create_csrf_token()}
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(users.users_bp)

    return app
