"""Tests for feedback CSV persistence using per-test temporary files."""
import csv

import pytest

from app import feedback


def test_save_valid_feedback(monkeypatch, tmp_path):
    target = tmp_path / "feedback.csv"
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", target)

    feedback.save_feedback("contract.pdf", "legal", 4)

    with target.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert list(rows[0]) == ["timestamp", "document_name", "domain", "rating"]
    assert rows[0]["document_name"] == "contract.pdf"
    assert rows[0]["domain"] == "legal"
    assert rows[0]["rating"] == "4"
    assert rows[0]["timestamp"]


def test_save_multiple_feedback_records(monkeypatch, tmp_path):
    target = tmp_path / "feedback.csv"
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", target)

    feedback.save_feedback("one.txt", "medical", 3)
    feedback.save_feedback("two.docx", "technical", 5)

    with target.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [(row["document_name"], row["rating"]) for row in rows] == [
        ("one.txt", "3"), ("two.docx", "5")
    ]


@pytest.mark.parametrize("rating", [0, 6, -1, 2.5, "4", True])
def test_invalid_rating_raises(monkeypatch, tmp_path, rating):
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", tmp_path / "feedback.csv")
    with pytest.raises(ValueError, match="integer from 1 to 5"):
        feedback.save_feedback("document.txt", "legal", rating)


def test_invalid_domain_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", tmp_path / "feedback.csv")
    with pytest.raises(ValueError, match="domain must be one of"):
        feedback.save_feedback("document.txt", "finance", 3)


@pytest.mark.parametrize("document_name", ["", "   ", None])
def test_empty_document_name_raises(monkeypatch, tmp_path, document_name):
    monkeypatch.setattr(feedback, "FEEDBACK_FILE", tmp_path / "feedback.csv")
    with pytest.raises(ValueError, match="document_name must not be empty"):
        feedback.save_feedback(document_name, "legal", 3)
