# Document Summarizer

A domain-aware document summarization system built as a college project (Case Study 11).

## Description

Uploads documents (PDF, DOCX, or plain text), classifies them by domain (legal, medical, technical),
and generates domain-specific summaries using the Cohere API. A PySpark ETL pipeline processes
the documents and summaries to produce structured metrics. A Gradio UI lets subject-matter experts
review and rate summaries. Grafana dashboards visualize service health and quality metrics.

## Technologies

| Layer | Technology |
|-------|-----------|
| ETL pipeline | PySpark |
| Summarization | Cohere API |
| User interface | Gradio |
| Monitoring | Grafana |
| Language | Python 3.11+ |
| Version control | Git / GitHub |

## Planned Features

- PySpark ETL: text cleaning, entity extraction, domain classification, coherence scoring,
  summary-length ratio calculation
- Domain-specific summarization prompts (legal clauses, technical findings, medical overview)
- Gradio UI: document upload, domain selection, summary display, star-rating feedback
- Grafana dashboards: documents per day, average processing time, summary-length stats,
  quality rating by domain, coherence score by domain

## Project Status

**Initial setup complete.** No implementation has been written yet.
Development will proceed module by module.

## Setup (future instructions)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd document-summarizer

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your Cohere API key
```

## API Key Security

- Copy `.env.example` to `.env` and add your `COHERE_API_KEY`.
- `.env` is listed in `.gitignore` and **must never be committed to GitHub**.
- `.env.example` (with placeholder values only) is safe to commit.
