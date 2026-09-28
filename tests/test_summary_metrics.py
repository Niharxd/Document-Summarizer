"""Summary metric generation and Gradio integration tests (Cohere is mocked)."""
import json
from unittest.mock import patch

from summarizer import summary_metrics
from app import gradio_app


def test_summary_word_count_and_document_ratio():
    record = summary_metrics.build_summary_metrics(
        "report.txt", "technical", "one two three four", "one two", 1.25
    )

    assert record["summary_length"] == 2
    assert record["summary_length_to_document_length_ratio"] == 0.5
    assert record["document_length"] == 4


def test_processing_time_is_recorded():
    record = summary_metrics.build_summary_metrics(
        "report.txt", "legal", "four words in document", "short result", 2.3456789
    )

    assert record["processing_time_seconds"] == 2.345679


def test_metrics_are_saved_as_reusable_json_lines(monkeypatch, tmp_path):
    target = tmp_path / "summary_metrics.jsonl"
    monkeypatch.setattr(summary_metrics, "SUMMARY_METRICS_FILE", target)
    record = summary_metrics.build_summary_metrics(
        "report.txt", "medical", "source document", "summary", 0.75
    )

    summary_metrics.save_summary_metrics(record)

    assert json.loads(target.read_text(encoding="utf-8").splitlines()[0]) == record


def test_normal_gradio_summary_flow_records_metrics(tmp_path):
    upload = tmp_path / "sample.txt"
    upload.touch()
    with patch.object(gradio_app, "extract_text", return_value="one two three four"), \
            patch.object(gradio_app, "generate_summary", return_value="short summary") as cohere, \
            patch.object(gradio_app, "save_summary_metrics") as save, \
            patch.object(gradio_app.time, "perf_counter", side_effect=[10.0, 12.5]):
        displayed_summary, record = gradio_app.summarize_uploaded_document(upload, "legal")

    cohere.assert_called_once_with("one two three four", "legal")
    assert displayed_summary == "short summary"
    assert record["document_name"] == "sample.txt"
    assert record["summary_length"] == 2
    assert record["summary_length_to_document_length_ratio"] == 0.5
    assert record["processing_time_seconds"] == 2.5
    save.assert_called_once_with(record)
