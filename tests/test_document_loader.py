"""Tests for app/document_loader.py"""
import sys
from pathlib import Path

# Ensure project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject, DecodedStreamObject
from docx import Document as DocxDocument

from app.document_loader import (
    extract_text_from_txt,
    extract_text_from_pdf,
    extract_text_from_docx,
    discover_documents,
    detect_domain,
    load_document,
    load_all_documents,
)

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_pdf(path: Path, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 40 750 Td ({safe}) Tj ET".encode()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
    })
    obj = DecodedStreamObject()
    obj.set_data(stream)
    page[NameObject("/Contents")] = obj
    with open(path, "wb") as f:
        writer.write(f)


def make_docx(path: Path, text: str) -> None:
    doc = DocxDocument()
    doc.add_paragraph(text)
    doc.save(path)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_corpus(tmp_path):
    """Create a minimal temporary corpus with one file per type."""
    (tmp_path / "legal").mkdir()
    (tmp_path / "medical").mkdir()

    txt_file = tmp_path / "legal" / "sample.txt"
    txt_file.write_text("Hello from TXT", encoding="utf-8")

    pdf_file = tmp_path / "legal" / "sample.pdf"
    make_pdf(pdf_file, "Hello from PDF")

    docx_file = tmp_path / "medical" / "sample.docx"
    make_docx(docx_file, "Hello from DOCX")

    return tmp_path


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_txt_extraction(tmp_corpus):
    path = tmp_corpus / "legal" / "sample.txt"
    text = extract_text_from_txt(path)
    assert "Hello from TXT" in text


def test_pdf_extraction(tmp_corpus):
    path = tmp_corpus / "legal" / "sample.pdf"
    text = extract_text_from_pdf(path)
    assert "Hello from PDF" in text


def test_docx_extraction(tmp_corpus):
    path = tmp_corpus / "medical" / "sample.docx"
    text = extract_text_from_docx(path)
    assert "Hello from DOCX" in text


def test_discover_documents(tmp_corpus):
    found = discover_documents(tmp_corpus)
    names = {p.name for p in found}
    assert "sample.txt" in names
    assert "sample.pdf" in names
    assert "sample.docx" in names
    assert len(found) == 3


def test_domain_detection(tmp_corpus):
    txt_path = tmp_corpus / "legal" / "sample.txt"
    docx_path = tmp_corpus / "medical" / "sample.docx"
    assert detect_domain(txt_path, tmp_corpus) == "legal"
    assert detect_domain(docx_path, tmp_corpus) == "medical"


def test_load_document_structure(tmp_corpus):
    path = tmp_corpus / "legal" / "sample.txt"
    record = load_document(path, tmp_corpus)
    assert set(record.keys()) >= {"document_id", "filename", "file_type", "domain", "text"}
    assert record["filename"] == "sample.txt"
    assert record["file_type"] == "txt"
    assert record["domain"] == "legal"
    assert len(record["document_id"]) > 0


def test_load_all_documents(tmp_corpus):
    records = load_all_documents(tmp_corpus)
    assert len(records) == 3
    domains = {r["domain"] for r in records}
    assert "legal" in domains
    assert "medical" in domains


def test_real_corpus_loads():
    """Smoke test: load the actual sample corpus and verify basic structure."""
    records = load_all_documents(RAW_DIR)
    # Exclude the generator script itself
    doc_records = [r for r in records if r["file_type"] in {"txt", "pdf", "docx"}]
    assert len(doc_records) >= 9
    domains = {r["domain"] for r in doc_records}
    assert domains >= {"legal", "medical", "technical"}
    for r in doc_records:
        assert len(r["text"].strip()) > 0, f"Empty text in {r['filename']}"
