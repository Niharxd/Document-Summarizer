"""Export Grafana-ready CSV aggregates from ETL, summary, and feedback data."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_ETL_PATH = PROCESSED_DIR / "etl_output.parquet"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "summary_metrics.jsonl"
DEFAULT_FEEDBACK_PATH = PROCESSED_DIR / "feedback.csv"
DEFAULT_OUTPUT_DIR = PROCESSED_DIR / "grafana"

CSV_SCHEMAS = {
    "documents_per_day.csv": ("date", "documents_processed"),
    "processing_time.csv": (
        "date", "domain", "average_processing_time_seconds", "operations",
    ),
    "summary_lengths.csv": (
        "date", "domain", "average_document_length", "average_summary_length",
        "average_summary_length_to_document_length_ratio", "summaries",
    ),
    "ratings_by_domain.csv": ("domain", "average_rating", "feedback_count"),
    "coherence_by_domain.csv": ("domain", "average_coherence_score", "documents"),
}


def _read_parquet_records(parquet_path: Path) -> list[dict[str, Any]]:
    """Read ETL Parquet rows using the project's existing PySpark dependency."""
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("DocumentSummarizerGrafanaExport")
        .getOrCreate()
    )
    try:
        rows = spark.read.parquet(str(parquet_path)).collect()
        return [row.asDict(recursive=True) for row in rows]
    finally:
        spark.stop()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                records.append(json.loads(line))
    return records


def _read_feedback(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def _date_key(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return str(value)[:10]


def _word_count(text: Any) -> int:
    return len(text.split()) if isinstance(text, str) else 0


def _write_csv(path: Path, fields: tuple[str, ...], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export_metrics(
    etl_path: str | Path = DEFAULT_ETL_PATH,
    summary_metrics_path: str | Path = DEFAULT_SUMMARY_PATH,
    feedback_path: str | Path = DEFAULT_FEEDBACK_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    """Read the three project data sources and write five Grafana CSV exports."""
    etl_path = Path(etl_path)
    summary_metrics_path = Path(summary_metrics_path)
    feedback_path = Path(feedback_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    etl_rows = _read_parquet_records(etl_path) if etl_path.exists() else []
    summaries = _read_jsonl(summary_metrics_path)
    feedback = _read_feedback(feedback_path)

    counts_by_day: dict[str, int] = defaultdict(int)
    coherence_by_domain: dict[str, list[float]] = defaultdict(list)
    for row in etl_rows:
        day = _date_key(row.get("processed_at"))
        if day:
            counts_by_day[day] += 1
        try:
            coherence = float(row["coherence_score"])
            domain = str(row["domain"])
        except (KeyError, TypeError, ValueError):
            continue
        coherence_by_domain[domain].append(coherence)

    processing_groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    summary_groups: dict[tuple[str, str], list[tuple[int, int, float]]] = defaultdict(list)
    for record in summaries:
        day = _date_key(record.get("timestamp"))
        domain = str(record.get("domain", ""))
        key = (day, domain)
        try:
            processing_groups[key].append(float(record["processing_time_seconds"]))
        except (KeyError, TypeError, ValueError):
            pass

        summary = record.get("summary", "")
        summary_length = _word_count(summary)
        if not summary and record.get("summary_length") is not None:
            try:
                summary_length = int(record["summary_length"])
            except (TypeError, ValueError):
                summary_length = 0
        try:
            document_length = int(record.get("document_length", 0))
        except (TypeError, ValueError):
            document_length = 0
        ratio = round(summary_length / document_length, 4) if document_length else 0.0
        summary_groups[key].append((document_length, summary_length, ratio))

    rating_groups: dict[str, list[float]] = defaultdict(list)
    for record in feedback:
        try:
            rating_groups[str(record["domain"])].append(float(record["rating"]))
        except (KeyError, TypeError, ValueError):
            continue

    processing_rows = [
        {
            "date": day,
            "domain": domain,
            "average_processing_time_seconds": round(fmean(values), 6),
            "operations": len(values),
        }
        for (day, domain), values in sorted(processing_groups.items())
    ]
    summary_rows = []
    for (day, domain), values in sorted(summary_groups.items()):
        summary_rows.append({
            "date": day,
            "domain": domain,
            "average_document_length": round(fmean(v[0] for v in values), 2),
            "average_summary_length": round(fmean(v[1] for v in values), 2),
            "average_summary_length_to_document_length_ratio": round(
                fmean(v[2] for v in values), 4
            ),
            "summaries": len(values),
        })

    rows_by_file = {
        "documents_per_day.csv": [
            {"date": day, "documents_processed": count}
            for day, count in sorted(counts_by_day.items())
        ],
        "processing_time.csv": processing_rows,
        "summary_lengths.csv": summary_rows,
        "ratings_by_domain.csv": [
            {
                "domain": domain,
                "average_rating": round(fmean(values), 4),
                "feedback_count": len(values),
            }
            for domain, values in sorted(rating_groups.items())
        ],
        "coherence_by_domain.csv": [
            {
                "domain": domain,
                "average_coherence_score": round(fmean(values), 4),
                "documents": len(values),
            }
            for domain, values in sorted(coherence_by_domain.items())
        ],
    }

    output_paths = {}
    for filename, rows in rows_by_file.items():
        output_path = output_dir / filename
        _write_csv(output_path, CSV_SCHEMAS[filename], rows)
        output_paths[filename] = output_path
    return output_paths


if __name__ == "__main__":
    exported = export_metrics()
    for name, path in exported.items():
        print(f"Wrote {name}: {path}")
