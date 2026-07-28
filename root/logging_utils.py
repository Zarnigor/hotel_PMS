"""Request-id correlation and JSON log rendering for structured logging.

Wires a per-request id into every log record (via a contextvar so it also
reaches code called outside the request/response cycle, e.g. Celery tasks
sharing the same thread) and renders file-handler records as single-line
JSON for Filebeat/Elasticsearch ingestion (see filebeat.yml).
"""

import contextvars
import json
import logging
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIDMiddleware:
    """Assign a correlation id to each request and expose it to the logger.

    Reuses the inbound X-Request-ID header when present (e.g. set by an
    upstream gateway/load balancer) so traces stay consistent across
    services, otherwise generates a new one. The id is echoed back on the
    response for client-side correlation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = request_id
        return response


class RequestIDFilter(logging.Filter):
    """Attach the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JSONFormatter(logging.Formatter):
    """Render a log record as one JSON line (timestamp, level, module, ...)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
