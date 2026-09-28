"""CSV persistence for summary ratings, separate from the ETL pipeline."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "feedback.csv"
DOMAINS = frozenset({"legal", "medical", "technical"})
CSV_FIELDS = ("timestamp", "document_name", "domain", "rating")


def save_feedback(document_name: str, domain: str, rating: int) -> None:
    """Append one validated rating to the feedback CSV."""
    if not isinstance(document_name, str) or not document_name.strip():
        raise ValueError("document_name must not be empty.")
    if not isinstance(domain, str) or domain not in DOMAINS:
        raise ValueError(f"domain must be one of: {', '.join(sorted(DOMAINS))}.")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        raise ValueError("rating must be an integer from 1 to 5.")

    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not FEEDBACK_FILE.exists() or FEEDBACK_FILE.stat().st_size == 0
    with FEEDBACK_FILE.open("a", newline="", encoding="utf-8") as feedback_file:
        writer = csv.DictWriter(feedback_file, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "document_name": document_name.strip(),
            "domain": domain,
            "rating": rating,
        })
