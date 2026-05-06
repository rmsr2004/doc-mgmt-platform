"""
routes.py — document_service
-----------------------------
Flask Blueprint exposing all /documents/* and /shared/* endpoints.

Audit logging (SR-06-B):
  Every document access and sharing operation is recorded via
  app.components.audit_log, capturing:
    - requesting user (actor_id / actor_username)
    - document identifier (document_id)
    - action performed (see actions below)
    - outcome ('success' / 'failure')
    - timestamp (set automatically in the DB)
    - source IP (set automatically in the DB)


  Actions recorded:
    'document_upload'   — user uploads a new document
    'document_view'     — user accesses the document detail page
    'document_download' — user downloads their own document
    'document_share'    — user shares a document with another user
    'shared_download'   — user downloads a document shared with them
"""
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, send_from_directory, abort

from app.components.auth_session.decorators import login_required
from app.components.authorization import service as authz_service
from app.components.input_validation_filter import file_validator
from app.components.sanitizing_storage_adapter import adapter as storage_sanitizer
from app.components.upload_guard import limiter
from app.components.audit_log import log_document_event
from app.config import UPLOAD_FOLDER, UPLOAD_RATE_LIMIT
from . import service
from app import utils

document_bp = Blueprint("documents", __name__)

def _extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)

@document_bp.route("/documents")
@login_required
def documents_page():
    user_id = session.get("user_id")

    documents = service.get_documents_for_user(user_id)

    if documents.is_failure():
        flash(documents.error.message, "error")
        return render_template(
            "documents.html",
            documents=[],
            current_user_id=user_id,
        ), documents.error.http_code

    return render_template(
        "documents.html",
        documents=documents.value,
        requested_user_id=user_id,
        current_user_id=user_id,
        username=session.get("username")
    )
    
@document_bp.route("/documents/<int:document_id>")
@login_required
def document_details(document_id):
    user_id = session.get("user_id")
    
    access = authz_service.verify_document_access(document_id, user_id)
    
    if access.is_failure():
        # SR-06-B: record failed view attempt
        log_document_event(
            action="document_view",
            actor_id=user_id,
            actor_username=session.get("username", ""),
            document_id=document_id,
            outcome="failure",
            source_ip=request.remote_addr,
        )
        flash(access.error.message, "error")
        return redirect(url_for("documents.documents_page"))
    
    result = service.get_document_details(document_id)
    
    if result.is_failure():
        flash(result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    # SR-06-B: successful view
    log_document_event(
        action="document_view",
        actor_id=user_id,
        actor_username=session.get("username", ""),
        document_id=document_id,
        outcome="success",
        source_ip=request.remote_addr,
    )

    return render_template("document_details.html", document=result.value)

@document_bp.route("/documents/upload", methods=["POST", "GET"])
@login_required
@limiter.limit(UPLOAD_RATE_LIMIT)
def upload_document():
    error = request.args.get("error")
    if error:
        flash("File size exceeds the allowed limit.", "error")
        return redirect(url_for("documents.documents_page"))
    
    user_id = session.get("user_id")
    title = request.form.get("title", "Untitled").strip()
    uploaded_file = request.files.get("document")

    if not title or len(title) > 255:
        flash("Invalid title.", "error")
        return redirect(url_for("documents.documents_page"))

    validation_result = file_validator.validate_file(uploaded_file)
    if validation_result.is_failure():
        flash(validation_result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    sanitize_result = storage_sanitizer.sanitize_file(uploaded_file.filename)
    if sanitize_result.is_failure():
        flash(sanitize_result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    uuid_filename, original_filename, safe_path = sanitize_result.value
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    uploaded_file.save(safe_path)

    metadata = _extract_metadata(safe_path)

    result = service.upload_document(user_id, title, original_filename, uuid_filename, metadata)
    if result.is_failure():
        safe_path.unlink(missing_ok=True)
        flash(result.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    # SR-06-B: log successful upload — fetch document id from the newly created row
    new_doc = service.get_document_by_uuid(uuid_filename)
    doc_id = new_doc.value["id"] if new_doc and new_doc.is_ok() else None

    log_document_event(
        action="document_upload",
        actor_id=user_id,
        actor_username=session.get("username", ""),
        document_id=doc_id,
        outcome="success",
        source_ip=request.remote_addr,
    )

    return redirect(url_for("documents.documents_page", uploaded=title))

@document_bp.route("/documents/<int:document_id>/download", methods=["GET"])
@login_required
def download_document(document_id):
    user_id = session.get("user_id")
    
    access = authz_service.verify_document_access(document_id, user_id)
    
    if access.is_failure():
        # SR-06-B: failed download attempt
        log_document_event(
            action="document_download",
            actor_id=user_id,
            actor_username=session.get("username", ""),
            document_id=document_id,
            outcome="failure",
            source_ip=request.remote_addr,
        )
        if access.error.http_code == 404:
            abort(404)
        
        flash(access.error.message, "error")
        return redirect(url_for("documents.documents_page"))

    doc = service.get_document_details(document_id)
    
    if doc.is_failure():
        if doc.error.http_code == 404:
            abort(404)
        
        flash(doc.error.message, "error")
        return redirect(url_for("documents.documents_page"))
    
    doc = doc.value

    # SR-06-D: successful download
    log_document_event(
        action="document_download",
        actor_id=user_id,
        actor_username=session.get("username", ""),
        document_id=document_id,
        outcome="success",
        source_ip=request.remote_addr,
    )
    
    return send_from_directory(
        UPLOAD_FOLDER,
        doc['uuid_filename'],
        as_attachment=True,
        download_name=doc['filename']
    )

@document_bp.route("/documents/<int:document_id>/share", methods=["POST"])
@login_required
def share_document(document_id):
    share_with_user_id = request.form.get("share_with_user_id")
    user_id = session.get("user_id")
    
    if not share_with_user_id:
        flash("Please provide a user ID to share with.", "error")
        return redirect(url_for("documents.documents_page"))

    result = service.share_document(document_id, share_with_user_id)
    
    # SR-06-B: log share operation regardless of outcome
    log_document_event(
        action="document_share",
        actor_id=user_id,
        actor_username=session.get("username", ""),
        document_id=document_id,
        outcome="failure" if result.is_failure() else "success",
        source_ip=request.remote_addr,
    )

    if result.is_failure():
        flash(result.error.message, "error")
    else:
        flash("Document shared successfully!", "success")

    return redirect(url_for("documents.documents_page"))

@document_bp.route("/shared")
@login_required
def shared_documents_page():
    user_id = session.get("user_id")
    
    documents = service.get_shared_documents_for_user(user_id)

    if documents.is_failure():
        flash(documents.error.message, "error")
        return render_template(
            "shared_documents.html",
            documents=[],
            requested_user_id=user_id,
            current_user_id=user_id,
            username=session.get("username")
        ), documents.error.http_code

    return render_template(
        "shared_documents.html",
        documents=documents.value,
        requested_user_id=user_id,
        current_user_id=user_id,
        username=session.get("username")
    )

@document_bp.route("/shared/<int:document_id>/download", methods=["GET"])
@login_required
def download_shared_document(document_id):
    user_id = session.get("user_id")
    
    access = authz_service.verify_document_access(document_id, user_id)
    
    if access.is_failure():
        # SR-06-B: failed shared-document download
        log_document_event(
            action="shared_download",
            actor_id=user_id,
            actor_username=session.get("username", ""),
            document_id=document_id,
            outcome="failure",
            source_ip=request.remote_addr,
        )
        if access.error.http_code == 404:
            abort(404)
            
        flash(access.error.message, "error")
        return redirect(url_for("documents.documents_page"))
    
    doc = service.get_document_details(document_id)
    
    if doc.is_failure():
        if doc.error.http_code == 404:
            abort(404)
        
        flash(doc.error.message, "error")
        return redirect(url_for("documents.documents_page"))
    
    doc = doc.value

    # SR-06-B: successful shared-document download
    log_document_event(
        action="shared_download",
        actor_id=user_id,
        actor_username=session.get("username", ""),
        document_id=document_id,
        outcome="success",
        source_ip=request.remote_addr,
    )
    
    return send_from_directory(
        UPLOAD_FOLDER, 
        doc['uuid_filename'], 
        as_attachment=True,
        download_name=doc['filename']    
    )
