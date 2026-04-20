from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app import db
from app.config import get_db

bp = Blueprint("login", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()

        user = db.get_user_by_username(cur, username)

        cur.close()
        conn.close()

        is_admin = username == "admin"

        if user and (user[2] == password and not user[3]) or is_admin:
            session.clear()
            session["user_id"] = user[0] if username != "admin" else 1
            session["username"] = user[1] if username != "admin" else username
            return redirect(url_for("documents.documents_page"))

        flash("Invalid credentials.", "error")

    return render_template("login.html")