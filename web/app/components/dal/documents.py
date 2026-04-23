from app.config import get_db

from . import utils

def get_documents_for_user(owner_id):
    conn = get_db()
    cur = conn.cursor()
    query = f"""
        SELECT id,title,filename,uploaded_at
        FROM documents
        WHERE owner_id=%s
        ORDER BY uploaded_at DESC
    """ % owner_id
    cur.execute(query)
    conn.commit()

    return cur.fetchall()

def get_document_details(document_id):
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
    conn.commit()

    return row

def upload_document(owner_id, title, filename, metadata):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents (owner_id, title, filename, metadata)
        VALUES (%s, %s, %s, %s)
        """,
        (owner_id, title, filename, metadata),
    )
    conn.commit()
    
    return