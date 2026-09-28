"""Build and persist metrics associated with generated summaries."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from etl.transformations import document_length

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_METRICS_FILE = PROJECT_ROOT / "data" / "processed" / "summary_metrics.jsonl"


def build_summary_metrics(
    document_name: str,
    domain: str,
    document_text: str,
    summary: str,
    processing_time_seconds: float,
) -> dict[str, Any]:
    """Create a timestamped record with summary text and dashboard metrics."""
    source_length = document_length(document_text)
    summary_length = document_length(summary)
    ratio = round(summary_length / source_length, 4) if source_length else 0.0
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "document_name": document_name,
        "domain": domain,
        "summary": summary,
        "document_length": source_length,
        "summary_length": summary_length,
        "summary_length_to_document_length_ratio": ratio,
        "processing_time_seconds": round(float(processing_time_seconds), 6),
    }


def save_summary_metrics(record: dict[str, Any]) -> None:
    """Append a summary record as one JSON object per line."""
    SUMMARY_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_METRICS_FILE.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
