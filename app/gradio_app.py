"""Simple Gradio interface for domain-aware document summarization."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow both ``python app/gradio_app.py`` and package imports from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr

from app.document_loader import extract_text
from summarizer.cohere_client import generate_summary


def summarize_uploaded_document(file_path: str | Path | None, domain: str) -> str:
    """Extract an uploaded document and return its generated summary."""
    if not file_path:
        return "Please upload a TXT, PDF, or DOCX document."

    try:
        document_text = extract_text(Path(file_path))
        if not document_text or not document_text.strip():
            return "The uploaded document contains no text to summarize."
        return generate_summary(document_text, domain)
    except Exception as exc:
        return f"Unable to generate summary: {exc}"


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
        rating = gr.Slider(
            minimum=1, maximum=5, step=1, value=5,
            label="Rate this summary (1–5 stars)",
        )
        generate.click(
            fn=summarize_uploaded_document,
            inputs=[document, domain],
            outputs=summary,
        )
    return interface


if __name__ == "__main__":
    create_interface().launch()
