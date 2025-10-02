import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

import pika
import redis
import structlog
from dotenv import load_dotenv
from opentelemetry import trace  # type: ignore
from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
from opentelemetry.propagate import extract
from sqlalchemy import text

from config import get_settings
from entity_extraction import extract_entities, summarize_text
from metrics import (
    consumer_dlq_total,
    consumer_failure_total,
    duplicates_skipped_total,
    e2e_transcription_latency_seconds,
    idempotency_db_hits_total,
    idempotency_memory_hits_total,
    idempotency_redis_hits_total,
    transcription_queue_depth,
    transcripts_persisted_total,
)
from nextcloud_storage import store_transcript_payload
from persistence import SESSION_MAKER, store_transcript
from rabbitmq_utils import send_to_rabbitmq
try:  # optional instrumentation
    RequestsInstrumentor().instrument()
except Exception:  # noqa: BLE001
    pass

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

settings = get_settings()
RABBITMQ_URL = settings.rabbitmq_url
TRANSCRIPTION_QUEUE = settings.transcription_queue
DLQ_QUEUE = f"{TRANSCRIPTION_QUEUE}_dlq"

_log = structlog.get_logger(__name__).bind(component="transcription_consumer")

_SEEN_HASHES: list[str] = []  # preserve order for simple FIFO pruning (fallback)
_redis_client = None
if settings.redis_url:
    try:  # noqa: SIM105
        _redis_client = redis.StrictRedis.from_url(settings.redis_url, decode_responses=True)
        # Optionally initialize Bloom filter (requires RedisBloom module loaded)
        if settings.use_bloom_idempotency:
            try:
                # Check if filter already exists by reserving only if absent.
                # For BF: BF.RESERVE key error_rate capacity (NX not universally supported; emulate)
                # We'll attempt an INFO command to see if module present.
                modules = _redis_client.execute_command("MODULE", "LIST")  # type: ignore[arg-type]
                has_bloom = any(b"bf" in (m[1] if isinstance(m, list) and len(m) > 1 else b"") for m in modules) or any(
                    b"redisbloom" in (m[1] if isinstance(m, list) and len(m) > 1 else b"") for m in modules
                )
                if has_bloom:
                    # Try creating filter if not yet created; ignore errors if exists.
                    try:
                        _redis_client.execute_command(
                            "BF.RESERVE",
                            "idemp_filter",
                            settings.bloom_error_rate,
                            settings.bloom_capacity,
                        )
                    except Exception:  # filter likely exists
                        pass
                else:
                    # If RedisBloom not present, we silently fall back to normal set logic.
                    pass
            except Exception:
                pass
    except Exception:  # noqa: BLE001
        _redis_client = None


def _message_hash(data: Dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update((data.get("filename", "") + "::" + data.get("text", "")).encode("utf-8"))
    return digest.hexdigest()


def _check_duplicate(message_hash: str) -> bool:
    duplicate = False
    if settings.enable_idempotency:
        if _redis_client:
            try:
                bloom_maybe_exists = False
                if settings.use_bloom_idempotency:
                    try:
                        bloom_ret = _redis_client.execute_command("BF.ADD", "idemp_filter", message_hash)  # type: ignore[arg-type]
                        bloom_maybe_exists = bloom_ret in (0, b"0")
                    except Exception:
                        bloom_maybe_exists = False
                key = f"idemp:{message_hash}"
                added = _redis_client.set(name=key, value="1", nx=True, ex=settings.idempotency_ttl_seconds)
                if not added:
                    duplicate = True
                    idempotency_redis_hits_total.inc()
                elif settings.use_bloom_idempotency and bloom_maybe_exists:
                    pass
            except Exception:
                if message_hash in _SEEN_HASHES:
                    duplicate = True
        else:
            if message_hash in _SEEN_HASHES:
                duplicate = True
                idempotency_memory_hits_total.inc()
    if settings.enable_db_idempotency:
        try:
            with SESSION_MAKER() as session:
                now_dt = datetime.now(timezone.utc)
                session.execute(text("DELETE FROM idempotency_keys WHERE expires_at < :now"), {"now": now_dt})
                existed = session.execute(text("SELECT 1 FROM idempotency_keys WHERE key=:k"), {"k": message_hash}).first()
                if existed:
                    duplicate = True
                    idempotency_db_hits_total.inc()
                else:
                    exp = now_dt + timedelta(seconds=settings.idempotency_db_ttl_seconds)
                    session.execute(
                        text("INSERT INTO idempotency_keys (key, created_at, expires_at) VALUES (:k, :c, :e)"),
                        {"k": message_hash, "c": now_dt, "e": exp},
                    )
                session.commit()
        except Exception:
            pass
    return duplicate


def _send_to_dlq(message: Dict[str, Any]) -> None:
    try:
        send_to_rabbitmq(queue=DLQ_QUEUE, message=message, rabbitmq_url=RABBITMQ_URL)
        consumer_dlq_total.inc()
    except Exception:
        pass


def callback(ch, method, properties, body):
    tracer = trace.get_tracer("transcription_consumer")
    carrier: Dict[str, str] = {}
    try:
        if getattr(properties, "headers", None):
            for key, value in properties.headers.items():  # type: ignore[attr-defined]
                if isinstance(key, bytes):
                    key = key.decode()
                if isinstance(value, bytes):
                    value = value.decode(errors="ignore")
                carrier[key] = value
    except Exception:
        pass
    ctx = extract(carrier) if carrier else None
    with tracer.start_as_current_span("consume_message", context=ctx) as span:
        logger = _log
        try:
            data: Dict[str, Any] = json.loads(body)
        except Exception as exc:
            span.record_exception(exc)
            logger.error("invalid_payload", error=str(exc))
            consumer_failure_total.inc()
            raw_body = body.decode("utf-8", errors="ignore") if isinstance(body, (bytes, bytearray)) else str(body)
            _send_to_dlq({"raw_body": raw_body, "reason": "invalid_json"})
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        span.set_attribute("filename", data.get("filename", ""))
        started_ts = None
        try:
            started_ts = float(data.get("publish_time"))
        except Exception:
            started_ts = None
        if started_ts:
            e2e_transcription_latency_seconds.observe(max(0, time.time() - started_ts))

        message_hash = _message_hash(data)
        if settings.enable_idempotency and _check_duplicate(message_hash):
            duplicates_skipped_total.inc()
            logger.info("duplicate_skipped", filename=data.get("filename"))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if settings.enable_idempotency and not _redis_client:
            _SEEN_HASHES.append(message_hash)
            if len(_SEEN_HASHES) > settings.idempotency_cache_size:
                drop = max(1, settings.idempotency_cache_size // 10)
                del _SEEN_HASHES[0:drop]

        filename = data.get("filename")
        text_value = data.get("text")
        if not filename or not text_value:
            logger.error("missing_fields", filename=filename)
            consumer_failure_total.inc()
            _send_to_dlq({**data, "reason": "missing_fields"})
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        try:
            enrichment = extract_entities(text_value)
            enrichment_dict = enrichment.to_dict()
        except Exception as exc:
            span.record_exception(exc)
            logger.warning("enrichment_failed", error=str(exc))
            enrichment_dict = {}

        try:
            summary = summarize_text(text_value)
        except Exception as exc:
            span.record_exception(exc)
            logger.warning("summary_failed", error=str(exc))
            summary = None

        with tracer.start_as_current_span("persist_transcript") as pspan:
            pspan.set_attribute("filename", filename)
            record_id = store_transcript(
                filename=filename,
                text=text_value,
                summary=summary,
                enrichment=enrichment_dict,
                source=data.get("source", "api"),
            )

        if record_id <= 0:
            logger.error("persistence_failed", filename=filename)
            consumer_failure_total.inc()
            _send_to_dlq({**data, "reason": "persistence_failed"})
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        transcripts_persisted_total.inc()

        metadata = {
            "source": data.get("source"),
            "correlation_id": data.get("correlation_id"),
            "publish_time": data.get("publish_time"),
            "queue": TRANSCRIPTION_QUEUE,
        }

        store_transcript_payload(
            record_id=record_id,
            filename=filename,
            text=text_value,
            summary=summary,
            enrichment=enrichment_dict,
            metadata=metadata,
        )

        logger.info("transcript_processed", filename=filename, record_id=record_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
def main():
    print(f"[Consumer] Connecting to RabbitMQ at {RABBITMQ_URL}")
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=TRANSCRIPTION_QUEUE, durable=True)
    try:
        q = channel.queue_declare(queue=TRANSCRIPTION_QUEUE, passive=True)
        transcription_queue_depth.set(q.method.message_count)  # type: ignore[attr-defined]
    except Exception:
        pass

    def poll_depth():  # background gauge updater
        while True:
            try:
                q = channel.queue_declare(queue=TRANSCRIPTION_QUEUE, passive=True)
                transcription_queue_depth.set(q.method.message_count)  # type: ignore[attr-defined]
            except Exception:
                pass
            time.sleep(settings.queue_depth_poll_interval)

    threading.Thread(target=poll_depth, daemon=True).start()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=TRANSCRIPTION_QUEUE, on_message_callback=callback)
    print(f"[Consumer] Waiting for transcription messages on '{TRANSCRIPTION_QUEUE}'. Press CTRL+C to exit.")
    channel.start_consuming()


if __name__ == '__main__':
    main()
