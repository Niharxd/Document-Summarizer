"""Serve only generated Grafana CSV exports over a local HTTP endpoint."""
from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "data" / "processed" / "grafana"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
ALLOWED_FILES = frozenset({
    "documents_per_day.csv",
    "processing_time.csv",
    "summary_lengths.csv",
    "ratings_by_domain.csv",
    "coherence_by_domain.csv",
})


class ExportCSVHandler(SimpleHTTPRequestHandler):
    """HTTP handler rooted at the generated export directory and CSV allowlist."""

    export_directory = EXPORT_DIR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.export_directory), **kwargs)

    def _is_allowed_export(self) -> bool:
        requested = unquote(urlsplit(self.path).path).lstrip("/")
        return requested in ALLOWED_FILES

    def do_GET(self) -> None:
        if not self._is_allowed_export():
            self.send_error(404, "Only generated Grafana CSV exports are available")
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if not self._is_allowed_export():
            self.send_error(404, "Only generated Grafana CSV exports are available")
            return
        super().do_HEAD()


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build the local server; callers decide when to run its serve loop."""
    return ThreadingHTTPServer((host, port), ExportCSVHandler)


def main() -> None:
    server = create_server()
    print(f"Serving Grafana CSV exports from {EXPORT_DIR} at http://localhost:{DEFAULT_PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Grafana CSV server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
