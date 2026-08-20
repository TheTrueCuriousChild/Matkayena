"""Structured logging with secret redaction and correlation ID propagation."""

import json
import logging
import re
import sys
import time
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Patterns to redact from logs
SENSITIVE_KEYS = {
    "password", "token", "access_token", "secret", "private_key",
    "api_key", "authorization", "cvv", "card_number", "ssn", "pan"
}


def sanitize_dict(data: Any) -> Any:
    """Recursively redact sensitive keys in dictionaries and lists."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_dict(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    return data


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include correlation or request metadata if attached
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "request_id") and record.request_id:
            log_obj["request_id"] = record.request_id
        if hasattr(record, "source_service") and record.source_service:
            log_obj["source_service"] = record.source_service
        if hasattr(record, "extra_data") and record.extra_data:
            log_obj["data"] = sanitize_dict(record.extra_data)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logger(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Sets up a structured JSON logger for a specific service."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns/propagates request and correlation IDs and logs requests."""
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = setup_logger(service_name)

    async def dispatch(self, request: Request, call_next):
        import uuid
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        source_service = request.headers.get("X-Source-Service", "client")

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.source_service = source_service

        start_time = time.time()
        response: Response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Don't log spam for /health and /ready
        if not (request.url.path.endswith("/health") or request.url.path.endswith("/ready")):
            extra = {
                "request_id": request_id,
                "correlation_id": correlation_id,
                "source_service": source_service,
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            }
            log_record = logging.LogRecord(
                name=self.service_name,
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"{request.method} {request.url.path} - {response.status_code} ({round(duration_ms, 2)}ms)",
                args=(),
                exc_info=None,
            )
            for k, v in extra.items():
                setattr(log_record, k, v)
            self.logger.handle(log_record)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        return response
