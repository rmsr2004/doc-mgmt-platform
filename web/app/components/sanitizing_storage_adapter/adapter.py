import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from app.shared.result.Result import Result, Error
from app.config import UPLOAD_FOLDER

def sanitize_file(filename: str):
    if not filename or not filename.strip():
        return Result.fail(Error("Filename cannot be empty", 400))

    safe_filename = secure_filename(filename)

    if not safe_filename:
        return Result.fail(Error("Filename is not valid after sanitization", 400))

    uuid_filename = _build_uuid_filename(safe_filename)

    path_result = _resolve_safe_path(uuid_filename)
    if not path_result.success:
        return Result.fail(path_result.error)

    return Result.ok((uuid_filename, safe_filename, path_result.value))

def _build_uuid_filename(filename: str) -> str:
    ext = _extract_extension(filename)
    return f"{uuid.uuid4().hex}{ext}"

def _resolve_safe_path(uuid_filename: str):
    upload_root = Path(UPLOAD_FOLDER).resolve()
    candidate = (upload_root / uuid_filename).resolve()
    
    if not str(candidate).startswith(str(upload_root) + os.sep):
        return Result.fail(Error("Path traversal attempt detected", 400))

    return Result.ok(candidate)
    
def _extract_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()