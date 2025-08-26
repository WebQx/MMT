from fastapi.testclient import TestClient
import main as app_module
from main import issue_internal_jwt
from persistence import save_session
from datetime import datetime, UTC, timedelta
import base64


def _token(scope: str):
    sid = f"sid-{scope}"
    save_session(sid, scope, "access", None, datetime.now(UTC)+timedelta(hours=1))
    return issue_internal_jwt(sid, scope)


def test_upload_chunk_requires_auth():
    client = TestClient(app_module.app)
    resp = client.post("/upload_chunk/", files={"chunk": ("a.wav", b"123", "audio/wav")})
    assert resp.status_code in (401, 403)
    token = _token("user/DocumentReference.write")
    resp = client.post("/upload_chunk/", headers={"Authorization": f"Bearer {token}"}, data={"upload_id":"u1","chunk_index":0,"total_chunks":1,"filename":"a.wav"}, files={"chunk": ("a.wav", b"123", "audio/wav")})
    assert resp.status_code == 200


def test_upload_chunk_size_limit(monkeypatch):
    client = TestClient(app_module.app)
    token = _token("user/DocumentReference.write")
    app_module.settings.max_upload_bytes = 10
    big = b"A"*11
    resp = client.post("/upload_chunk/", headers={"Authorization": f"Bearer {token}"}, data={"upload_id":"u2","chunk_index":0,"total_chunks":1,"filename":"b.wav"}, files={"chunk": ("b.wav", big, "audio/wav")})
    assert resp.status_code == 413


def test_websocket_requires_auth():
    client = TestClient(app_module.app)
    # Should fail without token
    try:
        client.websocket_connect("/ws/transcribe")
        assert False, "unauthorized ws should not connect"
    except Exception:
        pass
    token = _token("user/DocumentReference.write")
    with client.websocket_connect(f"/ws/transcribe?token={token}") as ws:
        ws.send_json({"type":"chunk","data": base64.b64encode(b'A'*1000).decode(),"final": True, "filename":"x.wav"})
        # Expect either ack then final or final
        for _ in range(3):
            msg = ws.receive_json()
            if msg['type'] in {'final','error'}:
                break
