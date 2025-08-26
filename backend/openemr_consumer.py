import pika
import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
import time
import redis
import threading
from openemr_api import send_to_openemr_api
from dotenv import load_dotenv
from config import get_settings
from persistence import SESSION_MAKER
from sqlalchemy import text
from openemr_fhir import create_document_reference
from entity_extraction import extract_entities, summarize_text
from persistence import store_transcript, update_fhir_id
from rabbitmq_utils import send_to_rabbitmq
import structlog
from metrics import (
    consumer_fhir_success_total,
    consumer_legacy_success_total,
    consumer_failure_total,
    transcripts_persisted_total,
    consumer_dlq_total,
    e2e_transcription_latency_seconds,
    duplicates_skipped_total,
    transcription_queue_depth,
    idempotency_db_hits_total,
    idempotency_redis_hits_total,
    idempotency_memory_hits_total,
)
from opentelemetry import trace  # type: ignore
from opentelemetry.propagate import extract
from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
try:  # optional instrumentation
    RequestsInstrumentor().instrument()
except Exception:  # noqa: BLE001
    pass

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

settings = get_settings()
OPENEMR_API_URL = os.environ.get('OPENEMR_API_URL', 'http://localhost:8080/apis/api')
OPENEMR_API_KEY = os.environ.get('OPENEMR_API_KEY', 'test-api-key')
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

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


def _message_hash(data: dict) -> str:
    m = hashlib.sha256()
    # Use filename + text to derive a deterministic fingerprint
    m.update((data.get("filename", "") + "::" + data.get("text", "")).encode("utf-8"))
    return m.hexdigest()


def callback(ch, method, properties, body):
    tracer = trace.get_tracer("openemr_consumer")
    # Extract upstream context from headers if present
    carrier = {}
    try:
        if getattr(properties, 'headers', None):
            # pika may give headers as dict with byte keys/values
            for k, v in properties.headers.items():  # type: ignore[attr-defined]
                if isinstance(k, bytes):
                    k = k.decode()
                if isinstance(v, bytes):
                    v = v.decode(errors="ignore")
                carrier[k] = v
    except Exception:
        pass
    ctx = extract(carrier) if carrier else None
    with tracer.start_as_current_span("consume_message", context=ctx) as span:
        logger = structlog.get_logger().bind(component="openemr_consumer")
        data = json.loads(body)
        span.set_attribute("filename", data.get("filename", ""))
        started_ts = None
        try:
            # If publisher set a publish_time field (epoch seconds)
            started_ts = float(data.get("publish_time"))
        except Exception:  # noqa: BLE001
            pass
        if started_ts:
            e2e_transcription_latency_seconds.observe(max(0, time.time() - started_ts))

        # Idempotency / duplicate suppression (memory only, reset on restart)
        h = _message_hash(data)
        duplicate = False
        if settings.enable_idempotency:
            if _redis_client:
                try:
                    added = None
                    bloom_maybe_exists = False
                    if settings.use_bloom_idempotency:
                        try:
                            bloom_ret = _redis_client.execute_command("BF.ADD", "idemp_filter", h)  # type: ignore[arg-type]
                            bloom_maybe_exists = (bloom_ret == 0 or bloom_ret == b"0")
                        except Exception:
                            bloom_maybe_exists = False
                    key = f"idemp:{h}"
                    added = _redis_client.set(name=key, value="1", nx=True, ex=settings.idempotency_ttl_seconds)
                    if not added:
                        duplicate = True
                        idempotency_redis_hits_total.inc()
                    elif settings.use_bloom_idempotency and bloom_maybe_exists and not duplicate:
                        pass
                except Exception:  # noqa: BLE001
                    if h in _SEEN_HASHES:
                        duplicate = True
            else:
                if h in _SEEN_HASHES:
                    duplicate = True
                    idempotency_memory_hits_total.inc()
        # Durable DB idempotency layer
        if settings.enable_db_idempotency:
            try:
                with SESSION_MAKER() as session:
                    now_dt = datetime.now(timezone.utc)
                    session.execute(text("DELETE FROM idempotency_keys WHERE expires_at < :now"), {"now": now_dt})
                    existed = session.execute(text("SELECT 1 FROM idempotency_keys WHERE key=:k"), {"k": h}).first()
                    if existed:
                        duplicate = True
                        idempotency_db_hits_total.inc()
                    else:
                        exp = now_dt + timedelta(seconds=settings.idempotency_db_ttl_seconds)
                        session.execute(text("INSERT INTO idempotency_keys (key, created_at, expires_at) VALUES (:k, :c, :e)"), {"k": h, "c": now_dt, "e": exp})
                    session.commit()
            except Exception:
                pass
        if duplicate:
            logger.info("duplicate_skipped", filename=data.get('filename'))
            duplicates_skipped_total.inc()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        if settings.enable_idempotency and not _redis_client:
            _SEEN_HASHES.append(h)
            if len(_SEEN_HASHES) > settings.idempotency_cache_size:
                drop = max(1, settings.idempotency_cache_size // 10)
                del _SEEN_HASHES[0:drop]
        logger.info("received_transcription", filename=data.get('filename'), size=len(data.get('text','')))
        # Enrichment
        enrichment = extract_entities(data['text'])
        summary = summarize_text(data['text'])
        data['enrichment'] = enrichment.to_dict()
        data['summary'] = summary
        with tracer.start_as_current_span("persist_transcript") as pspan:
            pspan.set_attribute("filename", data.get('filename'))
            record_id = store_transcript(
                filename=data['filename'],
                text=data['text'],
                summary=summary,
                enrichment=enrichment.to_dict(),
                source=data.get('source', 'unknown'),
            )
        if record_id > 0:
            transcripts_persisted_total.inc()
        fhir_enabled = all([
            settings.openemr_fhir_base_url,
            settings.openemr_fhir_client_id,
            settings.openemr_fhir_client_secret,
            settings.openemr_fhir_username,
            settings.openemr_fhir_password,
        ])
        if fhir_enabled:
            # Simple circuit breaker parameters
            breaker_allowed = True
            now = time.time()
            open_attr = getattr(callback, '_fhir_cb_open_until', 0)
            failure_count = getattr(callback, '_fhir_cb_failures', 0)
            if now < open_attr:
                breaker_allowed = False
            def record_failure():
                f = getattr(callback, '_fhir_cb_failures', 0) + 1
                setattr(callback, '_fhir_cb_failures', f)
                if f >= 5:  # threshold
                    setattr(callback, '_fhir_cb_open_until', time.time() + 60)  # open 60s
                    setattr(callback, '_fhir_cb_failures', 0)
            if breaker_allowed:
                composite_text = data['text'] + "\n\nSUMMARY:\n" + summary + "\n\nENRICHMENT:\n" + json.dumps(enrichment.to_dict())
                attempt = 0
                max_attempts = 3
                backoff = 1
                while attempt < max_attempts:
                    try:
                        with tracer.start_as_current_span("create_document_reference"):
                            resp = create_document_reference(composite_text, filename=data['filename'])
                        fhir_id = resp.get('id')
                        logger.info("fhir_document_created", id=fhir_id)
                        if fhir_id:
                            update_fhir_id(record_id, fhir_id)
                        consumer_fhir_success_total.inc()
                        setattr(callback, '_fhir_cb_failures', 0)
                        break
                    except Exception as e:  # noqa: BLE001
                        attempt += 1
                        record_failure()
                        span.record_exception(e)
                        logger.warning("fhir_create_failed_attempt", attempt=attempt, error=str(e))
                        if attempt >= max_attempts:
                            # fallback
                            try:
                                with tracer.start_as_current_span("legacy_api_send"):
                                    api_response = send_to_openemr_api(
                                        filename=data['filename'],
                                        text=data['text'] + "\n\nSUMMARY:\n" + summary,
                                        api_url=OPENEMR_API_URL,
                                        api_key=OPENEMR_API_KEY
                                    )
                                logger.info("legacy_api_sent", response_status=api_response)
                                consumer_legacy_success_total.inc()
                            except Exception as e2:  # noqa: BLE001
                                span.record_exception(e2)
                                logger.error("legacy_api_failed", error=str(e2))
                                consumer_failure_total.inc()
                                _send_to_dlq(data)
                        else:
                            time.sleep(backoff)
                            backoff = min(backoff * 2, 8)
            else:
                logger.warning("fhir_circuit_open", retry_at=open_attr)
                # direct fallback
                try:
                    with tracer.start_as_current_span("legacy_api_send"):
                        api_response = send_to_openemr_api(
                            filename=data['filename'],
                            text=data['text'] + "\n\nSUMMARY:\n" + summary,
                            api_url=OPENEMR_API_URL,
                            api_key=OPENEMR_API_KEY
                        )
                    logger.info("legacy_api_sent", response_status=api_response)
                    consumer_legacy_success_total.inc()
                except Exception as e2:  # noqa: BLE001
                    span.record_exception(e2)
                    logger.error("legacy_api_failed", error=str(e2))
                    consumer_failure_total.inc()
                    _send_to_dlq(data)
        else:
            try:
                with tracer.start_as_current_span("legacy_api_send"):
                    api_response = send_to_openemr_api(
                        filename=data['filename'],
                        text=data['text'] + "\n\nSUMMARY:\n" + summary,
                        api_url=OPENEMR_API_URL,
                        api_key=OPENEMR_API_KEY
                    )
                logger.info("legacy_api_sent", response_status=api_response)
                consumer_legacy_success_total.inc()
            except Exception as e:  # noqa: BLE001
                span.record_exception(e)
                logger.error("legacy_api_failed", error=str(e))
                consumer_failure_total.inc()
                _send_to_dlq(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)


def _send_to_dlq(message: dict):
    """Publish failed message to a dead-letter queue.

    Best-effort only; swallow all exceptions to avoid recursive failure.
    """
    try:
        send_to_rabbitmq(
            queue='openemr_transcriptions_dlq',
            message=message,
            rabbitmq_url=RABBITMQ_URL,
        )
        consumer_dlq_total.inc()
    except Exception:  # noqa: BLE001
        return

def main():
    print(f"[OpenEMR] Connecting to RabbitMQ at {RABBITMQ_URL}")
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue='openemr_transcriptions', durable=True)
    try:
        q = channel.queue_declare(queue='openemr_transcriptions', passive=True)
        transcription_queue_depth.set(q.method.message_count)  # type: ignore[attr-defined]
    except Exception:
        pass

    def poll_depth():  # background gauge updater
        while True:
            try:
                q = channel.queue_declare(queue='openemr_transcriptions', passive=True)
                transcription_queue_depth.set(q.method.message_count)  # type: ignore[attr-defined]
            except Exception:
                pass
            time.sleep(get_settings().queue_depth_poll_interval)

    threading.Thread(target=poll_depth, daemon=True).start()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='openemr_transcriptions', on_message_callback=callback)
    print('[OpenEMR] Waiting for transcription messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main()
