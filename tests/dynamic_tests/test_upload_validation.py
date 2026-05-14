import io
import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

_PDF_MAGIC = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
_PHP_CONTENT = b"<?php echo 'hello'; ?>"


def _csrf_token(html: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        html,
    )
    return match.group(1) if match else ""


def _login_as(username: str, password: str) -> requests.Session:
    session = requests.Session()
    session.verify = False
    login_page = session.get(f"{BASE_URL}/login")
    csrf = _csrf_token(login_page.text)
    session.post(
        f"{BASE_URL}/login",
        data={"username": username, "password": password, "csrf_token": csrf},
        allow_redirects=True,
    )
    return session


def _upload(
    session: requests.Session,
    filename: str | None,
    content: bytes | None,
    content_type: str,
    title: str = "Test",
) -> requests.Response:
    docs_page = session.get(f"{BASE_URL}/documents")
    csrf = _csrf_token(docs_page.text)
    kwargs: dict = {"data": {"title": title, "csrf_token": csrf}, "allow_redirects": True}
    if filename is not None:
        kwargs["files"] = {"document": (filename, io.BytesIO(content), content_type)}
    return session.post(f"{BASE_URL}/documents/upload", **kwargs)


def test_upload_valid_pdf():
    """Valid PDF upload should redirect to /documents?uploaded=<title>."""
    session = _login_as("alice", "tth1mJj5?£58")
    response = _upload(session, "report.pdf", _PDF_MAGIC, "application/pdf", title="ValidPDF")
    assert response.status_code == 200
    assert "uploaded=" in response.url


def test_upload_exe_rejected():
    """Executable upload should be rejected and redirected without uploaded= param."""
    session = _login_as("alice", "tth1mJj5?£58")
    response = _upload(session, "malware.exe", b"MZ\x90\x00\x03\x00", "application/octet-stream")
    assert response.status_code == 200
    assert "uploaded=" not in response.url
    assert "flash error" in response.text or "Invalid file extension" in response.text


def test_upload_no_file_rejected():
    """POST with no file attached should be rejected."""
    session = _login_as("alice", "tth1mJj5?£58")
    response = _upload(session, None, None, "", title="NoFile")
    assert response.status_code == 200
    assert "uploaded=" not in response.url
    assert "flash error" in response.text or "No file provided" in response.text


def test_upload_empty_file_rejected():
    """Zero-byte file should be rejected."""
    session = _login_as("alice", "tth1mJj5?£58")
    response = _upload(session, "empty.pdf", b"", "application/pdf")
    assert response.status_code == 200
    assert "uploaded=" not in response.url
    assert "flash error" in response.text or "File must not be empty" in response.text


def test_upload_mismatched_mime_rejected():
    """File with .pdf extension but PHP content should be rejected by MIME check."""
    session = _login_as("alice", "tth1mJj5?£58")
    response = _upload(session, "doc.pdf", _PHP_CONTENT, "application/pdf")
    assert response.status_code == 200
    assert "uploaded=" not in response.url
    assert "flash error" in response.text or "Invalid MIME type" in response.text
