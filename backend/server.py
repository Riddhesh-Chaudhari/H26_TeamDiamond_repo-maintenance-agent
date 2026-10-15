import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from ai_agent import analyze_maintenance_evidence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MAX_REQUEST_BYTES = 1024 * 1024


class MaintenanceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"status": "ok"})
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/analyze":
            self._send_json(404, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header."})
            return

        if content_length <= 0:
            self._send_json(400, {"error": "Request body is required."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Evidence must be no larger than 1 MB."})
            return

        try:
            request_data = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        if not isinstance(request_data, dict):
            self._send_json(400, {"error": "Request body must be a JSON object."})
            return

        evidence = request_data.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            self._send_json(400, {"error": "Provide non-empty repository evidence."})
            return

        try:
            analysis = analyze_maintenance_evidence(evidence.strip())
        except RuntimeError as exc:
            self._send_json(502, {"error": str(exc)})
            return

        self._send_json(200, analysis)

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), MaintenanceHandler)
    print("Scout is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Scout.")
    finally:
        server.server_close()
