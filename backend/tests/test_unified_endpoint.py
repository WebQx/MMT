import os
os.environ.setdefault('FAST_TEST_MODE','1')
import json
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta
from persistence import save_session
import main as app_module
from main import issue_internal_jwt


def test_ambient_unified(monkeypatch):
    app_module.settings.force_sync_publish = True
    client = TestClient(app_module.app)
    # SMART session with write scope
    sid = "ambient-session"
    save_session(sid, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(sid, "user/DocumentReference.write")
    resp = client.post(
        "/transcribe/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        content=json.dumps({"text": "ambient hello world", "mode": "ambient"}),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ambient"] is True
    assert "hello world" in body["text"].lower()


def test_external_jwt_role_mapping(monkeypatch):
    # Simulate external Keycloak token with realm_access.roles
    client = TestClient(app_module.app)
    # Craft unsigned token accepted by disabled verification (monkeypatch verify_external_jwt)
    external_payload = {"realm_access": {"roles": [app_module.settings.keycloak_writer_role or "writer"]}}
    def fake_verify(token: str):
        return external_payload
    monkeypatch.setattr(app_module, "verify_external_jwt", fake_verify, raising=True)
    # Dummy bearer
    token = "external.dummy.token"
    # Call unified ambient (will require write scope via role)
    resp = client.post(
        "/transcribe/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        content=json.dumps({"text": "ext ambient", "mode": "ambient"}),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json().get("ambient") is True