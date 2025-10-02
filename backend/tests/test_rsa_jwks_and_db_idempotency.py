import os, json, base64
import pytest
from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient

import main as app_module
from main import issue_internal_jwt
from persistence import save_session, SessionLocal
from sqlalchemy import text


def _generate_rsa_keys():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv_pem, pub_pem


def test_rsa_jwks_and_db_idempotency(monkeypatch):
    priv, pub = _generate_rsa_keys()
    app_module.settings.use_rsa_internal_jwt = True  # type: ignore[attr-defined]
    app_module.settings.internal_jwt_private_key_pem = priv  # type: ignore[attr-defined]
    app_module.settings.internal_jwt_public_key_pem = pub  # type: ignore[attr-defined]
    app_module.settings.enable_db_idempotency = True  # type: ignore[attr-defined]
    # shorten TTL for test
    app_module.settings.idempotency_db_ttl_seconds = 60  # type: ignore[attr-defined]

    client = TestClient(app_module.app)
    session_id = "rsa-test"
    save_session(session_id, "user/DocumentReference.write", "dummy", None, datetime.now(UTC)+timedelta(hours=1))
    token = issue_internal_jwt(session_id, "user/DocumentReference.write")

    jwks = client.get('/.well-known/jwks.json').json()
    assert jwks['keys'] and jwks['keys'][0]['kty'] == 'RSA'
    # ensure n and e present and look base64url (no '=')
    n = jwks['keys'][0]['n']
    e = jwks['keys'][0]['e']
    assert isinstance(n, str) and isinstance(e, str) and '=' not in n and '=' not in e

    # Force direct consumer invocation to test DB idempotency duplicate path
    import openemr_consumer as consumer
    consumer.settings.enable_idempotency = False  # isolate DB layer
    consumer.settings.enable_db_idempotency = True
    consumer._redis_client = None  # type: ignore[attr-defined]
    monkeypatch.setattr(consumer, "store_transcript_payload", lambda **k: None, raising=False)
    monkeypatch.setattr(
        consumer,
        "extract_entities",
        lambda text: type("E", (), {"to_dict": lambda self: {}})(),
        raising=False,
    )
    monkeypatch.setattr(consumer, "summarize_text", lambda text: "summary", raising=False)

    payload = {"filename": "f.wav", "text": "hello world", "source": "api"}
    body = json.dumps(payload).encode()
    class DummyChannel:
        def basic_ack(self, delivery_tag):
            pass
    class DummyMethod:
        delivery_tag = 1

    # First consume inserts key
    consumer.callback(DummyChannel(), DummyMethod(), None, body)
    # Second consume should hit DB duplicate path (no Redis)
    consumer.callback(DummyChannel(), DummyMethod(), None, body)

    # Verify duplicate exists in table only once
    with SessionLocal() as session:
        rows = session.execute(text("SELECT count(*) FROM idempotency_keys")).scalar()
        assert rows == 1

    # JWKS token validation round-trip
    me_resp = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_resp.status_code == 200
