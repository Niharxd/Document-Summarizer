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

**Environment verified.** Virtual environment created, all dependencies installed, and PySpark smoke test passing.
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

## API Key Security

- Copy `.env.example` to `.env` and add your `COHERE_API_KEY`.
- `.env` is listed in `.gitignore` and **must never be committed to GitHub**.
- `.env.example` (with placeholder values only) is safe to commit.
