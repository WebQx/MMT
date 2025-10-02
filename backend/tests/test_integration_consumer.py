import json
from fastapi.testclient import TestClient
import importlib
import os

import main as app_module
from main import issue_internal_jwt
from persistence import save_session
from datetime import datetime, UTC, timedelta
import openemr_consumer as consumer


def _invoke_api_and_consumer(monkeypatch, transcript_text="sample transcript", nextcloud_calls=None):
    # Avoid heavy model load in integration tests
    import os as _os
    _os.environ["FAST_TEST_MODE"] = "1"
    client = TestClient(app_module.app)
    # Allow guest writes for legacy test simplicity
    app_module.settings.allow_guest_auth = True
    app_module.settings.force_sync_publish = True
    # Ensure idempotency does not short-circuit consumer logic between tests
    try:
        consumer.settings.enable_idempotency = False
        if hasattr(consumer, "_SEEN_HASHES"):
            consumer._SEEN_HASHES.clear()  # type: ignore[attr-defined]
    except Exception:
        pass

    # Monkeypatch transcription to bypass heavy model
    def fake_transcribe_local(data, filename, mime):
        return transcript_text

    monkeypatch.setattr(app_module, "transcribe_local", fake_transcribe_local, raising=True)

    monkeypatch.setattr(
        consumer,
        "extract_entities",
        lambda text: type("E", (), {"to_dict": lambda self: {}})(),
        raising=True,
    )
    monkeypatch.setattr(consumer, "summarize_text", lambda text: "summary", raising=True)

    if nextcloud_calls is not None:
        def fake_store_payload(**kwargs):
            nextcloud_calls.append(kwargs)
        monkeypatch.setattr(consumer, "store_transcript_payload", fake_store_payload, raising=True)
    else:
        monkeypatch.setattr(consumer, "store_transcript_payload", lambda **k: None, raising=True)

    # Monkeypatch queue publish to synchronously invoke consumer callback
    def fake_send(queue, message, rabbitmq_url=None):
        body = json.dumps(message).encode()

        class DummyChannel:
            def basic_ack(self, delivery_tag):
                pass

        class DummyMethod:
            delivery_tag = 1

        consumer.callback(DummyChannel(), DummyMethod(), None, body)

    monkeypatch.setattr(app_module, "send_to_rabbitmq", fake_send, raising=True)

    # Create SMART session record and internal JWT with write scope
    session_id = "test-session"
    save_session(session_id, "user/DocumentReference.write", "dummy_access", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")
    resp = client.post(
        "/transcribe/local/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("audio.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp.status_code == 200, resp.text


def test_end_to_end_nextcloud_upload(monkeypatch):
    calls = []
    _invoke_api_and_consumer(monkeypatch, transcript_text="nextcloud body", nextcloud_calls=calls)
    assert calls, "store_transcript_payload should be invoked"
    payload = calls[0]
    assert payload["filename"] == "audio.wav"
    assert payload["text"] == "nextcloud body"
    assert payload["summary"] == "summary"
    assert isinstance(payload["enrichment"], dict)
    assert payload["metadata"]["queue"] == consumer.TRANSCRIPTION_QUEUE