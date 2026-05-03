import magic
from werkzeug.datastructures import FileStorage

from app.shared.result.Result import Result, Error
from app.config import MAX_CONTENT_LENGTH

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg'
}

ALLOWED_MIME_TYPES = {
    'text/plain',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'image/png',
    'image/jpeg'
}

def validate_file(file: FileStorage):
    if not file or not file.filename:
        return Result.fail(Error("No file provided", 400))
        
    is_extension_valid = _validate_file_extension(file)
    if not is_extension_valid:
        return Result.fail(Error("Invalid file extension", 400))
    
    is_mime_type_valid = _validate_mime_type(file)
    if not is_mime_type_valid:
        return Result.fail(Error("Invalid MIME type", 400))
    
    return Result.ok(value=file)

def _validate_file_extension(file: FileStorage) -> bool:
    filename = file.filename
    extension = _extract_extension(filename)    
    return extension in ALLOWED_EXTENSIONS

def _validate_mime_type(file: FileStorage) -> bool:
    header = file.stream.read(1024)  # Read the first 1024 bytes to determine MIME type
    file.stream.seek(0)  # Reset the stream position after reading
    
    mime_type = magic.from_buffer(header, mime=True)
    
    return mime_type in ALLOWED_MIME_TYPES


def _extract_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    
    return filename.rsplit('.', 1)[1].lower()