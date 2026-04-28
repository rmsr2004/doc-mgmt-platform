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
    
def share_document(document_id, target_user_id):
    return utils.query_commit(
        "INSERT INTO document_shares (document_id, shared_with) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (document_id, target_user_id, )
    )

def get_shared_documents_for_user(user_id):
    return utils.query_fetch_all(
        """
        SELECT
        d.id,
        d.title,
        d.filename,
        d.metadata,
        d.uploaded_at,
        u.username AS owner_username
        FROM documents d
        JOIN document_shares ds ON ds.document_id = d.id
        JOIN users u ON u.id = d.owner_id
        WHERE ds.shared_with = %s
        ORDER BY d.uploaded_at DESC;
        """,
        (user_id, )
    )