import json
import os
from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient
import pytest

import main as app_module
from main import issue_internal_jwt
from persistence import save_session
import openemr_consumer as consumer
from metrics import duplicates_skipped_total
import redis


def test_duplicate_suppression(monkeypatch):
    import os as _os
    _os.environ["FAST_TEST_MODE"] = "1"
    # Ensure idempotency enabled
    consumer.settings.enable_idempotency = True
    consumer.settings.enable_db_idempotency = False
    # Use in-memory path (no redis)
    consumer._redis_client = None  # type: ignore[attr-defined]
    monkeypatch.setattr(consumer, "store_transcript", lambda **k: 1, raising=False)
    monkeypatch.setattr(
        consumer,
        "extract_entities",
        lambda text: type("E", (), {"to_dict": lambda self: {}})(),
        raising=False,
    )
    monkeypatch.setattr(consumer, "summarize_text", lambda text: "summary", raising=False)
    monkeypatch.setattr(consumer, "store_transcript_payload", lambda **k: None, raising=False)

    client = TestClient(app_module.app)
    session_id = "dup-test"
    app_module.settings.force_sync_publish = True
    save_session(session_id, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")

    # Track baseline metric value
    before = duplicates_skipped_total._value.get()  # type: ignore[attr-defined]

    # Monkeypatch transcription to avoid heavy work
    def fake_transcribe_local(data, filename, mime):
        return "same text"
    monkeypatch.setattr(app_module, "transcribe_local", fake_transcribe_local, raising=True)

    # Monkeypatch publisher to directly call consumer
    def fake_send(queue, message, rabbitmq_url=None):
        body = json.dumps(message).encode()
        class DummyChannel:
            def basic_ack(self, delivery_tag):
                pass
        class DummyMethod:
            delivery_tag = 1
        consumer.callback(DummyChannel(), DummyMethod(), None, body)
    monkeypatch.setattr(app_module, "send_to_rabbitmq", fake_send, raising=True)

    # First request (should process)
    resp1 = client.post(
        "/transcribe/local/?async_mode=false",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("audio.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp1.status_code == 200
    # Second identical request (should be skipped as duplicate in consumer)
    # Ensure in-memory seen hashes list retains first hash
    resp2 = client.post(
        "/transcribe/local/?async_mode=false",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("audio.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp2.status_code == 200

    after = duplicates_skipped_total._value.get()  # type: ignore[attr-defined]
    assert after == before + 1, f"Expected duplicates_skipped_total to increment by 1 (before={before}, after={after})"
    # Reset for other tests
    consumer.settings.enable_idempotency = False
    if hasattr(consumer, "_SEEN_HASHES"):
        try:
            consumer._SEEN_HASHES.clear()  # type: ignore[attr-defined]
        except Exception:
            pass


@pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="REDIS_URL not set; skipping Redis idempotency integration test")
def test_duplicate_suppression_redis(monkeypatch):
    consumer.settings.enable_idempotency = True
    url = os.environ.get("REDIS_URL")
    r = redis.StrictRedis.from_url(url, decode_responses=True)
    r.flushdb()
    consumer._redis_client = r  # type: ignore[attr-defined]
    monkeypatch.setattr(consumer, "store_transcript", lambda **k: 1, raising=False)
    monkeypatch.setattr(
        consumer,
        "extract_entities",
        lambda text: type("E", (), {"to_dict": lambda self: {}})(),
        raising=False,
    )
    monkeypatch.setattr(consumer, "summarize_text", lambda text: "summary", raising=False)
    monkeypatch.setattr(consumer, "store_transcript_payload", lambda **k: None, raising=False)
    client = TestClient(app_module.app)
    session_id = "dup-test-redis"
    save_session(session_id, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")
    before = duplicates_skipped_total._value.get()  # type: ignore[attr-defined]

    def fake_transcribe_local(data, filename, mime):
        return "same redis text"
    monkeypatch.setattr(app_module, "transcribe_local", fake_transcribe_local, raising=True)

    def fake_send(queue, message, rabbitmq_url=None):
        body = json.dumps(message).encode()
        class DummyChannel:
            def basic_ack(self, delivery_tag):
                pass
        class DummyMethod:
            delivery_tag = 1
        consumer.callback(DummyChannel(), DummyMethod(), None, body)
    monkeypatch.setattr(app_module, "send_to_rabbitmq", fake_send, raising=True)

    resp1 = client.post(
        "/transcribe/local/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("audio.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp1.status_code == 200
    resp2 = client.post(
        "/transcribe/local/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("audio.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp2.status_code == 200
    after = duplicates_skipped_total._value.get()  # type: ignore[attr-defined]
    assert after == before + 1
