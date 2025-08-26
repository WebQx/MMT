import json
from fastapi.testclient import TestClient
import importlib
import os

import main as app_module
from main import issue_internal_jwt
from persistence import save_session
from datetime import datetime, UTC, timedelta
import openemr_consumer as consumer


def _invoke_api_and_consumer(monkeypatch, transcript_text="sample transcript"):
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


def test_end_to_end_fhir_document_reference(monkeypatch):
    import os as _os
    if _os.environ.get("FAST_TEST_MODE") != "1":
        _os.environ["FAST_TEST_MODE"] = "1"
    # Ensure FHIR is enabled
    consumer.settings.openemr_fhir_base_url = "http://example"
    consumer.settings.openemr_fhir_client_id = "cid"
    consumer.settings.openemr_fhir_client_secret = "csecret"
    consumer.settings.openemr_fhir_username = "user"
    consumer.settings.openemr_fhir_password = "pass"

    called = {}

    def fake_create_document_reference(text, filename):
        called["text"] = text
        called["filename"] = filename
        return {"id": "doc-123"}

    def fail_legacy(**kwargs):  # shouldn't be called
        raise AssertionError("Legacy API should not be used when FHIR succeeds")

    monkeypatch.setattr(consumer, "create_document_reference", fake_create_document_reference, raising=True)
    monkeypatch.setattr(consumer, "send_to_openemr_api", fail_legacy, raising=True)

    _invoke_api_and_consumer(monkeypatch)

    assert "SUMMARY:" in called["text"]
    assert "ENRICHMENT:" in called["text"]
    assert called["filename"] == "audio.wav"


def test_end_to_end_legacy_fallback(monkeypatch):
    import os as _os
    if _os.environ.get("FAST_TEST_MODE") != "1":
        _os.environ["FAST_TEST_MODE"] = "1"
    # Disable FHIR
    consumer.settings.openemr_fhir_base_url = None
    consumer.settings.openemr_fhir_client_id = None
    consumer.settings.openemr_fhir_client_secret = None
    consumer.settings.openemr_fhir_username = None
    consumer.settings.openemr_fhir_password = None

    legacy_called = {}

    def fake_legacy_api(filename, text, api_url, api_key):
        legacy_called["filename"] = filename
        legacy_called["text"] = text
        return {"status": "ok"}

    def fail_fhir(*args, **kwargs):  # should not be called
        raise AssertionError("FHIR should not be attempted when disabled")

    monkeypatch.setattr(consumer, "send_to_openemr_api", fake_legacy_api, raising=True)
    monkeypatch.setattr(consumer, "create_document_reference", fail_fhir, raising=True)

    _invoke_api_and_consumer(monkeypatch, transcript_text="another transcript")

    assert legacy_called["filename"] == "audio.wav"
    assert "SUMMARY:" in legacy_called["text"]