import base64
from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient
import main as app_module
from persistence import save_session
from main import issue_internal_jwt


def test_jwks_and_old_secret(monkeypatch):
    # Setup: simulate an old secret plus current secret (HS256 path)
    app_module.settings.use_rsa_internal_jwt = False
    app_module.settings.internal_jwt_old_secrets = "oldsecret123"  # type: ignore[attr-defined]
    app_module.settings.internal_jwt_secret = "newsecret456"  # type: ignore[attr-defined]

    client = TestClient(app_module.app)
    session_id = "rot-test"
    save_session(session_id, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))

    # Token with new secret
    new_token = issue_internal_jwt(session_id, "user/DocumentReference.write")
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_resp.status_code == 200

    # Manually craft token with old secret by monkeypatching setting temporarily
    old_secret = "oldsecret123"
    app_module.settings.internal_jwt_secret = old_secret  # rotate signer to old value
    old_token = issue_internal_jwt(session_id, "user/DocumentReference.write")

    # Restore new secret as active so verification must succeed via old list
    app_module.settings.internal_jwt_secret = "newsecret456"

    me_old = client.get("/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me_old.status_code == 200, me_old.text

    # JWKS listing includes both keys (as oct entries)
    jwks = client.get("/.well-known/jwks.json").json()
    assert len(jwks.get("keys", [])) >= 2
