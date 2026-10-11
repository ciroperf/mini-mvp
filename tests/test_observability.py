import json
import logging

from fastapi.testclient import TestClient

from app.main import app
from app.observability import JsonFormatter

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_text() -> None:
    client.get("/health")  # genera almeno una richiesta da misurare

    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "cache_requests_total" in response.text


def test_access_log_line_is_valid_json() -> None:
    logger = logging.getLogger("app.access")
    records: list[str] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(self.format(record))

    handler = _CaptureHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    try:
        client.get("/health")
    finally:
        logger.removeHandler(handler)

    assert records
    payload = json.loads(records[-1])
    assert payload["path"] == "/health"
    assert payload["status"] == 200
    assert "duration_ms" in payload
    assert "level" in payload
    assert "timestamp" in payload
