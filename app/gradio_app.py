"""Simple Gradio interface for domain-aware document summarization."""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow both ``python app/gradio_app.py`` and package imports from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr

from app.document_loader import extract_text
from app.feedback import save_feedback
from summarizer.cohere_client import generate_summary
from summarizer.summary_metrics import build_summary_metrics, save_summary_metrics


def summarize_uploaded_document(
    file_path: str | Path | None, domain: str
) -> tuple[str, dict | None]:
    """Summarize an upload, persist its summary metrics, and return both."""
    if not file_path:
        return "Please upload a TXT, PDF, or DOCX document.", None

    try:
        started_at = time.perf_counter()
        document_text = extract_text(Path(file_path))
        if not document_text or not document_text.strip():
            return "The uploaded document contains no text to summarize.", None
        generated_summary = generate_summary(document_text, domain)
        processing_time_seconds = time.perf_counter() - started_at
        metrics = build_summary_metrics(
            document_name=Path(file_path).name,
            domain=domain,
            document_text=document_text,
            summary=generated_summary,
            processing_time_seconds=processing_time_seconds,
        )
        save_summary_metrics(metrics)
        return generated_summary, metrics
    except Exception as exc:
        return f"Unable to generate summary: {exc}", None


def submit_rating(file_path: str | Path | None, domain: str, rating: int | float) -> str:
    """Persist the selected rating for the uploaded document."""
    if not file_path:
        return "Please upload a document before submitting a rating."
    try:
        # Gradio sliders may return an integral value as a float.
        if isinstance(rating, float) and rating.is_integer():
            rating = int(rating)
        save_feedback(Path(file_path).name, domain, rating)
        return "Thank you. Your rating has been saved."
    except (TypeError, ValueError, OSError) as exc:
        return f"Unable to save rating: {exc}"


def create_interface() -> gr.Blocks:
    """Create the UI without starting a server."""
    with gr.Blocks(title="Document Summarizer") as interface:
        gr.Markdown("# Document Summarizer\nUpload a document and choose its domain to generate a summary.")
        with gr.Row():
            document = gr.File(
                label="Document (TXT, PDF, or DOCX)",
                file_types=[".txt", ".pdf", ".docx"],
                type="filepath",
            )
            domain = gr.Dropdown(
                choices=["legal", "medical", "technical"],
                value="legal",
                label="Domain",
            )
        generate = gr.Button("Generate Summary", variant="primary")
        summary = gr.Textbox(label="Generated Summary", lines=10, interactive=False)
        metrics = gr.JSON(label="Summary Metrics")
        rating = gr.Slider(
            minimum=1, maximum=5, step=1, value=5,
            label="Rate this summary (1–5 stars)",
        )
        submit = gr.Button("Submit Rating")
        feedback_status = gr.Markdown()
        generate.click(
            fn=summarize_uploaded_document,
            inputs=[document, domain],
            outputs=[summary, metrics],
        )
        submit.click(
            fn=submit_rating,
            inputs=[document, domain, rating],
            outputs=feedback_status,
        )
    return interface


if __name__ == "__main__":
    create_interface().launch()
