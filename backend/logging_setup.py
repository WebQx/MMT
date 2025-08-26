"""Structured logging configuration using structlog."""
from __future__ import annotations

import logging
import os
import sys
import structlog
from opentelemetry import trace

def _add_trace_ids(logger, method_name, event_dict):  # noqa: D401
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, '032x')
        event_dict["span_id"] = format(ctx.span_id, '016x')
    return event_dict


def configure_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        timestamper,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _add_trace_ids,
    ]
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
    )


configure_logging()
