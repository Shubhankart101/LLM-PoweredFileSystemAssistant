"""
fs_tools.py - Core File System Tools for LLM Assistant

This module implements structured tools for interacting with files and directories:
1. read_file: Reads resume documents (PDF, DOCX, TXT) with content & metadata extraction.
2. list_files: Lists directory contents with optional extension filtering and metadata.
3. write_file: Writes content to disk, automatically creating missing directories.
4. search_in_file: Performs case-insensitive keyword searches with surrounding context.

Designed for standalone programmatic usage and direct LLM function calling integration.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _format_datetime(ts: float) -> str:
    """Format timestamp into ISO 8601 string."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _read_txt(path: Path) -> tuple[str, dict[str, Any]]:
    """Read a plain text file with encoding fallback and metadata extraction."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    content = ""
    last_err: Optional[Exception] = None

    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read()
            last_err = None
            break
        except UnicodeDecodeError as err:
            last_err = err

    if last_err is not None:
        raise last_err

    lines = content.splitlines()
    words = content.split()
    metadata: dict[str, Any] = {
        "line_count": len(lines),
        "word_count": len(words),
        "character_count": len(content),
    }
    return content, metadata


def _read_pdf(path: Path) -> tuple[str, dict[str, Any]]:
    """Read a PDF file using pypdf and extract text + document metadata."""
    try:
        import pypdf
    except ImportError as exc:
        raise ImportError(
            "pypdf is required to parse PDF files. Install it with `pip install pypdf`."
        ) from exc

    reader = pypdf.PdfReader(str(path))
    page_texts: list[str] = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        page_texts.append(page_text.strip())

    full_text = "\n\n".join(page_texts)

    # Extract PDF metadata if available
    pdf_meta = reader.metadata or {}
    metadata: dict[str, Any] = {
        "page_count": len(reader.pages),
        "word_count": len(full_text.split()),
        "character_count": len(full_text),
        "author": getattr(pdf_meta, "author", None) or str(pdf_meta.get("/Author", "")) or None,
        "title": getattr(pdf_meta, "title", None) or str(pdf_meta.get("/Title", "")) or None,
        "producer": getattr(pdf_meta, "producer", None) or str(pdf_meta.get("/Producer", "")) or None,
    }
    return full_text, metadata


def _read_docx(path: Path) -> tuple[str, dict[str, Any]]:
    """Read a DOCX document using python-docx and extract paragraphs & tables."""
    try:
        import docx
    except ImportError as exc:
        raise ImportError(
            "python-docx is required to parse DOCX files. Install it with `pip install python-docx`."
        ) from exc

    doc = docx.Document(str(path))
    paragraphs: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]

    # Extract tables content if present
    table_texts: list[str] = []
    for table in doc.tables:
        for row in table.rows:
            row_str = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_str:
                table_texts.append(row_str)

    combined_text = "\n".join(paragraphs)
    if table_texts:
        combined_text += "\n\n[Tables Data]:\n" + "\n".join(table_texts)

    core = doc.core_properties
    metadata: dict[str, Any] = {
        "paragraph_count": len(doc.paragraphs),
        "table_count": len(doc.tables),
        "word_count": len(combined_text.split()),
        "character_count": len(combined_text),
        "author": core.author or None,
        "title": core.title or None,
    }
    return combined_text, metadata


def read_file(filepath: str) -> dict[str, Any]:
    """
    Read resume files (PDF, TXT, DOCX), extract text content, and return structured metadata.

    Args:
        filepath (str): Path to the target file.

    Returns:
        dict: A structured dictionary with the following schema:
            - success (bool): True if reading succeeded, False otherwise.
            - filepath (str): Normalized absolute path.
            - filename (str): Base filename.
            - extension (str): Lowercase file extension (e.g. '.pdf', '.docx', '.txt').
            - content (str): Extracted text content.
            - metadata (dict): File stats (size, modified time) + format-specific attributes.
            - error (str | None): Error description if reading failed.
    """
    path = Path(filepath)

    if not path.exists():
        return {
            "success": False,
            "filepath": str(path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "content": "",
            "metadata": {},
            "error": f"File does not exist: '{filepath}'",
        }

    if not path.is_file():
        return {
            "success": False,
            "filepath": str(path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "content": "",
            "metadata": {},
            "error": f"Path is not a regular file: '{filepath}'",
        }

    ext = path.suffix.lower()

    try:
        stat = path.stat()
        file_metadata: dict[str, Any] = {
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified_time": _format_datetime(stat.st_mtime),
        }

        if ext == ".pdf":
            content, specific_meta = _read_pdf(path)
        elif ext == ".docx":
            content, specific_meta = _read_docx(path)
        elif ext in [".txt", ".md", ".json", ".csv", ".log", ""]:
            content, specific_meta = _read_txt(path)
        else:
            # Fallback attempt as text
            try:
                content, specific_meta = _read_txt(path)
            except Exception:
                return {
                    "success": False,
                    "filepath": str(path.resolve()),
                    "filename": path.name,
                    "extension": ext,
                    "content": "",
                    "metadata": file_metadata,
                    "error": f"Unsupported file extension '{ext}'. Supported formats: PDF, DOCX, TXT.",
                }

        file_metadata.update(specific_meta)

        return {
            "success": True,
            "filepath": str(path.resolve()),
            "filename": path.name,
            "extension": ext,
            "content": content,
            "metadata": file_metadata,
            "error": None,
        }

    except Exception as exc:
        return {
            "success": False,
            "filepath": str(path.resolve()) if path.exists() else str(path),
            "filename": path.name,
            "extension": ext,
            "content": "",
            "metadata": {},
            "error": f"Error reading file '{path.name}': {type(exc).__name__}: {str(exc)}",
        }


def list_files(directory: str, extension: Optional[str] = None) -> list[dict[str, Any]]:
    """
    List all files in a directory, optionally filtered by extension, with metadata.

    Args:
        directory (str): Directory path to scan.
        extension (str, optional): Filter by extension, e.g. '.pdf', 'pdf', '.txt'.
                                   Case-insensitive. Defaults to None (all files).

    Returns:
        list[dict]: A list of metadata dicts for matching files. Each dict contains:
            - name (str): File basename.
            - filepath (str): Absolute file path.
            - relative_path (str): Path relative to directory queried.
            - extension (str): File extension in lowercase (e.g. '.pdf').
            - size_bytes (int): File size in bytes.
            - size_kb (float): File size in kilobytes rounded to 2 decimals.
            - modified_time (str): Last modified datetime (YYYY-MM-DD HH:MM:SS).
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    if not dir_path.is_dir():
        return []

    norm_ext: Optional[str] = None
    if extension:
        norm_ext = extension.strip().lower()
        if not norm_ext.startswith("."):
            norm_ext = f".{norm_ext}"

    results: list[dict[str, Any]] = []

    try:
        for entry in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_file():
                if norm_ext is not None and entry.suffix.lower() != norm_ext:
                    continue

                stat = entry.stat()
                results.append({
                    "name": entry.name,
                    "filepath": str(entry.resolve()),
                    "relative_path": str(entry.relative_to(dir_path) if dir_path.is_absolute() else entry),
                    "extension": entry.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified_time": _format_datetime(stat.st_mtime),
                })
    except Exception:
        return []

    return results


def write_file(filepath: str, content: str) -> dict[str, Any]:
    """
    Write content to a file, creating parent directories automatically if needed.

    Args:
        filepath (str): Target destination path.
        content (str): Content string to write (written using UTF-8).

    Returns:
        dict: A structured dictionary containing:
            - success (bool): True if write succeeded, False otherwise.
            - filepath (str): Absolute file path.
            - filename (str): Base filename.
            - bytes_written (int): Count of bytes written.
            - message (str): Human-readable confirmation or error message.
            - error (str | None): Error detail if failed, None otherwise.
    """
    path = Path(filepath)

    try:
        # Create parent directories if they don't already exist
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            bytes_written = f.write(content)

        return {
            "success": True,
            "filepath": str(path.resolve()),
            "filename": path.name,
            "bytes_written": len(content.encode("utf-8")),
            "message": f"Successfully wrote {len(content.encode('utf-8'))} bytes to '{path.name}'",
            "error": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "filepath": str(path.resolve()) if path.parent.exists() else str(path),
            "filename": path.name,
            "bytes_written": 0,
            "message": f"Failed to write file '{path.name}'",
            "error": f"{type(exc).__name__}: {str(exc)}",
        }


def search_in_file(
    filepath: str, keyword: str, context_lines: int = 1
) -> dict[str, Any]:
    """
    Search for a keyword inside a file's content (case-insensitive) and return matches with context.

    Supports PDF, DOCX, and TXT files by reading their parsed text content.

    Args:
        filepath (str): Path to the target file.
        keyword (str): Search term / query (case-insensitive).
        context_lines (int): Number of surrounding lines before and after match. Defaults to 1.

    Returns:
        dict: A structured dictionary containing:
            - success (bool): True if search executed, False if file could not be read.
            - filepath (str): Absolute file path.
            - filename (str): File name.
            - keyword (str): Searched keyword.
            - matches_count (int): Number of matching occurrences.
            - matches (list[dict]): List of match dicts:
                - line_number (int): 1-indexed line number.
                - line_text (str): Exact line where match occurred.
                - context (str): Surrounding lines joined as snippet.
            - error (str | None): Error description if search failed.
    """
    if not keyword or not keyword.strip():
        return {
            "success": False,
            "filepath": str(Path(filepath)),
            "filename": Path(filepath).name,
            "keyword": keyword,
            "matches_count": 0,
            "matches": [],
            "error": "Search keyword cannot be empty.",
        }

    read_result = read_file(filepath)
    if not read_result["success"]:
        return {
            "success": False,
            "filepath": read_result["filepath"],
            "filename": read_result["filename"],
            "keyword": keyword,
            "matches_count": 0,
            "matches": [],
            "error": read_result["error"],
        }

    text = read_result["content"]
    lines = text.splitlines()
    needle = keyword.lower()

    matches: list[dict[str, Any]] = []

    for idx, line in enumerate(lines):
        if needle in line.lower():
            start_idx = max(0, idx - context_lines)
            end_idx = min(len(lines), idx + context_lines + 1)
            context_snippet = "\n".join(lines[start_idx:end_idx])

            matches.append({
                "line_number": idx + 1,
                "line_text": line.strip(),
                "context": context_snippet.strip(),
            })

    return {
        "success": True,
        "filepath": read_result["filepath"],
        "filename": read_result["filename"],
        "keyword": keyword,
        "matches_count": len(matches),
        "matches": matches,
        "error": None,
    }


# ============================================================================
# OpenAI-Compatible Tool Schema Definitions
# ============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read resume documents (PDF, DOCX, TXT) and extract text content "
                "along with file metadata (page count, size, modified time)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path to the file to read (e.g. 'resumes/resume_john_doe.pdf').",
                    }
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List all files in a directory, optionally filtered by extension (.pdf, .docx, .txt), "
                "and return file metadata such as size and last modified date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The directory path to inspect (e.g. 'resumes' or '.').",
                    },
                    "extension": {
                        "type": "string",
                        "description": "Optional file extension filter, e.g. '.pdf', '.docx', '.txt'.",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text content to a destination file. Automatically creates any parent directories "
                "if they do not already exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Destination file path (e.g. 'summaries/summary_john_doe.txt').",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file.",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": (
                "Search for keywords in a file's content (case-insensitive) across PDF, DOCX, or TXT. "
                "Returns matching lines with surrounding context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to search within.",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "The keyword or phrase to search for (e.g. 'Python', 'AWS', 'Docker').",
                    },
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]

# Map tool names to python callable functions
TOOL_MAP = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
}
