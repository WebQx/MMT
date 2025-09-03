"""Dead-letter queue (DLQ) reprocessor service.

Consumes messages from the DLQ (``openemr_transcriptions_dlq``) and attempts to
re-publish them to the primary queue after optional backoff. Implements a
bounded retry counter embedded in the message payload (``_dlq_attempts``).

Exit codes:
 0 normal shutdown
 1 unrecoverable startup error

Environment variables:
 RABBITMQ_URL  AMQP connection URL
 DLQ_QUEUE     Name of DLQ queue (default: openemr_transcriptions_dlq)
 MAIN_QUEUE    Name of main queue (default: openemr_transcriptions)
 MAX_REPROCESS_ATTEMPTS  Maximum retry attempts (default: 5)
 BACKOFF_BASE_SECONDS    Base backoff seconds (default: 5)

Metrics (Prometheus counters):
 reprocessor_attempt_total
 reprocessor_success_total
 reprocessor_failure_total
 reprocessor_permanent_failure_total
"""
from __future__ import annotations

import json
import os
import time
import math
import pika
import threading
import signal
import structlog
from typing import Any, Dict
from metrics import (
	reprocessor_attempt_total,
	reprocessor_success_total,
	reprocessor_failure_total,
	reprocessor_permanent_failure_total,
)
from rabbitmq_utils import send_to_rabbitmq
from opentelemetry import trace  # type: ignore

logger = structlog.get_logger().bind(component="dlq_reprocessor")

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
DLQ_QUEUE = os.environ.get("DLQ_QUEUE", "openemr_transcriptions_dlq")
MAIN_QUEUE = os.environ.get("MAIN_QUEUE", "openemr_transcriptions")
MAX_REPROCESS_ATTEMPTS = int(os.environ.get("MAX_REPROCESS_ATTEMPTS", "5"))
BACKOFF_BASE_SECONDS = float(os.environ.get("BACKOFF_BASE_SECONDS", "5"))


def _calc_backoff(attempt: int) -> float:
	# Exponential with jitter
	return BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)) * (0.5 + os.urandom(1)[0] / 255)


def _handle_message(ch, method, properties, body):  # noqa: ANN001
	tracer = trace.get_tracer("dlq_reprocessor")
	with tracer.start_as_current_span("dlq_consume") as span:
		span.set_attribute("dlq_queue", DLQ_QUEUE)
		span.set_attribute("main_queue", MAIN_QUEUE)
		try:
			msg = json.loads(body)
		except (json.JSONDecodeError, ValueError) as e:
			reprocessor_permanent_failure_total.inc()
			ch.basic_ack(delivery_tag=method.delivery_tag)
			logger.warning("drop_malformed", size=len(body), error=str(e))
			return
		attempts = int(msg.get("_dlq_attempts", 0)) + 1
		span.set_attribute("attempt", attempts)
		reprocessor_attempt_total.inc()
		if attempts > MAX_REPROCESS_ATTEMPTS:
			reprocessor_permanent_failure_total.inc()
			ch.basic_ack(delivery_tag=method.delivery_tag)
			logger.error("permanent_failure", attempts=attempts, filename=msg.get("filename"))
			return
		delay = _calc_backoff(attempts)
		time.sleep(min(delay, 60))
		msg["_dlq_attempts"] = attempts
		try:
			send_to_rabbitmq(queue=MAIN_QUEUE, message=msg, rabbitmq_url=RABBITMQ_URL)
			reprocessor_success_total.inc()
			ch.basic_ack(delivery_tag=method.delivery_tag)
			logger.info("reprocessed", attempts=attempts, filename=msg.get("filename"))
		except Exception as e:  # noqa: BLE001
			span.record_exception(e)
			reprocessor_failure_total.inc()
			ch.basic_ack(delivery_tag=method.delivery_tag)
			try:
				send_to_rabbitmq(queue=DLQ_QUEUE, message=msg, rabbitmq_url=RABBITMQ_URL)
			except Exception:
				pass
			logger.warning("reprocess_failed", error=str(e), attempts=attempts)


_stop_event = threading.Event()


def run():
	logger.info("starting_reprocessor", dlq=DLQ_QUEUE, main=MAIN_QUEUE, url=RABBITMQ_URL)
	connection = None
	try:
		connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
		channel = connection.channel()
		channel.queue_declare(queue=DLQ_QUEUE, durable=True)
		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(queue=DLQ_QUEUE, on_message_callback=_handle_message)

	def _graceful(*_a):  # noqa: D401
		logger.info("signal_received_shutdown")
		_stop_event.set()
		try:
			channel.stop_consuming()
		except Exception:  # noqa: BLE001
			pass

	for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no cover
		try:
			signal.signal(sig, _graceful)
		except Exception:  # noqa: BLE001
			pass
		try:
			while not _stop_event.is_set():
				channel.connection.process_data_events(time_limit=1)
		finally:
			if connection and not connection.is_closed:
				connection.close()
	except Exception as e:
		logger.error("connection_error", error=str(e))
		if connection and not connection.is_closed:
			connection.close()


if __name__ == "__main__":  # pragma: no cover
	run()

