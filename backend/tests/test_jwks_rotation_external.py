import os
import json
import base64
import time
from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import main as app_module
from persistence import save_session
from main import issue_internal_jwt

# Utility to build minimal RSA key pair for JWKS
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def _gen_rsa():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub = key.public_key()
    pub_numbers = pub.public_numbers()
    n = pub_numbers.n
    e = pub_numbers.e
    def b64u(i: int):
        b = i.to_bytes((i.bit_length()+7)//8, 'big')
        return base64.urlsafe_b64encode(b).decode().rstrip('=')
    jwk = {"kty":"RSA","alg":"RS256","use":"sig","kid": base64.urlsafe_b64encode(os.urandom(8)).decode().rstrip('='), "n": b64u(n), "e": b64u(e)}
    pub_pem = pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv_pem, pub_pem, jwk

class _JWKSHandler(BaseHTTPRequestHandler):
    jwks_payload = {"keys": []}
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(self.jwks_payload).encode())
    def log_message(self, *a, **kw):  # silence
        pass


def test_external_jwks_rotation(monkeypatch):
    # Generate two keys to simulate rotation; start serving first only
    priv1, pub1, jwk1 = _gen_rsa()
    priv2, pub2, jwk2 = _gen_rsa()

    # Minimal external token issuance: build unsigned header+payload then sign manually with selected private key
    from jose import jwt as pyjwt
    issuer = "https://issuer.example"

    # configure settings for external jwks
    app_module.settings.keycloak_issuer = issuer
    # start tiny HTTP server in background thread
    server = HTTPServer(('127.0.0.1', 0), _JWKSHandler)
    host, port = server.server_address
    url = f"http://{host}:{port}/jwks"
    app_module.settings.keycloak_jwks_url = url
    app_module.settings.keycloak_jwks_refresh_seconds = 1  # fast refresh

    _JWKSHandler.jwks_payload = {"keys": [jwk1]}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Force initial refresh
    from main import _refresh_jwks  # type: ignore
    _refresh_jwks(initial=True)

    client = TestClient(app_module.app)

    # Build token signed with key1
    token1 = pyjwt.encode({"sub":"user","realm_access":{"roles":[app_module.settings.keycloak_writer_role]} ,"iss":issuer}, priv1, algorithm="RS256", headers={"kid": jwk1['kid']})

    # Monkeypatch external verification to ensure using real function
    from main import verify_external_jwt as real_verify
    # Validate token1 accepted
    resp = client.post("/transcribe/", headers={"Authorization": f"Bearer {token1}", "Content-Type":"application/json"}, json={"text":"hello rotation","mode":"ambient"})
    assert resp.status_code == 200, resp.text

    # Rotate JWKS to only key2
    _JWKSHandler.jwks_payload = {"keys": [jwk2]}
    # wait for refresh loop to pick up (call refresh directly for determinism)
    _refresh_jwks()

    # Build token signed with key2
    token2 = pyjwt.encode({"sub":"user2","realm_access":{"roles":[app_module.settings.keycloak_writer_role]} ,"iss":issuer}, priv2, algorithm="RS256", headers={"kid": jwk2['kid']})
    resp2 = client.post("/transcribe/", headers={"Authorization": f"Bearer {token2}", "Content-Type":"application/json"}, json={"text":"hello rotation 2","mode":"ambient"})
    assert resp2.status_code == 200, resp2.text

    server.shutdown()
