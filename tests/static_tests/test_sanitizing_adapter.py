# tests/api_tests/test_sanitizing_adapter.py
"""
Tests for SR-10 / AD-03b: Sanitizing Storage Adapter.
Unit-style tests that exercise the adapter module directly.
"""
import pytest
from unittest.mock import patch
from pathlib import Path

FAKE_UPLOAD_FOLDER = "/fake/uploads"

@pytest.fixture(autouse=True)
def patch_upload_folder():
    with patch(
        "app.components.sanitizing_storage_adapter.adapter.UPLOAD_FOLDER",
        FAKE_UPLOAD_FOLDER,
    ):
        yield


from app.components.sanitizing_storage_adapter.adapter import (
    sanitize_file,
    _build_uuid_filename,
    _extract_extension,
    _resolve_safe_path,
)


# ---------------------------------------------------------------------------
# _extract_extension
# ---------------------------------------------------------------------------

class TestExtractExtension:
    def test_common_extension(self):
        assert _extract_extension("report.pdf") == ".pdf"

    def test_uppercase_normalised_to_lowercase(self):
        assert _extract_extension("IMAGE.PNG") == ".png"

    def test_no_extension_returns_empty(self):
        assert _extract_extension("noext") == ""

    def test_multiple_dots_takes_last(self):
        assert _extract_extension("archive.tar.gz") == ".gz"

    def test_mixed_case_extension(self):
        assert _extract_extension("document.DOCX") == ".docx"


# ---------------------------------------------------------------------------
# _build_uuid_filename
# ---------------------------------------------------------------------------

class TestBuildUuidFilename:
    def test_produces_uuid_hex_with_extension(self):
        result = _build_uuid_filename("document.pdf")
        assert result.endswith(".pdf")
        assert len(result) == 36  # 32 hex + '.pdf'

    def test_no_extension_returns_32_chars(self):
        result = _build_uuid_filename("noext")
        assert len(result) == 32

    def test_two_calls_produce_different_names(self):
        a = _build_uuid_filename("file.txt")
        b = _build_uuid_filename("file.txt")
        assert a != b

    def test_uuid_contains_only_hex_and_dot(self):
        result = _build_uuid_filename("file.pdf")
        name, ext = result[:-4], result[-4:]
        assert all(c in "0123456789abcdef" for c in name)
        assert ext == ".pdf"


# ---------------------------------------------------------------------------
# _resolve_safe_path
# ---------------------------------------------------------------------------

class TestResolveSafePath:
    def test_valid_filename_returns_ok(self):
        result = _resolve_safe_path("abc123.pdf")
        assert result.success
        assert str(result.value).startswith(FAKE_UPLOAD_FOLDER)

    def test_resolved_path_contains_filename(self):
        result = _resolve_safe_path("abc123.pdf")
        assert result.success
        assert "abc123.pdf" in str(result.value)

    def test_path_traversal_blocked(self):
        result = _resolve_safe_path("../etc/passwd")
        assert not result.success
        assert result.error.http_code == 400

    def test_absolute_path_blocked(self):
        result = _resolve_safe_path("/etc/passwd")
        assert not result.success
        assert result.error.http_code == 400


# ------------------------
# sanitize_file
# -----------------------

class TestSanitizeFile:

    # --- happy path ---

    def test_valid_filename_returns_ok(self):
        result = sanitize_file("report.pdf")
        assert result.success
        uuid_filename, original_filename, safe_path = result.value
        assert uuid_filename.endswith(".pdf")
        assert len(uuid_filename) == 36
        assert original_filename == "report.pdf"
        assert isinstance(safe_path, Path)

    def test_original_filename_preserved(self):
        result = sanitize_file("Relatório Final 2025.docx")
        assert result.success
        _, original_filename, _ = result.value
        assert original_filename == "Relatorio_Final_2025.docx"

    def test_uuid_filename_differs_from_original(self):
        result = sanitize_file("secret.pdf")
        assert result.success
        uuid_filename, original_filename, _ = result.value
        assert uuid_filename != original_filename

    def test_safe_path_inside_upload_folder(self):
        result = sanitize_file("document.pdf")
        assert result.success
        _, _, safe_path = result.value
        assert str(safe_path).startswith(FAKE_UPLOAD_FOLDER)

    def test_extension_preserved_for_all_allowed_types(self):
        for ext in ["pdf", "docx", "txt", "png", "jpg", "pptx"]:
            result = sanitize_file(f"file.{ext}")
            assert result.success
            uuid_filename, _, _ = result.value
            assert uuid_filename.endswith(f".{ext}")

    # --- path traversal ---

    def test_unix_traversal_sanitised(self):
        """'../../etc/passwd.pdf' — secure_filename remove os '../'."""
        result = sanitize_file("../../etc/passwd.pdf")
        assert result.success
        uuid_filename, _, safe_path = result.value
        assert ".." not in uuid_filename
        assert "/" not in uuid_filename
        assert str(safe_path).startswith(FAKE_UPLOAD_FOLDER)

    def test_windows_backslash_traversal_sanitised(self):
        result = sanitize_file("..\\..\\windows\\cmd.exe.pdf")
        assert result.success
        uuid_filename, _, _ = result.value
        assert ".." not in uuid_filename
        assert "\\" not in uuid_filename

    def test_url_encoded_traversal_sanitised(self):
        result = sanitize_file("%2e%2e%2fetc%2fpasswd.pdf")
        if result.success:
            uuid_filename, _, _ = result.value
            assert ".." not in uuid_filename
            assert "/" not in uuid_filename
        else:
            assert result.error.http_code == 400

    def test_null_byte_sanitised(self):
        result = sanitize_file("shell.php\x00.pdf")
        if result.success:
            uuid_filename, _, _ = result.value
            assert "\x00" not in uuid_filename
        else:
            assert result.error.http_code == 400

    # --- invalid filenames — must fail with 400 ---

    def test_pure_dots_blocked(self):
        result = sanitize_file("...")
        assert not result.success
        assert result.error.http_code == 400

    def test_only_slashes_blocked(self):
        result = sanitize_file("///")
        assert not result.success
        assert result.error.http_code == 400

    def test_empty_string_blocked(self):
        result = sanitize_file("")
        assert not result.success
        assert result.error.http_code == 400

    def test_whitespace_only_blocked(self):
        result = sanitize_file("   ")
        assert not result.success
        assert result.error.http_code == 400

    def test_only_dots_and_slashes_blocked(self):
        result = sanitize_file("../../")
        assert not result.success
        assert result.error.http_code == 400
