"""
ETL transformation functions.

All functions are plain Python so they can be unit-tested without Spark.
They are registered as Spark UDFs in pipeline.py.
"""
from __future__ import annotations

import re
from datetime import datetime


# ── Text cleaning ─────────────────────────────────────────────────────────────

# Matches runs of whitespace (spaces, tabs, newlines) for normalisation
_WHITESPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
# Control characters except newline (\n=10) and tab (\t=9)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str | None) -> str:
    """
    Normalise whitespace, strip control characters, preserve punctuation.
    Returns empty string for null/empty input.
    """
    if not text or not text.strip():
        return ""
    text = _CONTROL.sub("", text)          # remove control chars
    text = _WHITESPACE.sub(" ", text)      # collapse horizontal whitespace
    text = _MULTI_NEWLINE.sub("\n\n", text)  # collapse excessive blank lines
    return text.strip()


# ── Document length ───────────────────────────────────────────────────────────

def document_length(text: str | None) -> int:
    """Word count of the raw text."""
    if not text:
        return 0
    return len(text.split())


# ── Entity extraction ─────────────────────────────────────────────────────────

# Date patterns: covers common formats found in legal/medical/technical docs
_DATE_PATTERNS = [
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
]


def extract_dates(text: str | None) -> list[str]:
    """Extract date strings from text using regex patterns."""
    if not text:
        return []
    found: list[str] = []
    for pattern in _DATE_PATTERNS:
        found.extend(pattern.findall(text))
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for d in found:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


# Common words that are capitalised at sentence starts but are not proper nouns
_STOPWORDS = frozenset({
    "The", "A", "An", "This", "That", "These", "Those", "It", "Its",
    "He", "She", "They", "We", "You", "I", "My", "Our", "Your", "His", "Her",
    "In", "On", "At", "To", "For", "Of", "By", "As", "Is", "Are", "Was",
    "Were", "Be", "Been", "Has", "Have", "Had", "Do", "Does", "Did",
    "All", "Any", "Each", "Both", "No", "Not", "And", "Or", "But", "If",
    "With", "From", "Upon", "Such", "When", "Where", "Which", "Who",
    "What", "How", "May", "Shall", "Will", "Should", "Would", "Could",
})

# Matches a single capitalised word (first letter upper, rest lower or mixed)
_CAPITALISED_WORD = re.compile(r"\b([A-Z][a-z][a-zA-Z]*)\b")


def extract_proper_nouns(text: str | None) -> list[str]:
    """
    Extract proper nouns using a capitalisation heuristic.
    Finds words that start with an uppercase letter followed by at least one
    lowercase letter, excluding common sentence-starting words.
    No external NLP libraries — safe to run inside Spark UDFs.
    """
    if not text:
        return []
    candidates = _CAPITALISED_WORD.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for word in candidates:
        if word not in _STOPWORDS and word not in seen:
            seen.add(word)
            result.append(word)
    return result[:50]


def extract_entities(text: str | None) -> dict[str, list[str]]:
    """Return a dict with 'dates' and 'proper_nouns' lists."""
    return {
        "dates": extract_dates(text),
        "proper_nouns": extract_proper_nouns(text),
    }


# ── Baseline metrics ──────────────────────────────────────────────────────────

def coherence_score(text: str | None) -> float:
    """
    Baseline coherence score: lexical diversity (unique words / total words).
    Range 0.0–1.0.  Higher = more varied vocabulary.

    NOTE: This is a structural placeholder until Cohere-generated summaries
    are available.  It does NOT measure summary-to-document coherence.
    """
    if not text:
        return 0.0
    words = [w.lower() for w in text.split() if w.isalpha()]
    if not words:
        return 0.0
    return round(len(set(words)) / len(words), 4)


def summary_length_ratio(summary_len: int, doc_len: int) -> float:
    """
    summary_length / document_length ratio.

    NOTE: summary_len is 0 until Cohere integration is complete.
    This field is a placeholder and will be populated in Stage 5.
    """
    if doc_len == 0:
        return 0.0
    return round(summary_len / doc_len, 4)


# ── Processing timestamp ──────────────────────────────────────────────────────

def processing_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
