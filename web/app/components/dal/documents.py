from app.config import get_db

from . import utils

def get_documents_for_user(owner_id):
    return utils.query_fetch_all(
        "SELECT id,title,filename,uploaded_at FROM documents WHERE owner_id=%s ORDER BY uploaded_at DESC",
        (owner_id, )
    )

def get_document_details(document_id):
    return utils.query_fetch_one(
        "SELECT id, owner_id, title, filename, metadata FROM documents WHERE id = %s",
        (document_id, )
    )

def upload_document(owner_id, title, filename, metadata):
    return utils.query_commit(
        "INSERT INTO documents (owner_id, title, filename, metadata) VALUES (%s, %s, %s, %s)",
        (owner_id, title, filename, metadata, )
    )