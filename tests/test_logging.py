from __future__ import annotations

import json
import logging
from io import StringIO
from uuid import UUID

from fastapi.testclient import TestClient

from app.config import Settings
from app.logging import LOGGER_NAME, JsonFormatter
from app.main import create_app
from app.middleware import safe_request_id


def test_json_formatter_emits_required_request_fields() -> None:
    record = logging.LogRecord(
        name=LOGGER_NAME,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request.completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    record.method = "GET"
    record.path = "/health"
    record.status = 200
    record.duration_ms = 1.25

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "request.completed"
    assert payload["level"] == "INFO"
    assert payload["timestamp"].endswith("+00:00")
    assert payload["request_id"] == "req-123"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status"] == 200
    assert payload["duration_ms"] == 1.25


def test_request_log_excludes_query_values_and_returns_request_id() -> None:
    app = create_app(Settings(_env_file=None, repository_backend="memory"))
    client = TestClient(app)
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(LOGGER_NAME)
    logger.addHandler(handler)

    try:
        response = client.get(
            "/health?token=do-not-log",
            headers={"X-Request-ID": "request-123"},
        )
    finally:
        logger.removeHandler(handler)

    payload = json.loads(output.getvalue())
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"
    assert payload["path"] == "/health"
    assert "do-not-log" not in output.getvalue()
    assert "token" not in output.getvalue()


def test_unsafe_request_id_is_replaced() -> None:
    generated = safe_request_id("bad\nvalue")

    assert generated != "bad\nvalue"
    assert str(UUID(generated)) == generated
