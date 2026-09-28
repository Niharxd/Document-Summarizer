"""Configuration tests for the local Grafana CSV server."""
from pathlib import Path

from grafana import serve


def test_server_is_configured_for_only_generated_export_csvs():
    assert serve.EXPORT_DIR == Path(serve.PROJECT_ROOT) / "data" / "processed" / "grafana"
    assert serve.DEFAULT_PORT == 8000
    assert serve.ExportCSVHandler.export_directory == serve.EXPORT_DIR
    assert serve.ALLOWED_FILES == {
        "documents_per_day.csv",
        "processing_time.csv",
        "summary_lengths.csv",
        "ratings_by_domain.csv",
        "coherence_by_domain.csv",
    }


def test_server_factory_can_be_constructed_without_running_forever():
    server = serve.create_server(port=0)
    try:
        assert server.server_address[1] > 0
        assert server.RequestHandlerClass is serve.ExportCSVHandler
    finally:
        server.server_close()
