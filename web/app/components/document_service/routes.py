import pathlib
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, send_from_directory

from app.components.auth_session.decorators import login_required
from . import service
from app import utils

document_bp = Blueprint("documents", __name__)

def _extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)

@document_bp.route("/documents/<int:document_id>")
@login_required
def document_details(document_id):
    result = service.get_document_details(document_id)
    
    if (result.is_failure()):
        flash(result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    return render_template("document_details.html", document=result.value)

@document_bp.route("/documents")
@login_required
def documents_page():
    requested_user_id = request.args.get("user_id")
    current_user_id = session.get("user_id")

    owner_id = requested_user_id or current_user_id

    documents = service.get_documents_for_user(owner_id)
    
    shared_documents = service.get_shared_documents_for_user(owner_id)
    
    if documents.is_failure() or shared_documents.is_failure():
        error_msg = (
            documents.error.message
            if documents.is_failure()
            else shared_documents.error.message
        )
        flash(error_msg, "error")
        return render_template(
            "documents.html",
            documents=[],
            shared_documents=[],
            current_user_id=current_user_id,
        )

    return render_template(
        "documents.html",
        documents=documents.value,
        shared_documents= shared_documents.value,
        requested_user_id=owner_id,
        current_user_id=current_user_id,
        username=session.get("username")
    )

@document_bp.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    user_id = session.get("user_id")
    title = request.form.get("title", "Untitled")
    uploaded_file = request.files.get("document")

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please choose a file.", "error")
        return redirect(url_for("documents.documents_page"))

    upload_folder = pathlib.Path(document_bp.root_path).parent.parent.parent / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = utils.sanitize_filename(uploaded_file.filename)
    destination = upload_folder / uploaded_file.filename
    uploaded_file.save(destination)
    metadata = _extract_metadata(destination)

    result = service.upload_document(user_id, title, uploaded_file.filename, metadata)
    
    if (result.is_failure()):
        flash(result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    return redirect(url_for("documents.documents_page", uploaded=title))

@document_bp.route("/documents/<int:document_id>/download", methods=["GET"])
@login_required
def download_document(document_id):
    user_id = session.get("user_id")
    doc = service.get_document_details(document_id)
    
    if (doc.is_failure()):
        flash(doc.error.message, "error")
        return redirect(url_for("documents.documents_page"))
    
    doc = doc.value
    
    if user_id != doc['owner_id']:
        flash("You do not have permission to download this document.", "error")
        return redirect(url_for("documents.documents_page"))
     
    upload_folder = pathlib.Path(document_bp.root_path).parent.parent.parent / "uploads"
    
    return send_from_directory(upload_folder, doc['filename'], as_attachment=True)

@document_bp.route("/documents/<int:document_id>/share", methods=["POST"])
@login_required
def share_document(document_id):
    share_with_user_id = request.form.get("share_with_user_id")
    
    if not share_with_user_id:
        flash("Please provide a user ID to share with.", "error")
        return redirect(url_for("documents.documents_page"))

    result = service.share_document(document_id, share_with_user_id)
    
    if (result.is_failure()):
        flash(result.error.message, "error")
    else:
        flash("Document shared successfully!", "success")

    return redirect(url_for("documents.documents_page"))
