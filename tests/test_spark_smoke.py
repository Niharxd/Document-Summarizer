"""Minimal PySpark smoke test."""
from pyspark.sql import SparkSession


def main():
    spark = None
    try:
        spark = (
            SparkSession.builder
            .master("local")
            .appName("SmokeTest")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("ERROR")

        data = [(1, "Test"), (2, "Spark")]
        df = spark.createDataFrame(data, ["id", "name"])
        df.show()

        row_count = df.count()
        assert row_count == 2, f"Expected 2 rows, got {row_count}"

        print("PySpark smoke test PASSED.")
    finally:
        if spark:
            spark.stop()


if __name__ == "__main__":
    main()
