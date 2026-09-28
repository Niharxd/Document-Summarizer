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

**Stage 5 complete.** Cohere summarization client implemented. Domain-aware prompts for legal,
medical, and technical documents. All 48 tests passing.
Development will proceed module by module.

## Setup

### Prerequisites

- Python 3.13
- Java JDK 11, 17, or 22 (required by PySpark)
- Hadoop `winutils.exe` for Windows (required for Parquet/file writes)

### Windows — Required Environment Variables

PySpark on Windows requires Java and Hadoop `winutils.exe`. Set these permanently via
**"Edit the system environment variables"** in Windows System Properties:

| Variable | Correct value | Common mistake |
|---|---|---|
| `JAVA_HOME` | `C:\Program Files\Java\jdk-22` | Do NOT include `\bin` at the end |
| `HADOOP_HOME` | `C:\hadoop` | Must contain `bin\winutils.exe` |

Also add `%HADOOP_HOME%\bin` to your system `PATH`.

> **Important (Windows):** `C:\hadoop\bin` must be on `PATH` — not just `HADOOP_HOME` set — at the
> time PySpark is invoked. `HADOOP_HOME` tells Spark where to find `winutils.exe`, but the JVM
> loads `hadoop.dll` via the OS `PATH`. If `C:\hadoop\bin` is missing from `PATH` you will get
> `UnsatisfiedLinkError: NativeIO$Windows.access0` when writing Parquet files.

```powershell
# Verify your setup in PowerShell:
Test-Path "$env:JAVA_HOME\bin\java.exe"          # must return True
Test-Path "$env:HADOOP_HOME\bin\winutils.exe"    # must return True
Test-Path "$env:HADOOP_HOME\bin\hadoop.dll"      # must return True
([System.Environment]::GetEnvironmentVariable('PATH','Machine')) -split ';' | Select-String 'hadoop'  # must show C:\hadoop\bin
```

### Windows — Hadoop winutils setup (one-time)

PySpark 4.x bundles Hadoop 3.5.0. The closest compatible `winutils.exe` is from Hadoop 3.3.6
(forward-compatible for local filesystem operations):

```powershell
# Create the directory
New-Item -ItemType Directory -Force -Path C:\hadoop\bin

# Download winutils.exe and hadoop.dll
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin/winutils.exe' -OutFile 'C:\hadoop\bin\winutils.exe'
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin/hadoop.dll' -OutFile 'C:\hadoop\bin\hadoop.dll'

# Then set HADOOP_HOME=C:\hadoop in Windows System Environment Variables
# and add C:\hadoop\bin to PATH
```

Source: https://github.com/cdarlint/winutils (community-maintained Windows Hadoop binaries)

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

# 4. Download required NLTK corpora (one-time, needed by TextBlob)
.venv\Scripts\python.exe setup_nltk.py

# 5. Configure environment variables
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

## ETL Pipeline

The ETL pipeline lives in `etl/` and is composed of two modules:

- `etl/transformations.py` — pure Python functions (no Spark dependency): `clean_text`,
  `document_length`, `extract_dates`, `extract_proper_nouns`, `coherence_score`,
  `summary_length_ratio`, `processing_timestamp`
- `etl/pipeline.py` — registers UDFs, builds the Spark DataFrame, applies all transformations,
  and writes Parquet output to `data/processed/etl_output.parquet`

Transformations applied per document:

| Column | Description |
|--------|-------------|
| `document_length` | Word count of raw text |
| `cleaned_text` | Whitespace/control-char normalised text |
| `dates` | Dates extracted via regex (ISO, slash, month-name formats) |
| `proper_nouns` | Capitalised-word heuristic (regex, capped at 50) |
| `extracted_entities` | `dates` + `proper_nouns` joined as a single string |
| `coherence_score` | Lexical diversity (unique words / total words) |
| `summary_length_to_document_length_ratio` | Placeholder `0.0` until Cohere stage |
| `processed_at` | UTC timestamp of the pipeline run |

> `generate_corpus.py` in `data/raw/` is intentionally excluded — only `.txt`, `.pdf`, and `.docx`
> files are ingested.

### Run the ETL pipeline

```powershell
# Windows — all env vars must be set in the same shell invocation
$env:JAVA_HOME='C:\Program Files\Java\jdk-22'
$env:HADOOP_HOME='C:\hadoop'
$env:PATH='C:\hadoop\bin;' + $env:PATH
$env:PYSPARK_PYTHON='.venv\Scripts\python.exe'
$env:PYSPARK_DRIVER_PYTHON='.venv\Scripts\python.exe'
.venv\Scripts\python.exe -m etl.pipeline
```

### Run ETL tests

```powershell
.venv\Scripts\python.exe -m pytest tests/test_etl.py -v
```

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

## Cohere Summarizer

The summarization layer lives in `summarizer/cohere_client.py` and exposes:

- `get_cohere_client()` — returns a cached `cohere.ClientV2` instance; raises `ValueError` if
  `COHERE_API_KEY` is missing
- `build_domain_prompt(document_text, domain)` — returns the full prompt string for the given domain
- `generate_summary(document_text, domain)` — calls the Cohere Chat API and returns the summary

Supported domains and prompt focus:

| Domain | Prompt focus |
|--------|--------------|
| `legal` | Important clauses, obligations, rights, conditions |
| `medical` | Diagnosis, findings, treatment, important observations |
| `technical` | Architecture, methods, findings, technical conclusions |

Model used: `command-a-plus-05-2026`

### Cohere setup

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` and replace the placeholder with your real key:
   ```
   COHERE_API_KEY=your_cohere_api_key_here
   ```
3. Get a free API key at https://dashboard.cohere.com/api-keys

### Run summarizer tests

```bash
.venv\Scripts\python.exe -m pytest tests/test_cohere_client.py -v
```

## Gradio Interface

Launch the document summarization interface from the project root:

```bash
python app/gradio_app.py
```

Upload a TXT, PDF, or DOCX file, select its domain, and click **Generate Summary**. The 1–5
rating is captured in the interface; feedback persistence is not implemented yet.

## Grafana CSV Dashboard

Generate the Grafana-ready CSV exports first, then start the local file server:

```bash
python grafana/export_metrics.py
python grafana/serve.py
```

In Grafana, configure the Infinity data source and import `grafana/dashboard.json`. The dashboard
requests the CSV exports from `http://localhost:8000/`; keep the local server running while using
the dashboard.

## API Key Security

- Copy `.env.example` to `.env` and add your `COHERE_API_KEY`.
- `.env` is listed in `.gitignore` and **must never be committed to GitHub**.
- `.env.example` (with placeholder values only) is safe to commit.
