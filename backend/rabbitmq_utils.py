"""RabbitMQ helper utilities.

Provides a single helper to publish durable messages. Keeps connections short-lived
to avoid channel leaks in synchronous FastAPI request handlers.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from opentelemetry.propagate import inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

import pika
from opentelemetry import trace  # type: ignore


DEFAULT_RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"


def send_to_rabbitmq(queue: str, message: Dict[str, Any], rabbitmq_url: str | None = None) -> None:
    """Publish a JSON serialisable message to a durable queue.

    Parameters
    ----------
    queue : str
        Queue name (declared durable if not present).
    message : dict
        Payload (will be json.dumps serialised).
    rabbitmq_url : str | None
        AMQP URL; falls back to env RABBITMQ_URL or default guest URL.
    """
    if rabbitmq_url is None:
        rabbitmq_url = os.environ.get("RABBITMQ_URL", DEFAULT_RABBITMQ_URL)

    tracer = trace.get_tracer("rabbitmq")
    with tracer.start_as_current_span("rabbitmq_publish") as span:
        span.set_attribute("queue", queue)
        # Inject W3C trace context into headers
        carrier: Dict[str, str] = {}
        inject(carrier)
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        try:
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers={k: v for k, v in carrier.items()}
                ),
            )
        finally:
            connection.close()

