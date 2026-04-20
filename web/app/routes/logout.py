from flask import Blueprint, session, redirect, url_for

bp = Blueprint("logout", __name__)

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login.login"))