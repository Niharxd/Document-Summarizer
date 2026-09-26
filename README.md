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
| Language | Python 3.13 |
| Version control | Git / GitHub |

## Planned Features

- PySpark ETL: text cleaning, entity extraction, domain classification, coherence scoring,
  summary-length ratio calculation
- Domain-specific summarization prompts (legal clauses, technical findings, medical overview)
- Gradio UI: document upload, domain selection, summary display, star-rating feedback
- Grafana dashboards: documents per day, average processing time, summary-length stats,
  quality rating by domain, coherence score by domain

## Project Status

**Stage 3 complete.** Sample corpus created (9 documents across 3 domains), document ingestion
utilities implemented, and all 8 ingestion tests passing.
Development will proceed module by module.

## Setup

### Prerequisites

- Python 3.13
- Java JDK 8, 11, or 17 (required by PySpark)

### Windows — Required Environment Variables

PySpark requires Java. Set these in your Windows System Environment Variables
(or in your terminal session before running anything):

```powershell
# Point to your JDK root directory — NOT the bin folder
$env:JAVA_HOME = "C:\path\to\your\jdk"   # e.g. C:\Program Files\Java\jdk-17

# Optional: tell PySpark which Python to use when running locally
$env:PYSPARK_PYTHON = ".venv\Scripts\python.exe"
```

To set these permanently, search for **"Edit the system environment variables"** in Windows,
then add `JAVA_HOME` under System Variables.

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd document-summarizer

# 2. Create and activate a virtual environment (Windows)
py -3.13 -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env
# Edit .env and add your Cohere API key
```

### Verify PySpark

```bash
.venv\Scripts\python.exe tests\test_spark_smoke.py
```

Expected output:
```
+---+-----+
| id| name|
+---+-----+
|  1| Test|
|  2|Spark|
+---+-----+
PySpark smoke test PASSED.
```

## Sample Corpus

The sample corpus lives under `data/raw/` organised by domain:

```
data/raw/
├── legal/
│   ├── service_agreement.txt
│   ├── employment_contract.pdf
│   └── lease_agreement.docx
├── medical/
│   ├── clinical_case_summary.txt
│   ├── discharge_summary.pdf
│   └── research_abstract.docx
└── technical/
    ├── system_architecture_report.txt
    ├── api_specification.pdf
    └── ml_evaluation_report.docx
```

All documents are fictional and contain no real personal or patient information.

### Supported File Types

| Extension | Parser |
|-----------|--------|
| `.txt`    | Built-in `pathlib` |
| `.pdf`    | `pypdf` |
| `.docx`   | `python-docx` |

## Document Ingestion

The ingestion layer lives in `app/document_loader.py` and exposes:

- `discover_documents(root)` — recursively finds all `.txt`, `.pdf`, `.docx` files
- `extract_text(path)` — dispatches to the correct parser by file extension
- `detect_domain(path, root)` — infers domain from the immediate subfolder name
- `load_document(path, root)` — returns a single structured record
- `load_all_documents(root)` — discovers and loads every document under `root`

Each record contains:
```python
{
    "document_id": "<uuid>",
    "filename":    "service_agreement.txt",
    "file_type":   "txt",
    "domain":      "legal",
    "text":        "..."
}
```

### Run ingestion tests

```bash
.venv\Scripts\python.exe -m pytest tests/test_document_loader.py -v
```

## API Key Security

- Copy `.env.example` to `.env` and add your `COHERE_API_KEY`.
- `.env` is listed in `.gitignore` and **must never be committed to GitHub**.
- `.env.example` (with placeholder values only) is safe to commit.
