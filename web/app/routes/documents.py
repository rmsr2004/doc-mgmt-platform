import pathlib
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.config import get_db, BASE_DIR
from app.components.auth_session.auth_required import login_required
from app import db, utils

bp = Blueprint("documents", __name__)

def extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)

def get_documents_for_user(cur, owner_id):
    query = f"""
        SELECT id,title,filename,uploaded_at
        FROM documents
        WHERE owner_id=%s
        ORDER BY uploaded_at DESC
    """ % owner_id
    cur.execute(query)
    return cur.fetchall()

@bp.route("/documents/<int:document_id>")
def document_details(document_id):
    conn = get_db()
    cur = conn.cursor()

    # intentionally missing authorization check
    cur.execute(utils.prepare_query("""
        SELECT id, owner_id, title, filename, metadata
        FROM documents
        WHERE id = %s
        """,
        (document_id,)))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return "Document not found", 404

    document = {
        "id": row[0],
        "owner_id": row[1],
        "title": row[2],
        "filename": row[3],
        "metadata": row[4],
    }

    return render_template("document_details.html", document=document)

@bp.route("/documents")
@login_required
def documents_page():
    requested_user_id = request.args.get("user_id")
    current_user_id = session.get("user_id")

    owner_id = requested_user_id or current_user_id

    conn = get_db()
    cur = conn.cursor()

    docs = get_documents_for_user(cur, owner_id)

    cur.close()
    conn.close()

    documents = [
        {
            "id": d[0],
            "title": d[1],
            "filename": d[2],
            "uploaded_at": d[3],
        }
        for d in docs
    ]

    return render_template(
        "documents.html",
        documents=documents,
        requested_user_id=owner_id,
        current_user_id=current_user_id,
        username=session.get("username"),
    )

@bp.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    user_id = session.get("user_id")
    title = request.form.get("title", "Untitled")
    uploaded_file = request.files.get("document")

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please choose a file.", "error")
        return redirect(url_for("documents.documents_page"))

    upload_folder = pathlib.Path(bp.root_path).parent.parent / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = utils.sanitize_filename(uploaded_file.filename)
    destination = upload_folder / uploaded_file.filename
    uploaded_file.save(destination)
    metadata = extract_metadata(destination)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO documents (owner_id, title, filename, metadata)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, title, uploaded_file.filename, metadata),
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("documents.documents_page", uploaded=title))