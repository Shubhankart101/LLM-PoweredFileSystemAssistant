"""
test_fs_tools.py - Unit test suite for fs_tools.py

Covers:
- list_files (listing, extension filtering, nonexistent dirs, name/size/modified date keys)
- read_file (PDF, DOCX, TXT, missing files, metadata verification)
- write_file (writing, automatic parent directory creation, status reporting)
- search_in_file (case-insensitivity, context window, line_content, non-matches, empty keywords)
"""

import os
import shutil
from pathlib import Path
import pytest
import fs_tools

TEST_DIR = Path(__file__).resolve().parent / "temp_test_sandbox"
RESUMES_DIR = Path(__file__).resolve().parent.parent / "resumes"


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Create and clean up temporary test sandbox."""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)


class TestListFiles:
    def test_list_all_files(self):
        files = fs_tools.list_files(str(RESUMES_DIR))
        assert len(files) >= 8
        for f in files:
            # Check exact keys from assignment prompt: (name, size, modified date)
            assert "name" in f
            assert "size" in f
            assert "modified_date" in f
            # Also check helper keys
            assert "filepath" in f
            assert "extension" in f
            assert "size_bytes" in f
            assert "size_kb" in f
            assert f["size"] > 0

    def test_filter_by_extension_with_dot(self):
        pdf_files = fs_tools.list_files(str(RESUMES_DIR), extension=".pdf")
        assert len(pdf_files) == 3
        assert all(f["extension"] == ".pdf" for f in pdf_files)

    def test_filter_by_extension_without_dot(self):
        docx_files = fs_tools.list_files(str(RESUMES_DIR), extension="docx")
        assert len(docx_files) == 3
        assert all(f["extension"] == ".docx" for f in docx_files)

    def test_filter_txt_files(self):
        txt_files = fs_tools.list_files(str(RESUMES_DIR), extension=".txt")
        assert len(txt_files) == 2
        assert all(f["extension"] == ".txt" for f in txt_files)

    def test_nonexistent_directory(self):
        files = fs_tools.list_files("nonexistent_directory_xyz")
        assert files == []


class TestReadFile:
    def test_read_pdf_file(self):
        pdf_path = RESUMES_DIR / "resume_john_doe.pdf"
        result = fs_tools.read_file(str(pdf_path))
        assert result["success"] is True
        assert result["filename"] == "resume_john_doe.pdf"
        assert result["extension"] == ".pdf"
        assert "John Doe" in result["content"]
        assert "Python" in result["content"]
        assert result["metadata"]["page_count"] >= 1
        assert result["metadata"]["size"] > 0
        assert "modified_date" in result["metadata"]

    def test_read_docx_file(self):
        docx_path = RESUMES_DIR / "resume_bob_kumar.docx"
        result = fs_tools.read_file(str(docx_path))
        assert result["success"] is True
        assert result["filename"] == "resume_bob_kumar.docx"
        assert result["extension"] == ".docx"
        assert "Bob Kumar" in result["content"]
        assert "React" in result["content"]
        assert result["metadata"]["paragraph_count"] > 0

    def test_read_txt_file(self):
        txt_path = RESUMES_DIR / "resume_david_wilson.txt"
        result = fs_tools.read_file(str(txt_path))
        assert result["success"] is True
        assert result["filename"] == "resume_david_wilson.txt"
        assert result["extension"] == ".txt"
        assert "David Wilson" in result["content"]
        assert "DevOps" in result["content"]
        assert result["metadata"]["line_count"] > 0

    def test_read_nonexistent_file(self):
        result = fs_tools.read_file("nonexistent_file.pdf")
        assert result["success"] is False
        assert result["error"] is not None
        assert "does not exist" in result["error"]


class TestWriteFile:
    def test_write_and_auto_create_directories(self):
        target = TEST_DIR / "nested" / "sub" / "output.txt"
        content = "Line 1: Automated testing content\nLine 2: System generated."
        result = fs_tools.write_file(str(target), content)

        assert result["success"] is True
        assert result["status"] == "success"
        assert target.exists()
        assert target.read_text(encoding="utf-8") == content
        assert result["bytes_written"] == len(content.encode("utf-8"))

    def test_overwrite_existing_file(self):
        target = TEST_DIR / "overwrite_test.txt"
        fs_tools.write_file(str(target), "Initial text")
        result = fs_tools.write_file(str(target), "Updated text")
        assert result["success"] is True
        assert result["status"] == "success"
        assert target.read_text(encoding="utf-8") == "Updated text"


class TestSearchInFile:
    def test_case_insensitive_search(self):
        pdf_path = RESUMES_DIR / "resume_john_doe.pdf"

        # Search with lowercase
        res_lower = fs_tools.search_in_file(str(pdf_path), "python")
        assert res_lower["success"] is True
        assert res_lower["matches_count"] >= 3

        # Search with uppercase
        res_upper = fs_tools.search_in_file(str(pdf_path), "PYTHON")
        assert res_upper["success"] is True
        assert res_upper["matches_count"] == res_lower["matches_count"]

    def test_search_context_window(self):
        txt_path = RESUMES_DIR / "resume_david_wilson.txt"
        res = fs_tools.search_in_file(str(txt_path), "Kubernetes", context_lines=2)
        assert res["success"] is True
        assert res["matches_count"] >= 1
        first_match = res["matches"][0]
        assert "line_number" in first_match
        assert "line_content" in first_match
        assert "line_text" in first_match
        assert "context" in first_match
        assert "Kubernetes" in first_match["context"]

    def test_search_nonexistent_keyword(self):
        pdf_path = RESUMES_DIR / "resume_john_doe.pdf"
        res = fs_tools.search_in_file(str(pdf_path), "NonExistentKeywordXYZ123")
        assert res["success"] is True
        assert res["matches_count"] == 0
        assert res["matches"] == []

    def test_search_empty_keyword(self):
        pdf_path = RESUMES_DIR / "resume_john_doe.pdf"
        res = fs_tools.search_in_file(str(pdf_path), "   ")
        assert res["success"] is False
        assert "cannot be empty" in res["error"]
