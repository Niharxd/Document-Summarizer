"""
PySpark ETL pipeline for Document Summarization.

Run from the project root:
    .venv\\Scripts\\python.exe -m etl.pipeline

Reads:   data/raw/   (via app.document_loader)
Writes:  data/processed/etl_output.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when run as a module
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType, FloatType, IntegerType, StringType, StructField, StructType
)

from app.document_loader import load_all_documents
from etl.transformations import (
    clean_text,
    coherence_score,
    document_length,
    extract_dates,
    extract_proper_nouns,
    processing_timestamp,
    summary_length_ratio,
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "etl_output.parquet"

# ── Spark UDF registrations ───────────────────────────────────────────────────

_udf_clean_text = F.udf(clean_text, StringType())
_udf_doc_length = F.udf(document_length, IntegerType())
_udf_dates = F.udf(extract_dates, ArrayType(StringType()))
_udf_proper_nouns = F.udf(extract_proper_nouns, ArrayType(StringType()))
_udf_coherence = F.udf(coherence_score, FloatType())
_udf_summary_ratio = F.udf(summary_length_ratio, FloatType())


# ── Schema ────────────────────────────────────────────────────────────────────

INPUT_SCHEMA = StructType([
    StructField("document_id", StringType(), False),
    StructField("filename", StringType(), False),
    StructField("file_type", StringType(), False),
    StructField("domain", StringType(), False),
    StructField("text", StringType(), True),
])


# ── Pipeline ──────────────────────────────────────────────────────────────────

def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .master("local[1]")
        .appName("DocumentSummarizationETL")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def run(spark: SparkSession | None = None) -> "pyspark.sql.DataFrame":
    """
    Execute the full ETL pipeline.

    Parameters
    ----------
    spark : SparkSession, optional
        Pass an existing session (useful in tests). A new one is created
        if not provided.

    Returns
    -------
    Transformed Spark DataFrame (also written to OUTPUT_DIR as Parquet).
    """
    owns_spark = spark is None
    if owns_spark:
        spark = build_spark()
        spark.sparkContext.setLogLevel("ERROR")

    try:
        # 1. Ingest documents via document_loader
        print(f"[ETL] Loading documents from: {RAW_DIR}")
        records = load_all_documents(RAW_DIR)
        # Filter to only document files (exclude .py scripts in data/raw/)
        records = [r for r in records if r["file_type"] in {"txt", "pdf", "docx"}]
        print(f"[ETL] Documents loaded: {len(records)}")

        # 2. Create Spark DataFrame from ingested records
        df = spark.createDataFrame(records, schema=INPUT_SCHEMA)

        # 3. Apply transformations
        ts = processing_timestamp()

        df = (
            df
            # document_length on raw text
            .withColumn("document_length", _udf_doc_length(F.col("text")))
            # cleaned text
            .withColumn("cleaned_text", _udf_clean_text(F.col("text")))
            # entity extraction
            .withColumn("dates", _udf_dates(F.col("text")))
            .withColumn("proper_nouns", _udf_proper_nouns(F.col("text")))
            # combined extracted_entities as JSON-like string for easy inspection
            .withColumn(
                "extracted_entities",
                F.concat_ws(
                    "; ",
                    F.concat(F.lit("dates: "), F.array_join(F.col("dates"), ", ")),
                    F.concat(F.lit("proper_nouns: "), F.array_join(F.col("proper_nouns"), ", ")),
                )
            )
            # baseline coherence score (lexical diversity of cleaned text)
            .withColumn("coherence_score", _udf_coherence(F.col("cleaned_text")))
            # summary_length_to_document_length_ratio — placeholder (0 until Cohere)
            .withColumn(
                "summary_length_to_document_length_ratio",
                _udf_summary_ratio(F.lit(0), F.col("document_length")),
            )
            # processing metadata
            .withColumn("processed_at", F.lit(ts))
        )

        # 4. Select final column order
        df = df.select(
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
        )

        # 5. Write Parquet output
        # Count before write so we don't trigger a second full Spark action
        doc_count = df.count()
        print(f"[ETL] Writing Parquet output to: {OUTPUT_DIR}")
        OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)
        df.write.mode("overwrite").parquet(str(OUTPUT_DIR))
        print(f"[ETL] Done. {doc_count} documents written.")

        return df

    finally:
        if owns_spark:
            spark.stop()


if __name__ == "__main__":
    run()
