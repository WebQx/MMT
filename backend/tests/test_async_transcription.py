from fastapi.testclient import TestClient
import main as app_module
from main import issue_internal_jwt
from persistence import save_session
from datetime import datetime, UTC, timedelta
import time


def test_async_local_transcription(monkeypatch):
    client = TestClient(app_module.app)
    sid = 'async1'
    save_session(sid, 'user/DocumentReference.write user/DocumentReference.read', 'access', None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(sid, 'user/DocumentReference.write user/DocumentReference.read')

    def fake_transcribe_local(data, filename, mime):
        return 'async text'
    monkeypatch.setattr(app_module, 'transcribe_local', fake_transcribe_local, raising=True)
    monkeypatch.setattr(app_module, '_publish_transcription', lambda *a, **k: None, raising=True)

    resp = client.post('/transcribe/local/?async_mode=true', headers={'Authorization': f'Bearer {token}'}, files={'file':('a.wav', b'RIFF....data', 'audio/wav')})
    assert resp.status_code == 202
    task_id = resp.json()['task_id']
    # poll
    for _ in range(10):
        r2 = client.get(f'/transcribe/local/task/{task_id}', headers={'Authorization': f'Bearer {token}'})
        assert r2.status_code == 200
        js = r2.json()
        if js['status'] == 'done':
            assert js['text'] == 'async text'
            break
        time.sleep(0.1)
    else:
        raise AssertionError('Async transcription did not finish')