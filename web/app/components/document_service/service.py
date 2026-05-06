import app.components.dal.documents as documents
from app.shared.result.Result import Result, Error

def get_document_details(document_id) -> Result:
    row = documents.get_document_details(document_id)
    
    # error from database
    if type(row) is Error:
        return Result.fail(row)
    
    if not row:
        return Result.fail(Error(message="Document not found", http_code=404))
    
    document = {
        "id": row['id'],
        "owner_id": row['owner_id'],
        "title": row['title'],
        "filename": row['filename'],
        "uuid_filename": row['uuid_filename'],
        "metadata": row['metadata'],
    }
    
    return Result.ok(document)

def get_documents_for_user(owner_id) -> Result:
    rows = documents.get_documents_for_user(owner_id)
    
    # error from database
    if type(rows) is Error:
        return Result.fail(rows)
    
    documents_list = [
        {
            "id": d['id'],
            "title": d['title'],
            "filename": d['filename'],
            "uploaded_at": d['uploaded_at'],
        }
        for d in rows
    ]
    
    return Result.ok(documents_list)

def upload_document(owner_id, title, filename, uuid_filename, metadata) -> Result:
    result = documents.upload_document(owner_id, title, filename, uuid_filename, metadata)
    
    # error from database
    if type(result) is Error:
        return Result.fail(result)
    
    return Result.ok(None)

def get_document_by_uuid(uuid_filename: str) -> Result:
    row = documents.get_document_by_uuid(uuid_filename)

    if type(row) is Error:
        return Result.fail(row)

    if not row:
        return Result.fail(Error(message="Document not found", http_code=404))

    return Result.ok({"id": row["id"]})

def share_document(document_id, target_user_id) -> Result:
    row = documents.share_document(document_id, target_user_id)
    
    if type(row) is Error:
        return Result.fail(row)
    
    return Result.ok(None)

def get_shared_documents_for_user(user_id) -> Result:
    rows = documents.get_shared_documents_for_user(user_id)
    
    # error from database
    if type(rows) is Error:
        return Result.fail(rows)

    shared_docs = [
        {
            "id": d['id'],
            "title": d['title'],
            "filename": d['filename'],
            "metadata": d['metadata'],
            "uploaded_at": d['uploaded_at'],
            "owner_username": d['owner_username']
        }
        for d in rows
    ]

    return Result.ok(shared_docs)