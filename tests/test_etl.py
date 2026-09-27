"""Tests for etl/transformations.py and etl/pipeline.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from pyspark.sql import SparkSession

from etl.transformations import (
    clean_text,
    coherence_score,
    document_length,
    extract_dates,
    extract_proper_nouns,
    summary_length_ratio,
)


# ── Spark fixture (session-scoped to avoid repeated JVM startup) ──────────────

@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local")
        .appName("ETLTests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


# ── clean_text ────────────────────────────────────────────────────────────────

def test_clean_text_normalises_whitespace():
    assert clean_text("hello   world") == "hello world"


def test_clean_text_removes_control_chars():
    assert "\x00" not in clean_text("hello\x00world")


def test_clean_text_preserves_punctuation():
    result = clean_text("Section 1.2: Payment terms (30 days).")
    assert "1.2" in result
    assert "(" in result


def test_clean_text_handles_none():
    assert clean_text(None) == ""


def test_clean_text_handles_empty():
    assert clean_text("   ") == ""


# ── document_length ───────────────────────────────────────────────────────────

def test_document_length_counts_words():
    assert document_length("one two three") == 3


def test_document_length_handles_none():
    assert document_length(None) == 0


# ── extract_dates ─────────────────────────────────────────────────────────────

def test_extract_dates_month_name():
    dates = extract_dates("Signed on January 15, 2024 and March 3, 2024.")
    assert "January 15, 2024" in dates
    assert "March 3, 2024" in dates


def test_extract_dates_iso_format():
    dates = extract_dates("Effective date: 2024-06-01.")
    assert "2024-06-01" in dates


def test_extract_dates_empty():
    assert extract_dates("No dates here.") == []


def test_extract_dates_deduplicates():
    dates = extract_dates("January 15, 2024 and again January 15, 2024.")
    assert dates.count("January 15, 2024") == 1


# ── extract_proper_nouns ──────────────────────────────────────────────────────

def test_extract_proper_nouns_finds_names():
    nouns = extract_proper_nouns("Acme Legal Solutions and Sandra Whitfield signed the contract.")
    assert len(nouns) > 0


def test_extract_proper_nouns_handles_none():
    assert extract_proper_nouns(None) == []


# ── coherence_score ───────────────────────────────────────────────────────────

def test_coherence_score_range():
    score = coherence_score("the quick brown fox jumps over the lazy dog")
    assert 0.0 <= score <= 1.0


def test_coherence_score_high_diversity():
    # All unique words → score close to 1.0
    score = coherence_score("alpha beta gamma delta epsilon")
    assert score > 0.9


def test_coherence_score_low_diversity():
    # Repeated word → low score
    score = coherence_score("the the the the the")
    assert score < 0.5


def test_coherence_score_handles_none():
    assert coherence_score(None) == 0.0


# ── summary_length_ratio ──────────────────────────────────────────────────────

def test_summary_ratio_zero_before_cohere():
    # Placeholder: summary_len=0 until Cohere is integrated
    assert summary_length_ratio(0, 100) == 0.0


def test_summary_ratio_calculation():
    assert summary_length_ratio(25, 100) == 0.25


def test_summary_ratio_zero_doc_length():
    assert summary_length_ratio(0, 0) == 0.0


# ── Pipeline fixtures (session-scoped — run ETL exactly once) ────────────────

EXPECTED_COLUMNS = {
    "document_id",
    "filename",
    "file_type",
    "domain",
    "text",
    "document_length",
    "cleaned_text",
    "extracted_entities",
    "dates",
    "proper_nouns",
    "summary_length_to_document_length_ratio",
    "coherence_score",
    "processed_at",
}


@pytest.fixture(scope="session")
def etl_df(spark):
    """Run the full ETL pipeline once and reuse the result across all pipeline tests."""
    from etl.pipeline import run
    return run(spark=spark)


# ── Pipeline tests (all use etl_df — no repeated Spark jobs) ─────────────────

def test_pipeline_output_schema(etl_df):
    assert set(etl_df.columns) == EXPECTED_COLUMNS


def test_pipeline_row_count(etl_df):
    assert etl_df.count() >= 9


def test_pipeline_no_null_document_ids(etl_df):
    from pyspark.sql import functions as F
    assert etl_df.filter(F.col("document_id").isNull()).count() == 0


def test_pipeline_domains_present(etl_df):
    domains = {row["domain"] for row in etl_df.select("domain").collect()}
    assert {"legal", "medical", "technical"}.issubset(domains)


def test_pipeline_document_length_positive(etl_df):
    from pyspark.sql import functions as F
    assert etl_df.filter(F.col("document_length") <= 0).count() == 0


def test_pipeline_coherence_in_range(etl_df):
    from pyspark.sql import functions as F
    out_of_range = etl_df.filter(
        (F.col("coherence_score") < 0.0) | (F.col("coherence_score") > 1.0)
    ).count()
    assert out_of_range == 0
