import json
import logging
import sys
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Numero totale di richieste HTTP ricevute",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Durata delle richieste HTTP in secondi",
    ["method", "path"],
)
CACHE_REQUESTS = Counter(
    "cache_requests_total",
    "Numero di accessi alla cache per esito (hit/miss)",
    ["result"],
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for field in ("path", "status", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload)


def _build_access_logger() -> logging.Logger:
    logger = logging.getLogger("app.access")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


access_logger = _build_access_logger()


async def observability_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_seconds = time.perf_counter() - start
    path = request.url.path
    method = request.method
    status = response.status_code

    REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)

    access_logger.info(
        "request completed",
        extra={
            "path": path,
            "status": status,
            "duration_ms": round(duration_seconds * 1000, 2),
        },
    )
    return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_cache_result(hit: bool) -> None:
    CACHE_REQUESTS.labels(result="hit" if hit else "miss").inc()
