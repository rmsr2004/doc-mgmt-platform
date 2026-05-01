import io
import pytest
from unittest.mock import patch
from werkzeug.datastructures import FileStorage

from app.components.input_validation_filter.file_validator import (
    validate_file,
    _validate_file_extension,
    _validate_mime_type,
    _extract_extension,
)

def make_file(filename: str, content: bytes = b"dummy content") -> FileStorage:
    return FileStorage(stream=io.BytesIO(content), filename=filename)

def test_extract_extension_normal():
    assert _extract_extension("document.pdf") == "pdf"

def test_extract_extension_uppercase():
    assert _extract_extension("IMAGE.JPG") == "jpg"

def test_extract_extension_no_dot():
    assert _extract_extension("nodotfile") == ""

def test_extract_extension_multiple_dots():
    assert _extract_extension("archive.tar.gz") == "gz"

def test_extension_pdf_valid():
    assert _validate_file_extension(make_file("report.pdf")) is True

def test_extension_docx_valid():
    assert _validate_file_extension(make_file("notes.docx")) is True

def test_extension_exe_invalid():
    assert _validate_file_extension(make_file("malware.exe")) is False

def test_extension_no_extension_invalid():
    assert _validate_file_extension(make_file("nodotfile")) is False

def test_extension_uppercase_valid():
    assert _validate_file_extension(make_file("IMAGE.PNG")) is True

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/pdf")
def test_mime_pdf_valid(mock_magic):
    assert _validate_mime_type(make_file("doc.pdf")) is True

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="image/png")
def test_mime_png_valid(mock_magic):
    assert _validate_mime_type(make_file("img.png")) is True

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/x-php")
def test_mime_php_invalid(mock_magic):
    assert _validate_mime_type(make_file("shell.php")) is False

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/pdf")
def test_mime_stream_is_reset_after_read(mock_magic):
    content = b"some file content"
    file = make_file("doc.pdf", content=content)
    _validate_mime_type(file)
    assert file.stream.read() == content

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/pdf")
def test_validate_file_success(mock_magic):
    file = make_file("report.pdf", content=b"pdf content")
    result = validate_file(file)
    assert not result.is_failure()
    assert result.value == file

def test_validate_file_none():
    result = validate_file(None)
    assert result.is_failure()
    assert result.error.http_code == 400

def test_validate_file_empty_filename():
    file = make_file("")
    result = validate_file(file)
    assert result.is_failure()
    assert result.error.http_code == 400

def test_validate_file_invalid_extension():
    file = make_file("virus.exe", content=b"content")
    result = validate_file(file)
    assert result.is_failure()
    assert result.error.http_code == 400
    assert "extension" in result.error.message.lower()

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/x-php")
def test_validate_file_invalid_mime(mock_magic):
    file = make_file("doc.pdf", content=b"<?php echo 1; ?>")
    result = validate_file(file)
    assert result.is_failure()
    assert "MIME" in result.error.message

@patch("app.components.input_validation_filter.file_validator.magic.from_buffer", return_value="application/pdf")
def test_validate_file_valid_mime_invalid_extension(mock_magic):
    file = make_file("virus.exe", content=b"pdf bytes")
    result = validate_file(file)
    assert result.is_failure()
    assert "extension" in result.error.message.lower()