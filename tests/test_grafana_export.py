"""Grafana export tests use temporary CSV/JSONL input and mocked Parquet rows."""
import csv
import json

from grafana import export_metrics as exporter


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_exports_aggregated_metrics_from_temporary_sources(monkeypatch, tmp_path):
    etl_path = tmp_path / "etl_output.parquet"
    etl_path.mkdir()
    summary_path = tmp_path / "summary_metrics.jsonl"
    summary_path.write_text("\n".join([
        json.dumps({
            "timestamp": "2026-09-28T10:00:00+00:00", "document_name": "a.txt",
            "domain": "legal", "summary": "short useful summary", "document_length": 12,
            "summary_length": 3, "processing_time_seconds": 2.0,
        }),
        json.dumps({
            "timestamp": "2026-09-28T12:00:00+00:00", "document_name": "b.txt",
            "domain": "legal", "summary": "another summary", "document_length": 10,
            "summary_length": 2, "processing_time_seconds": 4.0,
        }),
    ]), encoding="utf-8")
    feedback_path = tmp_path / "feedback.csv"
    with feedback_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["timestamp", "document_name", "domain", "rating"])
        writer.writeheader()
        writer.writerows([
            {"timestamp": "2026-09-28T10:00:00+00:00", "document_name": "a.txt", "domain": "legal", "rating": "4"},
            {"timestamp": "2026-09-28T11:00:00+00:00", "document_name": "b.txt", "domain": "legal", "rating": "2"},
        ])

    monkeypatch.setattr(exporter, "_read_parquet_records", lambda _: [
        {"processed_at": "2026-09-28T09:00:00Z", "domain": "legal", "coherence_score": 0.5},
        {"processed_at": "2026-09-28T09:00:00Z", "domain": "legal", "coherence_score": 0.9},
        {"processed_at": "2026-09-29T09:00:00Z", "domain": "medical", "coherence_score": 0.6},
    ])
    outputs = exporter.export_metrics(
        etl_path=etl_path,
        summary_metrics_path=summary_path,
        feedback_path=feedback_path,
        output_dir=tmp_path / "grafana",
    )

    assert set(outputs) == set(exporter.CSV_SCHEMAS)
    docs = _read_csv(outputs["documents_per_day.csv"])
    assert docs == [
        {"date": "2026-09-28", "documents_processed": "2"},
        {"date": "2026-09-29", "documents_processed": "1"},
    ]
    processing = _read_csv(outputs["processing_time.csv"])
    assert processing[0]["average_processing_time_seconds"] == "3.0"
    assert processing[0]["operations"] == "2"
    lengths = _read_csv(outputs["summary_lengths.csv"])
    assert lengths[0]["average_summary_length"] == "2.5"
    assert lengths[0]["average_summary_length_to_document_length_ratio"] == "0.225"
    ratings = _read_csv(outputs["ratings_by_domain.csv"])
    assert ratings == [{"domain": "legal", "average_rating": "3.0", "feedback_count": "2"}]
    coherence = _read_csv(outputs["coherence_by_domain.csv"])
    assert coherence[0]["average_coherence_score"] == "0.7"
    assert coherence[0]["documents"] == "2"


def test_missing_feedback_and_summaries_still_write_headers(monkeypatch, tmp_path):
    etl_path = tmp_path / "etl_output.parquet"
    etl_path.mkdir()
    monkeypatch.setattr(exporter, "_read_parquet_records", lambda _: [])

    outputs = exporter.export_metrics(
        etl_path=etl_path,
        summary_metrics_path=tmp_path / "missing.jsonl",
        feedback_path=tmp_path / "missing.csv",
        output_dir=tmp_path / "grafana",
    )

    for filename, fields in exporter.CSV_SCHEMAS.items():
        with outputs[filename].open(newline="", encoding="utf-8") as stream:
            rows = list(csv.reader(stream))
        assert rows == [list(fields)]


def test_summary_ratio_is_recomputed_from_word_counts(monkeypatch, tmp_path):
    etl_path = tmp_path / "etl_output.parquet"
    etl_path.mkdir()
    summary_path = tmp_path / "summary_metrics.jsonl"
    summary_path.write_text(json.dumps({
        "timestamp": "2026-09-28T10:00:00Z", "domain": "technical",
        "summary": "one two three", "document_length": 8,
        "summary_length": 999, "processing_time_seconds": 1,
    }), encoding="utf-8")
    monkeypatch.setattr(exporter, "_read_parquet_records", lambda _: [])

    outputs = exporter.export_metrics(
        etl_path=etl_path,
        summary_metrics_path=summary_path,
        feedback_path=tmp_path / "missing.csv",
        output_dir=tmp_path / "grafana",
    )

    row = _read_csv(outputs["summary_lengths.csv"])[0]
    assert row["average_summary_length"] == "3.0"
    assert row["average_summary_length_to_document_length_ratio"] == "0.375"
