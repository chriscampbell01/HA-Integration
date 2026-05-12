import json
import os
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

TRUTHY_VALUES = {"1", "true", "yes"}
MAX_PAYLOAD_SIZE = 1_048_576


def process_request(method, path, headers=None, body=b"", expected_token=None):
    headers = headers or {}
    parsed_path = urlparse(path).path

    if method == "GET" and parsed_path == "/health":
        return 200, {"status": "ok"}

    if method == "GET" and parsed_path == "/api/v1/state":
        return 200, {
            "integration": "HA-Integration",
            "state": "online",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    if method == "POST" and parsed_path == "/api/v1/events":
        if expected_token:
            authorization = headers.get("Authorization", "")
            auth_prefix = "Bearer "
            if not authorization.startswith(auth_prefix):
                return 401, {"error": "unauthorized"}
            provided_token = authorization[len(auth_prefix) :]
            if not secrets.compare_digest(provided_token, expected_token):
                return 401, {"error": "unauthorized"}

        if not body:
            return 400, {"error": "empty_body"}

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return 400, {"error": "invalid_json"}

        event = payload.get("event")
        if not isinstance(event, str):
            return 400, {"error": "missing_event"}
        event = event.strip()
        if not event:
            return 400, {"error": "missing_event"}

        return 202, {
            "accepted": True,
            "event": event,
            "data": payload.get("data", {}),
        }

    return 404, {"error": "not_found"}


class HAAPIHandler(BaseHTTPRequestHandler):
    server_version = "HAIntegrationAPI/1.0"

    def _send_json(self, status, payload):
        response = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _handle(self, method):
        raw_content_length = self.headers.get("Content-Length", "0")
        try:
            content_length = int(raw_content_length)
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if content_length < 0:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if content_length > MAX_PAYLOAD_SIZE:
            self._send_json(413, {"error": "payload_too_large"})
            return
        body = self.rfile.read(content_length) if content_length > 0 else b""
        expected_token = os.environ.get("HA_API_TOKEN")
        status, payload = process_request(
            method=method,
            path=self.path,
            headers=self.headers,
            body=body,
            expected_token=expected_token,
        )
        self._send_json(status, payload)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def log_message(self, fmt, *args):
        if os.environ.get("HA_API_LOG_REQUESTS", "").lower() in TRUTHY_VALUES:
            super().log_message(fmt, *args)


def run():
    host = os.environ.get("HOST", "127.0.0.1")
    port_value = os.environ.get("PORT", "8080")
    try:
        port = int(port_value)
    except ValueError as exc:
        raise ValueError("Invalid PORT value: must be a number") from exc
    server = ThreadingHTTPServer((host, port), HAAPIHandler)
    print(f"HA API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
