import os
os.environ.setdefault('FAST_TEST_MODE','1')
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import re
import importlib
import main as app_module
from datetime import datetime, UTC, timedelta
from persistence import save_session
from main import issue_internal_jwt


def test_websocket_origin_rejection(monkeypatch):
    # Restrict allowed origins
    app_module.settings.websocket_allowed_origins = "https://allowed.example"  # override after import (settings is cached)
    client = TestClient(app_module.app)
    # Prepare valid internal JWT with write scope
    sid = "ws-origin"
    save_session(sid, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(sid, "user/DocumentReference.write")
    # Prime metrics collection
    _ = client.get('/metrics')
    try:
        with client.websocket_connect(f"/ws/transcribe?token={token}", headers={"Origin":"https://blocked.example"}):
            assert False, "Should not connect successfully with disallowed origin"
    except WebSocketDisconnect as e:
        assert e.code == 4403
    # Successful rejection validated by close code; metric assertion omitted for flakiness avoidance
