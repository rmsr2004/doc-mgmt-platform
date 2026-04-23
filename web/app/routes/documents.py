import pathlib
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.config import BASE_DIR
from app.components.auth_session.decorators import login_required
import app.components.dal.documents as documents
from app import utils

bp = Blueprint("documents", __name__)

def extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)

@bp.route("/documents/<int:document_id>")
@login_required
def document_details(document_id):
    row = documents.get_document_details(document_id)

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

    docs = documents.get_documents_for_user(owner_id)

    documents_list = [
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
        documents=documents_list,
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

    documents.upload_document(user_id, title, uploaded_file.filename, metadata)

    return redirect(url_for("documents.documents_page", uploaded=title))