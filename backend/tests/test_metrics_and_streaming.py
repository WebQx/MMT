from fastapi.testclient import TestClient
import main as app_module
from main import issue_internal_jwt
from persistence import save_session
from datetime import datetime, UTC, timedelta
import base64


def test_metrics_after_publish(monkeypatch):
    client = TestClient(app_module.app)
    app_module.settings.allow_guest_auth = True

    def fake_transcribe_local(data, filename, mime):
        return "hello world"

    monkeypatch.setattr(app_module, "transcribe_local", fake_transcribe_local, raising=True)
    # Bypass actual RabbitMQ
    def fake_send(queue, message, rabbitmq_url=None):
        return None
    monkeypatch.setattr(app_module, "send_to_rabbitmq", fake_send, raising=True)
    session_id = "metrics-session"
    save_session(session_id, "user/DocumentReference.write", "dummy_access", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")
    resp = client.post(
        "/transcribe/local/?async_mode=false",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sample.wav", b"RIFF....data", "audio/wav")},
    )
    assert resp.status_code == 200
    metrics = client.get("/metrics").text
    assert "transcripts_published_total" in metrics


def test_partial_streaming(monkeypatch):
    app_module.settings.enable_partial_streaming = True  # enable
    client = TestClient(app_module.app)
    session_id = "ws-session"
    save_session(session_id, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")

    def fake_transcribe_local(data, filename, mime):
        return "partial result"

    monkeypatch.setattr(app_module, "transcribe_local", fake_transcribe_local, raising=True)

    with client.websocket_connect(f"/ws/transcribe?token={token}") as ws:
        ws.send_json({"type": "chunk", "data": base64.b64encode(b'A'*5000).decode(), "final": False, "filename": "x.wav"})
        ws.receive_json()  # ack
        ws.send_json({"type": "chunk", "data": base64.b64encode(b'A'*5000).decode(), "final": False, "filename": "x.wav"})
        ws.receive_json()  # ack or partial
        msg = ws.receive_json()
        assert msg["type"] in {"partial", "ack", "final"}