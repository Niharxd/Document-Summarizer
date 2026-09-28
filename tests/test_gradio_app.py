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


def test_rating_is_disabled_until_summary_generation_succeeds(tmp_path):
    interface = gradio_app.create_interface()
    config = interface.get_config_file()
    submit_button = next(
        component for component in config["components"]
        if component.get("props", {}).get("value") == "Submit rating"
    )
    assert submit_button["props"]["interactive"] is False
    rating_control = next(
        component for component in config["components"]
        if component.get("props", {}).get("elem_id") == "rating_control"
    )
    assert rating_control["type"] == "radio"
    assert [choice[1] for choice in rating_control["props"]["choices"]] == [1, 2, 3, 4, 5]

    handler = next(
        fn.fn for fn in interface.fns.values()
        if fn.fn.__name__ == "handle_summary_generation"
    )
    metrics = {
        "document_length": 10,
        "summary_length": 5,
        "summary_length_to_document_length_ratio": 0.5,
        "processing_time_seconds": 1.25,
    }
    upload = str(tmp_path / "sample.pdf")
    with patch.object(
        gradio_app,
        "summarize_uploaded_document",
        return_value=("Readable summary.", metrics),
    ):
        outputs = list(handler(upload, "medical"))[-1]

    assert outputs[8]["interactive"] is True
    assert outputs[9] == upload
    assert outputs[10] == "medical"
    assert outputs[3:7] == ("10 words", "5 words", "50.00%", "1.25 seconds")
    assert outputs[1] == "sample.pdf · Medical"


def test_generate_button_returns_summary_and_metrics_directly(tmp_path):
    interface = gradio_app.create_interface()
    config = interface.get_config_file()
    button = next(
        component for component in config["components"]
        if component.get("props", {}).get("elem_id") == "generate_button"
    )
    start_dependency = next(
        item for item in config["dependencies"]
        if (button["id"], "click") in item["targets"]
    )
    generation_dependency = next(
        item for item in config["dependencies"]
        if item["targets"] == [(None, "then")]
    )
    assert start_dependency["trigger_after"] is None
    assert start_dependency["queue"] is False
    assert generation_dependency["trigger_after"] == start_dependency["id"]
    assert len(generation_dependency["outputs"]) == 13

    start = next(
        fn.fn for fn in interface.fns.values()
        if fn.fn.__name__ == "start_generation"
    )
    status, button_update = start()
    assert status == "Generating summary..."
    assert button_update["value"] == "Generating summary..."
    assert button_update["interactive"] is False

    handler = next(
        fn.fn for fn in interface.fns.values()
        if fn.fn.__name__ == "handle_summary_generation"
    )
    metrics = {
        "document_length": 8,
        "summary_length": 3,
        "summary_length_to_document_length_ratio": 0.375,
        "processing_time_seconds": 0.42,
    }
    upload = str(tmp_path / "sample.txt")
    with patch.object(
        gradio_app,
        "summarize_uploaded_document",
        return_value=("Direct summary output", metrics),
    ) as summarize:
        progress, outputs = list(handler(upload, "technical"))

    summarize.assert_called_once_with(upload, "technical")
    assert outputs[0] == "Direct summary output"
    assert outputs[1] == "sample.txt · Technical"
    assert outputs[2].startswith("**Summary generated.**")
    assert outputs[3:7] == ("8 words", "3 words", "37.50%", "0.42 seconds")
    assert outputs[8]["interactive"] is True
    assert progress[2] == "Generating summary..."
    assert progress[8]["interactive"] is False
    assert progress[12]["interactive"] is False


def test_failed_generation_keeps_rating_disabled():
    interface = gradio_app.create_interface()
    handler = next(
        fn.fn for fn in interface.fns.values()
        if fn.fn.__name__ == "handle_summary_generation"
    )

    with patch.object(
        gradio_app,
        "summarize_uploaded_document",
        return_value=("Unable to generate summary: hidden detail", None),
    ):
        progress, outputs = list(handler("sample.pdf", "legal"))

    assert outputs[8]["interactive"] is False
    assert outputs[12]["interactive"] is True
    assert "hidden detail" not in outputs[2]


def test_new_document_resets_the_summarization_flow():
    interface = gradio_app.create_interface()
    config = interface.get_config_file()
    logo = next(
        component for component in config["components"]
        if component.get("props", {}).get("elem_id") == "brand-mark"
    )
    assert logo["type"] == "image"
    assert logo["props"]["value"]["orig_name"] == "documentai_logo.png"
    assert logo["props"]["width"] == 48
    assert logo["props"]["height"] == 34

    summary = next(
        component for component in config["components"]
        if component.get("props", {}).get("elem_id") == "summary_output"
    )
    assert summary["props"]["buttons"] == ["copy"]

    reset = next(
        fn.fn for fn in interface.fns.values()
        if fn.fn.__name__ == "reset_interface"
    )
    new_document_button = next(
        component for component in config["components"]
        if component.get("props", {}).get("elem_id") == "new_document"
    )
    assert any(
        (new_document_button["id"], "click") in event["targets"]
        for event in config["dependencies"]
    )
    outputs = reset()

    assert outputs[0]["value"] is None
    assert outputs[1]["value"] == "legal"
    assert outputs[2] == "_Your formatted summary will appear here._"
    assert outputs[3] == ""
    assert outputs[4] == "Upload a document to get started."
    assert outputs[5:9] == ("—", "—", "—", "—")
    assert outputs[10]["value"] == 5
    assert outputs[11]["interactive"] is False
    assert outputs[12:15] == (None, None, "")
    assert outputs[15]["interactive"] is True
