import io
import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("APP_BASE_URL", "https://localhost:443")

def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _csrf_token(page_text: str) -> str:
    match = re.search(
        r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
        page_text,
    )
    return match.group(1) if match else ""


def _upload_document(filename: str):
    session = requests.Session()
    session.verify = False

    login_page = session.get(_url("/login"), timeout=10)
    login_csrf = _csrf_token(login_page.text)

    login_response = session.post(
        _url("/login"),
        data={
            "username": "alice",
            "password": "tth1mJj5?£58",
            "csrf_token": login_csrf,
        },
        allow_redirects=False,
        timeout=10,
    )
    assert login_response.status_code in (302, 303)

    documents_page = session.get(_url("/documents"), timeout=10)
    upload_csrf = _csrf_token(documents_page.text)

    upload_response = session.post(
        _url("/documents/upload"),
        data={"title": "Sanitizing Adapter", "csrf_token": upload_csrf},
        files={
            "document": (
                filename,
                io.BytesIO(b"dummy pdf content"),
                "application/pdf",
            ),
        },
        allow_redirects=False,
        timeout=10,
    )

    documents_response = session.get(_url("/documents"), timeout=10)
    return upload_response, documents_response.text.lower()


def test_upload_path_traversal_filename_safe():
    response, response_text = _upload_document("../../etc/passwd.pdf")

    assert response.status_code in (302, 303)
    assert "/documents" in response.headers.get("Location", "")

    assert "../../" not in response_text
    assert "..\\" not in response_text
    assert "passwd.pdf" in response_text or "sanitizing adapter" in response_text


def test_upload_special_chars_filename_accepted():
    response, response_text = _upload_document("Relatório Final.pdf")

    assert response.status_code in (302, 303)
    assert "/documents" in response.headers.get("Location", "")

    assert "erro" not in response_text