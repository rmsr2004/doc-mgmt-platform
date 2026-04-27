import app.components.dal.documents as documents
from app.shared.result.Result import Result, Error

def get_document_details(document_id) -> Result:
    row = documents.get_document_details(document_id)
    
    # error from database
    if type(row) is Error:
        return Result.fail(row)
    
    if not row:
        return Result.fail(Error(message="Document not found"))
    
    document = {
        "id": row['id'],
        "owner_id": row['owner_id'],
        "title": row['title'],
        "filename": row['filename'],
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

def upload_document(owner_id, title, filename, metadata) -> Result:
    result = documents.upload_document(owner_id, title, filename, metadata)
    
    # error from database
    if type(result) is Error:
        return Result.fail(result)
    
    return Result.ok(None)
