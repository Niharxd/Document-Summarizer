"""
Document ingestion utilities.

Discovers supported files under a root directory, extracts plain text from
TXT / PDF / DOCX, and returns a consistent document record per file.

Domain is inferred from the immediate parent folder name
(e.g. data/raw/legal/foo.txt  ->  domain = "legal").
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from docx import Document

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(
        page.extract_text() or "" for page in reader.pages
    )


def extract_text_from_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return extract_text_from_txt(path)
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")


# ── Discovery ─────────────────────────────────────────────────────────────────

def discover_documents(root: str | Path) -> list[Path]:
    """Return all supported files found recursively under *root*."""
    root = Path(root)
    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


# ── Domain detection ──────────────────────────────────────────────────────────

def detect_domain(path: Path, root: Path) -> str:
    """
    Infer domain from the first path component below *root*.
    e.g. root=data/raw, path=data/raw/legal/foo.txt  ->  'legal'
    Falls back to 'unknown' if the file sits directly in root.
    """
    try:
        relative = path.relative_to(root)
        return relative.parts[0] if len(relative.parts) > 1 else "unknown"
    except ValueError:
        return "unknown"


# ── Main loader ───────────────────────────────────────────────────────────────

def load_document(path: Path, root: Path) -> dict[str, Any]:
    """Load a single document and return a structured record."""
    return {
        "document_id": str(uuid.uuid5(uuid.NAMESPACE_URL, str(path.resolve()))),
        "filename": path.name,
        "file_type": path.suffix.lower().lstrip("."),
        "domain": detect_domain(path, root),
        "text": extract_text(path),
    }


def load_all_documents(root: str | Path) -> list[dict[str, Any]]:
    """Discover and load all supported documents under *root*."""
    root = Path(root)
    return [load_document(p, root) for p in discover_documents(root)]
