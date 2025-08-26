import pytest
from fastapi.testclient import TestClient
import importlib


def test_publish_retry(monkeypatch):
    # Force guest auth to simplify
    monkeypatch.setenv('ALLOW_GUEST_AUTH', 'true')
    # Monkeypatch send_to_rabbitmq to fail twice then succeed
    import rabbitmq_utils
    calls = {'n':0}
    def fake_send_to_rabbitmq(queue, message, rabbitmq_url):
        calls['n'] += 1
        if calls['n'] < 3:
            raise RuntimeError('temp failure')
    monkeypatch.setattr(rabbitmq_utils, 'send_to_rabbitmq', fake_send_to_rabbitmq)
    import main as app_module
    importlib.reload(app_module)
    client = TestClient(app_module.app)
    # Override dependency for get_current_user
    def fake_user_dep():
        return {"role": "writer"}
    app_module.app.dependency_overrides[app_module.get_current_user] = fake_user_dep
    resp = client.post('/transcribe/cloud/', json={'text':'hello'}, headers={'Authorization':'Bearer test'})
    assert resp.status_code == 200
    assert calls['n'] == 3
