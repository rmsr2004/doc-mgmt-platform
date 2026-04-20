from flask import Blueprint, session, redirect, url_for

bp = Blueprint("index", __name__)

@bp.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("documents.documents_page"))
    return redirect(url_for("login.login"))