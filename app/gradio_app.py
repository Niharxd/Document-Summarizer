"""Simple Gradio interface for domain-aware document summarization."""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow both ``python app/gradio_app.py`` and package imports from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DOCUMENTAI_LOGO = PROJECT_ROOT / "assets" / "documentai_logo.png"

import gradio as gr

from app.document_loader import extract_text
from app.feedback import save_feedback
from summarizer.cohere_client import generate_summary
from summarizer.summary_metrics import build_summary_metrics, save_summary_metrics

APP_CSS = """
.gradio-container { --body-background-fill:#050505; --background-fill-primary:#0B0B0B; --background-fill-secondary:#111111; --block-background-fill:#101010; --block-border-color:#292929; --input-background-fill:#181818; --input-border-color:#383838; --neutral-50:#101010; --neutral-100:#181818; --neutral-200:#292929; --neutral-300:#383838; --neutral-500:#A3A3A3; --neutral-700:#E5E5E5; --neutral-800:#F5F5F5; background:radial-gradient(circle at 85% 10%,rgba(255,106,0,0.08),transparent 32%),linear-gradient(135deg,#050505 0%,#0B0B0B 55%,#120B07 100%) !important; background-attachment:fixed; color:#FFFFFF !important; font-family:Inter,ui-sans-serif,system-ui,sans-serif !important; }
.gradio-container, .gradio-container * { box-sizing:border-box; }
.gradio-container main { max-width:none !important; }
#documentai-shell { max-width:1100px; margin:0 auto; padding:16px 24px 24px; gap:12px; }
#app-header { position:relative; display:flex; align-items:center; gap:11px; min-height:52px; padding:0 0 11px; border-bottom:1px solid #292929; }
#app-header:after { position:absolute; bottom:-1px; left:0; width:120px; height:2px; background:linear-gradient(90deg,#FF6A00,#D94F00); content:''; }
#brand-mark { width:52px !important; height:38px !important; min-width:52px !important; flex:0 0 52px; overflow:hidden; padding:0 !important; border:0 !important; border-radius:0 !important; background:transparent !important; }
#brand-mark img { width:100% !important; height:100% !important; object-fit:contain !important; transform:scale(1.55); mix-blend-mode:screen; }
#app-header h1 { margin:0; color:#FFFFFF; font-size:20px; font-weight:740; letter-spacing:-.035em; line-height:1.15; }
#app-header p { margin:3px 0 0; color:#A3A3A3; font-size:12px; }
#workspace { gap:9px !important; padding:12px 14px 14px !important; border:1px solid #292929 !important; border-radius:12px !important; background:#111111 !important; box-shadow:0 12px 30px #00000030 !important; }
#workspace-header { align-items:flex-start !important; }
#new_document { width:124px !important; min-width:124px !important; max-width:124px !important; height:34px !important; min-height:34px !important; padding:0 12px !important; border:1px solid #383838 !important; border-radius:7px !important; background:#181818 !important; color:#D4D4D4 !important; font-size:11px !important; }
#new_document:hover { border-color:#FF6A00 !important; color:#FF8A3D !important; }
#workspace #workspace { padding:0 !important; border:0 !important; border-radius:0 !important; background:transparent !important; box-shadow:none !important; }
#workspace .styler { background:#111111 !important; border:0 !important; }
#workspace .row, #workspace .column { border:0 !important; background:transparent !important; box-shadow:none !important; }
#workspace [data-testid='html'] { border:0 !important; background:transparent !important; }
#workspace .block, #workspace .wrap { background-color:transparent !important; border:0 !important; box-shadow:none !important; }
.ui-section-title, .ui-section-title *, #workspace .prose, #workspace [data-testid='markdown'] { background:transparent !important; }
.ui-section-title h2 { margin:0; color:#FFFFFF !important; font-size:14px; font-weight:680; }
.ui-section-title p { margin:3px 0 0; color:#A3A3A3 !important; font-size:11px; }
#upload_control, #domain_control { min-width:0; }
#domain_control, #domain_control .column, #domain_control .block, #domain_control .wrap { background:#111111 !important; }
#upload_control label, #domain_control label { color:#E5E5E5 !important; font-size:12px !important; font-weight:650 !important; }
#upload_control [data-testid='file-upload'], #upload_control .upload-container { min-height:108px; border:1px dashed #494949 !important; border-radius:9px !important; background:#181818 !important; color:#FFFFFF !important; cursor:pointer; }
#upload_control [data-testid='file-upload']:hover { border-color:#FF6A00 !important; background:#20160F !important; }
#upload_control *, #domain_control * { color:#E5E5E5; }
#domain_control [role='combobox'], #domain_control input { color:#FFFFFF !important; background:#181818 !important; }
#domain_control [data-testid='dropdown'] { border:1px solid #383838 !important; border-radius:8px !important; }
#generate_button { min-height:44px; border:0 !important; border-radius:8px !important; background:linear-gradient(100deg,#FF6A00,#D94F00) !important; color:#FFFFFF !important; font-size:14px; font-weight:720; box-shadow:0 5px 16px #ff6a0030 !important; }
#generate_button:hover { background:linear-gradient(100deg,#FF8A3D,#E65A00) !important; }
#summary-heading h2, #feedback-heading h2 { margin:0; color:#FFFFFF !important; font-size:16px; font-weight:700; }
#summary_status { min-height:16px; margin:3px 0 5px; color:#A3A3A3 !important; font-size:11px; }
#summary_document_info { margin:-3px 0 3px; color:#FF8A3D !important; font-size:12px; font-weight:650; }
#summary_document_info p { color:#FF8A3D !important; }
#summary_output { min-height:82px; max-height:300px; overflow:auto; padding:12px 16px; border:1px solid #292929; border-radius:10px; background:#101010; color:#F5F5F5 !important; font-size:13px; line-height:1.65; }
#summary_output :is(p,li,td) { color:#E5E5E5 !important; }
#summary_output :is(h1,h2,h3,h4,strong) { color:#FFFFFF !important; }
#summary_output a { color:#FF8A3D !important; }
#summary_output table { width:100%; border-collapse:collapse; }
#summary_output th, #summary_output td { padding:7px 9px; border:1px solid #383838; text-align:left; }
#metrics-row { display:grid !important; grid-template-columns:repeat(4,minmax(0,1fr)); gap:9px; margin-top:0; }
.stat { min-width:0; min-height:65px; gap:2px !important; padding:9px 12px !important; border:1px solid #292929 !important; border-radius:9px !important; background:#101010 !important; }
.stat-label, .stat-label p { margin:0 !important; color:#A3A3A3 !important; font-size:10px; font-weight:650; letter-spacing:.045em; text-transform:uppercase; }
.stat-value, .stat-value p { margin:0 !important; color:#FF8A3D !important; font-size:18px; font-weight:750; letter-spacing:-.025em; }
#feedback-section { gap:5px; padding:2px 0 0; }
#feedback-heading h2 { font-size:14px; }
#feedback-heading p { margin:2px 0 0; color:#A3A3A3; font-size:11px; }
#rating_context { margin:0; color:#A3A3A3 !important; font-size:11px; }
#rating_control { max-width:390px; overflow:visible !important; padding:0 !important; border:0 !important; background:transparent !important; }
#rating_control > .wrap { display:flex !important; flex-direction:row !important; gap:8px; overflow:visible !important; background:transparent !important; }
#rating_control .wrap > label { display:flex; width:38px; min-height:36px; align-items:center; justify-content:center; padding:0 !important; border:1px solid #383838 !important; border-radius:8px !important; background:#181818 !important; color:#E5E5E5 !important; cursor:pointer; }
#rating_control .wrap > label.selected { border-color:#FF6A00 !important; background:#3A1C0C !important; color:#FF8A3D !important; box-shadow:inset 0 0 0 1px #FF6A00; }
#rating_control .wrap > label span { color:inherit !important; }
#rating_control input { position:absolute; width:1px; height:1px; opacity:0; accent-color:#FF6A00; }
#feedback-section > .row { align-items:center; gap:12px; }
#submit_button { width:100%; max-width:170px !important; min-width:145px; min-height:36px; border:0 !important; border-radius:8px !important; background:linear-gradient(100deg,#FF6A00,#D94F00) !important; color:#FFFFFF !important; font-size:12px; font-weight:700; }
#submit_button:hover:not(:disabled) { background:linear-gradient(100deg,#FF8A3D,#E65A00) !important; }
#submit_button:disabled { border:1px solid #383838 !important; background:#222222 !important; color:#858585 !important; opacity:1 !important; }
#feedback_status { min-height:16px; margin:0; color:#86EFAC !important; font-size:11px; }
.gradio-container label, .gradio-container .label-wrap span { color:#E5E5E5 !important; }
.gradio-container input, .gradio-container textarea, .gradio-container [role='combobox'] { color:#FFFFFF !important; }
.gradio-container input::placeholder, .gradio-container textarea::placeholder { color:#A3A3A3 !important; opacity:1 !important; }
.gradio-container button.secondary { background:#181818 !important; color:#E5E5E5 !important; border:1px solid #383838 !important; }
footer, .built-with { display:none !important; }
@media (max-width:700px) { #documentai-shell { padding:12px 12px 20px; gap:10px; } #workspace { padding:12px !important; } #metrics-row { grid-template-columns:repeat(2,minmax(0,1fr)); } }
"""


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
    """Build the polished DocumentAI interface without starting a server."""

    def present_summary_result(result_text, metrics, file_path, domain):
        if metrics is None:
            if result_text.startswith("Please upload"):
                message = "**Select a document before generating a summary.**"
            elif "contains no text" in result_text:
                message = "**No readable text was found.** Try a TXT, searchable PDF, or DOCX file."
            else:
                message = "**We couldn't generate a summary.** Check the document and try again."
            return (
                "",
                "",
                message,
                "—",
                "—",
                "—",
                "—",
                "",
                gr.update(interactive=False),
                None,
                None,
                "",
                gr.update(value="Generate Summary", interactive=True),
            )

        ratio = float(metrics.get("summary_length_to_document_length_ratio", 0.0))
        status = "**Summary generated.** Review the result and rate it below."
        document_info = f"{Path(file_path).name} · {domain.title()}"
        context = f"Rating for **{Path(file_path).name}** · **{domain.title()}**"
        return (
            result_text,
            document_info,
            status,
            f"{int(metrics.get('document_length', 0)):,} words",
            f"{int(metrics.get('summary_length', 0)):,} words",
            f"{ratio * 100:.2f}%",
            f"{float(metrics.get('processing_time_seconds', 0.0)):.2f} seconds",
            context,
            gr.update(interactive=True),
            file_path,
            domain,
            "",
            gr.update(value="Generate Summary", interactive=True),
        )

    def present_rating_result(file_path, domain, rating):
        result = submit_rating(file_path, domain, rating)
        if result.startswith("Unable to save"):
            return "**We couldn't save your rating.** Please try again."
        return f"**{result}**"

    def handle_summary_generation(file_path, domain):
        yield (
            "",
            "",
            "Generating summary...",
            "—",
            "—",
            "—",
            "—",
            "",
            gr.update(interactive=False),
            None,
            None,
            "",
            gr.update(value="Generating summary...", interactive=False),
        )
        result_text, metrics = summarize_uploaded_document(file_path, domain)
        yield present_summary_result(result_text, metrics, file_path, domain)

    def reset_interface():
        return (
            gr.update(value=None),
            gr.update(value="legal"),
            "_Your formatted summary will appear here._",
            "",
            "Upload a document to get started.",
            "—",
            "—",
            "—",
            "—",
            "",
            gr.update(value=5),
            gr.update(interactive=False),
            None,
            None,
            "",
            gr.update(value="Generate Summary", interactive=True),
        )

    def start_generation():
        return "Generating summary...", gr.update(value="Generating summary...", interactive=False)

    with gr.Blocks(title="DocumentAI") as interface:
        with gr.Column(elem_id="documentai-shell"):
            with gr.Row(elem_id="app-header", equal_height=True):
                gr.Image(
                    value=str(DOCUMENTAI_LOGO),
                    label=None,
                    show_label=False,
                    interactive=False,
                    container=False,
                    buttons=[],
                    height=34,
                    width=48,
                    elem_id="brand-mark",
                    alt_text="DocumentAI document summarization logo",
                    scale=0,
                )
                gr.HTML(
                    "<div><h1>DocumentAI</h1>"
                    "<p>Document summarization and analysis</p></div>"
                )

            with gr.Group(elem_id="workspace"):
                with gr.Row(elem_id="workspace-header"):
                    gr.HTML(
                        "<div class='ui-section-title'><h2>Prepare your document</h2>"
                        "<p>Upload a file, select its domain, and generate a summary.</p></div>"
                    )
                    new_document = gr.Button(
                        "New document", size="sm", elem_id="new_document", scale=0
                    )
                with gr.Row(equal_height=True):
                    document = gr.File(
                        label="Upload a document · PDF, DOCX or TXT",
                        file_types=[".txt", ".pdf", ".docx"],
                        type="filepath",
                        height=142,
                        scale=1,
                        elem_id="upload_control",
                    )
                    with gr.Column(scale=1, elem_id="domain_control"):
                        domain = gr.Dropdown(
                            choices=[("Legal", "legal"), ("Medical", "medical"), ("Technical", "technical")],
                            value="legal",
                            label="Document domain",
                        )
                        generate = gr.Button(
                            "Generate Summary", variant="primary", size="lg", elem_id="generate_button"
                        )

            rating_document = gr.State()
            rating_domain = gr.State()

            with gr.Column():
                gr.Markdown("## Generated summary", elem_id="summary-heading")
                summary_document_info = gr.Markdown(elem_id="summary_document_info")
                summary_status = gr.Markdown("Upload a document to get started.", elem_id="summary_status")
                summary = gr.Markdown(
                    "_Your formatted summary will appear here._",
                    elem_id="summary_output",
                    buttons=["copy"],
                )

            with gr.Row(elem_id="metrics-row"):
                with gr.Column(elem_classes=["stat"]):
                    gr.Markdown("Document length", elem_classes=["stat-label"])
                    document_length = gr.Markdown("—", elem_classes=["stat-value"])
                with gr.Column(elem_classes=["stat"]):
                    gr.Markdown("Summary length", elem_classes=["stat-label"])
                    summary_length = gr.Markdown("—", elem_classes=["stat-value"])
                with gr.Column(elem_classes=["stat"]):
                    gr.Markdown("Summary ratio", elem_classes=["stat-label"])
                    length_ratio = gr.Markdown("—", elem_classes=["stat-value"])
                with gr.Column(elem_classes=["stat"]):
                    gr.Markdown("Processing time", elem_classes=["stat-label"])
                    processing_time = gr.Markdown("—", elem_classes=["stat-value"])

            with gr.Column(elem_id="feedback-section"):
                gr.HTML(
                    "<div id='feedback-heading'><h2>Rate this summary</h2>"
                    "<p>How useful was this summary?</p></div>"
                )
                rating_context = gr.Markdown(elem_id="rating_context")
                with gr.Row(equal_height=True):
                    rating = gr.Radio(
                        choices=[1, 2, 3, 4, 5],
                        value=5,
                        label="Your rating · 1 = Not useful · 5 = Very useful",
                        container=False,
                        elem_id="rating_control",
                        scale=4,
                    )
                    submit = gr.Button(
                        "Submit rating", interactive=False, elem_id="submit_button", scale=1
                    )
                feedback_status = gr.Markdown()

        generate.click(
            fn=start_generation,
            inputs=[],
            outputs=[summary_status, generate],
            queue=False,
        ).then(
            fn=handle_summary_generation,
            inputs=[document, domain],
            outputs=[
                summary,
                summary_document_info,
                summary_status,
                document_length,
                summary_length,
                length_ratio,
                processing_time,
                rating_context,
                submit,
                rating_document,
                rating_domain,
                feedback_status,
                generate,
            ],
        )
        submit.click(
            fn=present_rating_result,
            inputs=[rating_document, rating_domain, rating],
            outputs=feedback_status,
        )
        new_document.click(
            fn=reset_interface,
            inputs=[],
            outputs=[
                document,
                domain,
                summary,
                summary_document_info,
                summary_status,
                document_length,
                summary_length,
                length_ratio,
                processing_time,
                rating_context,
                rating,
                submit,
                rating_document,
                rating_domain,
                feedback_status,
                generate,
            ],
        )
    return interface


if __name__ == "__main__":
    create_interface().launch(
        css=APP_CSS,
        theme=gr.themes.Base(primary_hue="orange", secondary_hue="orange", neutral_hue="zinc")
    )
