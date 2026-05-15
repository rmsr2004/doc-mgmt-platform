from flask import session

from app.shared.result.Result import Result, Error
from app.components.dal import documents

def verify_document_access(document_id: int, user_id: int) -> Result:
    doc = documents.get_document_owner(document_id)

    if not doc:
        return Result.fail(Error(message="Document not found", http_code=404))

    if type(doc) is Error:
        return Result.fail(doc)

    if doc['owner_id'] == user_id:
        return Result.ok(None)

    shared = documents.get_document_share(document_id, user_id)

    if type(shared) is Error:
        return Result.fail(shared)

    if shared:
        return Result.ok(None)

    return Result.fail(Error(message="You do not have permission to access this document", http_code=403))

def verify_if_admin(user_id: int) -> bool:
    return session.get("is_admin")