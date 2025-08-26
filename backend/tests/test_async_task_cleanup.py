import time
from datetime import datetime, UTC, timedelta
import main as app_module
from persistence import save_session, async_task_create, async_task_update
from fastapi.testclient import TestClient
from main import issue_internal_jwt

def test_async_task_cleanup(monkeypatch):
    # Force retention to 0 days to skip if not set, so set to 1 second effective by monkeypatching settings
    app_module.settings.async_task_retention_days = 0  # ensure cleanup requires override
    # Create stale task
    async_task_create('oldtask', 'f.wav')
    # Manually backdate updated_at via direct engine execute
    from sqlalchemy import text as _text
    from persistence import ENGINE
    with ENGINE.begin() as conn:
        conn.execute(_text("update async_tasks set updated_at=:ts"), {"ts": datetime.now(UTC) - timedelta(days=10)})
    app_module.settings.async_task_retention_days = 7
    purged = app_module.cleanup_async_tasks_once()
    assert purged >= 1

def test_breaker_metrics(monkeypatch):
    client = TestClient(app_module.app)
    sid = 'brk1'
    save_session(sid, 'user/DocumentReference.write user/DocumentReference.read', 'tok', None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(sid, 'user/DocumentReference.write user/DocumentReference.read')
    # Force send_to_rabbitmq to fail
    def fail_send(*a, **k):
        raise RuntimeError('rmq down')
    monkeypatch.setattr(app_module, 'send_to_rabbitmq', fail_send, raising=True)
    app_module._CB_THRESHOLD = 1
    r = client.post('/transcribe/local/?async_mode=false', headers={'Authorization': f'Bearer {token}'}, files={'file':('f.wav', b'RIFF....data', 'audio/wav')})
    assert r.status_code in (500,503)
    # Circuit should open next attempt and fallback
    app_module._cb_open_until = time.time() + 60
    r2 = client.post('/transcribe/local/?async_mode=false', headers={'Authorization': f'Bearer {token}'}, files={'file':('f.wav', b'RIFF....data', 'audio/wav')})
    assert r2.status_code in (200,500,503)
    # Metrics endpoint scrape to ensure metrics emitted
    m = client.get('/metrics')
    body = m.text
    assert 'breaker_open_total' in body or 'breaker_fallback_persist_total' in body
