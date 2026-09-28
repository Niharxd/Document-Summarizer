"""Tests for the Gradio summarization callback; all external work is mocked."""
from pathlib import Path
from unittest.mock import patch

from app import gradio_app


def test_callback_extracts_and_summarizes_with_selected_domain(tmp_path):
    upload = tmp_path / "sample.txt"
    upload.touch()

    with patch.object(gradio_app, "extract_text", return_value="source document") as extraction, \
            patch.object(gradio_app, "generate_summary", return_value="short summary") as summary, \
            patch.object(gradio_app, "save_summary_metrics"):
        result = gradio_app.summarize_uploaded_document(str(upload), "medical")

    assert result[0] == "short summary"
    assert result[1]["summary_length"] == 2
    assert result[1]["summary_length_to_document_length_ratio"] == 1.0
    extraction.assert_called_once_with(Path(upload))
    summary.assert_called_once_with("source document", "medical")


def test_callback_rejects_empty_extracted_text(tmp_path):
    with patch.object(gradio_app, "extract_text", return_value="  \n "), \
            patch.object(gradio_app, "generate_summary") as summary:
        result = gradio_app.summarize_uploaded_document(tmp_path / "empty.txt", "legal")

    assert "contains no text" in result[0]
    summary.assert_not_called()


def test_callback_requires_upload():
    with patch.object(gradio_app, "generate_summary") as summary:
        result = gradio_app.summarize_uploaded_document(None, "legal")

    assert "Please upload" in result[0]
    summary.assert_not_called()


def test_callback_reports_extraction_error(tmp_path):
    with patch.object(gradio_app, "extract_text", side_effect=OSError("read failed")):
        result = gradio_app.summarize_uploaded_document(tmp_path / "sample.pdf", "technical")

    assert "Unable to generate summary" in result[0]
    assert "read failed" in result[0]
