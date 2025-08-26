"""MMT transcription backend FastAPI app.

Refactored for modularity: cloud + local transcription services, RabbitMQ publishing,
and simple auth (guest / Keycloak JWT passthrough).
"""

from __future__ import annotations

import os
import mimetypes
import subprocess
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import hashlib
import base64
from cryptography.hazmat.primitives import serialization
from typing import List
import secrets

from config import get_settings
from audit import audit, AuditEvent
from audit import mask_phi_for_response
from openemr_smart import build_authorize_url, exchange_code, get_session_token, refresh_session
from logging_setup import configure_logging  # noqa: F401 side-effect import
from middleware import CorrelationIdMiddleware
from rate_limit import RateLimitMiddleware
from persistence import get_transcript
from persistence import rotate_encryption_keys
from metrics import (
    transcripts_published_total,
    websocket_partial_sent_total,
    transcription_duration_seconds,
    transcription_queue_depth,
    vault_refresh_failures_total,
    vault_token_renew_success_total,
    vault_token_renew_failures_total,
    api_requests_total,
    api_request_duration_seconds,
    api_in_flight_requests,
    decryption_warnings_total,
    publish_failures_total,
    breaker_open_total,
    breaker_fallback_persist_total,
    async_tasks_started_total,
    async_tasks_completed_total,
    async_tasks_failed_total,
    async_task_duration_seconds,
    async_task_queue_size,
    drain_start_total,
    websocket_rejected_total,
    jwks_refresh_total,
    jwks_keys_active,
    phi_redactions_total,
)
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog
from audit import _request_id_var, _user_role_var  # type: ignore
import os as _os
from rabbitmq_utils import send_to_rabbitmq
from opentelemetry import trace
from transcription_services import transcribe_cloud, transcribe_local, ALLOWED_MIME_TYPES, preload_models_if_configured
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
import base64
import json
import time
from postprocess import normalize_text
import threading
import requests as _requests
from threading import RLock

# JWKS caching (external Keycloak)
_jwks_lock = RLock()
_jwks_keys: list[dict] = []  # cached JWKS keys

def _refresh_jwks(initial: bool = False):
    if not settings.keycloak_jwks_url:
        return
    try:
        resp = _requests.get(settings.keycloak_jwks_url, timeout=5)
        if resp.status_code != 200:
            jwks_refresh_total.labels(status="fail").inc()
            return
        payload = resp.json()
        keys = payload.get("keys", []) if isinstance(payload, dict) else []
        if not isinstance(keys, list):
            jwks_refresh_total.labels(status="fail").inc()
            return
        with _jwks_lock:
            _jwks_keys.clear()
            _jwks_keys.extend(keys)
            jwks_keys_active.set(len(_jwks_keys))
        jwks_refresh_total.labels(status="success").inc()
    except Exception:  # noqa: BLE001
        jwks_refresh_total.labels(status="fail").inc()


def _jwks_background_loop():  # pragma: no cover
    while True:
        try:
            _refresh_jwks()
        except Exception:
            pass
        time.sleep(max(30, settings.keycloak_jwks_refresh_seconds))

__all__ = ["app", "issue_internal_jwt"]

settings = get_settings()
_vault_lock = threading.Lock()
if settings.sentry_dsn:  # Sentry telemetry (optional)
    try:
        import sentry_sdk  # type: ignore
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment_name, release=settings.app_version, traces_sample_rate=settings.sentry_traces_sample_rate)
    except Exception:  # noqa: BLE001
        structlog.get_logger(__name__).warning("sentry/init_failed")

def _load_rsa_keys_from_vault(initial: bool = False):
    if not settings.vault_addr or not settings.vault_rsa_secret_path:
        return
    # Ensure we have a token (AppRole if needed)
    if not settings.vault_token and settings.vault_role_id and settings.vault_secret_id:
        try:
            auth_url = settings.vault_addr.rstrip('/') + "/v1/auth/approle/login"
            resp = _requests.post(auth_url, json={"role_id": settings.vault_role_id, "secret_id": settings.vault_secret_id}, timeout=5)
            if resp.status_code == 200:
                new_token = resp.json().get("auth", {}).get("client_token")
                if new_token:
                    settings.vault_token = new_token  # type: ignore[attr-defined]
        except Exception:
            return
    if not settings.vault_token:
        return
    url = settings.vault_addr.rstrip('/') + f"/v1/{settings.vault_rsa_secret_path}"
    try:
        resp = _requests.get(url, headers={"X-Vault-Token": settings.vault_token}, timeout=5)
        if resp.status_code != 200:
            structlog.get_logger(__name__).warning("vault/key-fetch-failed", status=resp.status_code, initial=initial)
            return
        data = resp.json().get("data") or resp.json()
        # kv v2 nests under data.data
        if "data" in data:
            data = data["data"]
        priv = data.get("private_key_pem")
        pub = data.get("public_key_pem")
        if priv and pub:
            with _vault_lock:
                settings.internal_jwt_private_key_pem = priv  # type: ignore[attr-defined]
                settings.internal_jwt_public_key_pem = pub  # type: ignore[attr-defined]
    except Exception as e:
        structlog.get_logger(__name__).warning("vault/key-fetch-exception", error=str(e), initial=initial)
        return

def _renew_token_if_needed():
    """Renew Vault token if present; record metrics. Non-fatal on failure."""
    if not settings.vault_token:
        return
    if not settings.vault_addr:
        return
    try:
        renew_url = settings.vault_addr.rstrip('/') + "/v1/auth/token/renew-self"
        resp = _requests.post(renew_url, headers={"X-Vault-Token": settings.vault_token}, timeout=5)
        if resp.status_code == 200:
            vault_token_renew_success_total.inc()
        else:
            vault_token_renew_failures_total.inc()
    except Exception:
        vault_token_renew_failures_total.inc()

def _start_vault_refresh_thread():
    if not settings.use_rsa_internal_jwt:
        return
    if not (settings.vault_addr and settings.vault_rsa_secret_path):
        return
    interval = getattr(settings, 'vault_rsa_refresh_seconds', 300)
    def _loop():
        backoff = 5
        while True:
            try:
                _renew_token_if_needed()
                _load_rsa_keys_from_vault()
                backoff = 5  # reset on success
            except Exception:
                vault_refresh_failures_total.inc()
                backoff = min(backoff * 2, 300)
            sleep_for = interval if backoff == 5 else backoff
            time.sleep(sleep_for)
    t = threading.Thread(target=_loop, name="vault-rsa-refresh", daemon=True)
    t.start()

_load_rsa_keys_from_vault(initial=True)
_start_vault_refresh_thread()

# Encryption rotation background thread (optional)
def _start_rotation_thread():
    try:
        from config import get_settings as _gs
        s = _gs()
        if not s.enable_field_encryption or s.encryption_rotate_hours <= 0:
            return
        interval = max(1, s.encryption_rotate_hours) * 3600
        def _loop():
            import time as _t
            while True:
                try:
                    rotate_encryption_keys()
                except Exception:
                    pass
                _t.sleep(interval)
        threading.Thread(target=_loop, name="encryption-rotate", daemon=True).start()
    except Exception:
        pass

_start_rotation_thread()

# Optional OpenTelemetry auto-instrumentation (if OTEL_EXPORTER_OTLP_ENDPOINT provided)
if _os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    try:  # noqa: SIM105
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from persistence import ENGINE

        resource = Resource.create({
            "service.name": "mmt-transcription-api",
            "service.version": settings.app_version,
            "deployment.environment": settings.environment_name,
        })
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        RequestsInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument(engine=ENGINE.sync_engine if hasattr(ENGINE, 'sync_engine') else ENGINE)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

docs_enabled = os.environ.get('ENV','dev') != 'prod'
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import queue as _queue

_shutdown_flag = False
_executor_max_workers = getattr(settings, 'async_max_workers', int(os.environ.get('LOCAL_TX_WORKERS','2')))
_executor_queue_maxsize = getattr(settings, 'async_queue_maxsize', 50)
_submission_queue: "_queue.Queue[tuple[callable, tuple, dict]]" = _queue.Queue(maxsize=_executor_queue_maxsize)
_tx_executor = ThreadPoolExecutor(max_workers=_executor_max_workers)

def _executor_dispatch_loop():
    while not _shutdown_flag:
        try:
            fn, a, kw = _submission_queue.get(timeout=0.5)
        except _queue.Empty:
            continue
        try:
            _tx_executor.submit(fn, *a, **kw)
        except Exception:
            pass
        finally:
            try:
                async_task_queue_size.set(_submission_queue.qsize())
            except Exception:
                pass
            _submission_queue.task_done()

threading.Thread(target=_executor_dispatch_loop, daemon=True, name="async-dispatch").start()

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    if os.environ.get('FAST_TEST_MODE') != '1':
        preload_models_if_configured()
    _start_migration_revision_check()
    _start_retention_thread()
    yield
    global _draining, _shutdown_flag
    _draining = True
    _shutdown_flag = True
    _tx_executor.shutdown(wait=True, cancel_futures=False)

app = FastAPI(title="MMT Transcription API", version="0.1.0", docs_url="/docs" if docs_enabled else None, redoc_url=None if not docs_enabled else "/redoc", lifespan=lifespan)

@app.exception_handler(HTTPException)
async def _http_exc_handler(request: Request, exc: HTTPException):  # type: ignore[override]
    cid = getattr(request.state, 'correlation_id', None)
    body = {"error": {"code": exc.status_code, "message": exc.detail}, "correlation_id": cid}
    if exc.headers:
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)
    return JSONResponse(status_code=exc.status_code, content=body)

@app.exception_handler(Exception)
async def _unhandled_exc_handler(request: Request, exc: Exception):  # type: ignore[override]
    cid = getattr(request.state, 'correlation_id', None)
    structlog.get_logger(__name__).exception("unhandled_error", correlation_id=cid)
    body = {"error": {"code": 500, "message": "Internal Server Error"}, "correlation_id": cid}
    return JSONResponse(status_code=500, content=body)
if 'trace' in globals():  # instrument only if tracing set up
    try:  # noqa: SIM105
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument_app(app)
    except Exception:  # noqa: BLE001
        pass
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute, redis_url=settings.redis_url)
allow_origins = [o.strip() for o in (settings.cors_allow_origins or '*').split(',')] if settings.cors_allow_origins != '*' else ["*"]
if os.environ.get('ENV','dev') == 'prod' and ('*' in allow_origins or allow_origins == ['*']):
    structlog.get_logger(__name__).warning("security/cors-wildcard-prod", detail="Wildcard CORS disabled in production; set CORS_ALLOW_ORIGINS")
    allow_origins = []
app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Correlation-ID"], max_age=600)

class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        async def send_wrapper(message):
            if message.get('type') == 'http.response.start':
                headers = message.setdefault('headers', [])
                def _add(k,v): headers.append((k.encode(), v.encode()))
                _add('x-content-type-options','nosniff')
                _add('x-frame-options','DENY')
                _add('referrer-policy','no-referrer')
                _add('x-xss-protection','0')
                if settings.csp_policy:
                    _add('content-security-policy', settings.csp_policy)
                _add('strict-transport-security','max-age=63072000; includeSubDomains')
            await send(message)
        await self.app(scope, receive, send_wrapper)

app.add_middleware(SecurityHeadersMiddleware)
@app.middleware("http")
async def _body_size_limit(request: Request, call_next):
    # Rely on content-length if present; otherwise read but enforce max
    max_bytes = settings.max_request_body_bytes
    cl = request.headers.get('content-length')
    if cl and cl.isdigit() and int(cl) > max_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    # For streaming uploads FastAPI reads body later; we intercept by limiting receive buffer
    # Simplistic approach: proceed and trust chunk endpoints enforce size.
    return await call_next(request)
@app.middleware("http")
async def _metrics_middleware(request, call_next):  # noqa: D401
    import time as _t
    start = _t.time()
    api_in_flight_requests.inc()
    response = None
    try:
        # Set request id context for audit enrichment
        _request_id_var.set(getattr(request.state, 'correlation_id', None))
        response = await call_next(request)
        return response
    finally:
        duration = _t.time() - start
        api_in_flight_requests.dec()
        # label cardinality control: truncate path to first 2 segments
        path = request.url.path
        parts = [p for p in path.split('/') if p]
        short_path = '/' + '/'.join(parts[:2]) if parts else '/'
    method = request.method
    code = getattr(response, 'status_code', 500) if response is not None else 500
    api_requests_total.labels(method=method, path=short_path, code=str(code)).inc()
    api_request_duration_seconds.observe(duration)
logger = structlog.get_logger().bind(component="api")
_draining: bool = False
_cb_fail_count = 0
_cb_open_until = 0.0
_CB_THRESHOLD = 5
_CB_RESET_SECONDS = 60

@app.get("/healthz")
def healthz():
    from persistence import _enc_material  # type: ignore
    model_loaded = False
    try:
        from transcription_services import _whisper_model  # type: ignore
        model_loaded = _whisper_model is not None if settings.enable_local_transcription else True
    except Exception:
        model_loaded = False
    db_ok = True
    try:
        from persistence import ENGINE
        with ENGINE.connect() as conn:
            conn.execute("SELECT 1")  # simple ping
    except Exception:
        db_ok = False
    return {
        "status": "ok" if (model_loaded and db_ok) else "degraded",
        "version": settings.app_version,
        "env": settings.environment_name,
        "encryption_keys": len(_enc_material),
        "field_encryption_enabled": settings.enable_field_encryption,
        "model_loaded": model_loaded,
        "db_ok": db_ok,
    }

# ---------------------- Auth Helpers ---------------------- #
bearer_scheme = HTTPBearer(auto_error=False)

def verify_external_jwt(token: str):
    # JWKS path
    if settings.keycloak_jwks_url and settings.keycloak_issuer and _jwks_keys:
        with _jwks_lock:
            keys_snapshot = list(_jwks_keys)
        try:
            headers = jwt.get_unverified_header(token)
        except Exception:
            return None
        kid = headers.get("kid")
        for k in keys_snapshot:
            if kid and k.get("kid") != kid:
                continue
            if k.get("kty") == "RSA" and k.get("n") and k.get("e"):
                try:
                    from cryptography.hazmat.primitives.asymmetric import rsa
                    from cryptography.hazmat.primitives import serialization as _ser
                    import base64 as _b64
                    def _b64u(data: str):
                        pad = '=' * (-len(data) % 4)
                        return _b64.urlsafe_b64decode(data + pad)
                    n_int = int.from_bytes(_b64u(k['n']), 'big')
                    e_int = int.from_bytes(_b64u(k['e']), 'big')
                    pub_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                    pub_key = pub_numbers.public_key()
                    pem = pub_key.public_bytes(_ser.Encoding.PEM, _ser.PublicFormat.SubjectPublicKeyInfo)
                    return jwt.decode(token, pem, algorithms=[k.get('alg','RS256')], issuer=settings.keycloak_issuer)
                except Exception:
                    continue
        return None
    # Static key fallback
    if settings.keycloak_public_key and settings.keycloak_issuer:
        try:
            return jwt.decode(token, settings.keycloak_public_key, algorithms=["RS256"], issuer=settings.keycloak_issuer)
        except JWTError:  # noqa: PERF203
            return None
    return None

def _current_signing_kid(secret_or_key: str) -> str:
    return hashlib.sha256(secret_or_key.encode()).hexdigest()[:16]

def _get_all_internal_secrets():
    if settings.use_rsa_internal_jwt:
        keys: List[str] = []
        if settings.internal_jwt_public_key_file:
            try:
                with open(settings.internal_jwt_public_key_file, 'r') as f:
                    keys.append(f.read())
            except FileNotFoundError:
                pass
        if settings.internal_jwt_public_key_pem:
            keys.append(settings.internal_jwt_public_key_pem)
        if settings.internal_jwt_old_public_keys_pem:
            keys.extend([k for k in settings.internal_jwt_old_public_keys_pem.split("||") if k.strip()])
        return keys
    secrets_list = [settings.internal_jwt_secret]
    if settings.internal_jwt_old_secrets:
        secrets_list.extend([s for s in settings.internal_jwt_old_secrets.split(",") if s.strip()])
    return secrets_list

def verify_internal_jwt(token: str):
    alg = "RS256" if settings.use_rsa_internal_jwt else "HS256"
    for key in _get_all_internal_secrets():
        try:
            return jwt.decode(token, key, algorithms=[alg])
        except JWTError:
            continue
    return None


def issue_internal_jwt(session_id: str, scope: str) -> str:
    payload = {"sid": session_id, "scope": scope, "iss": "mmt-backend"}
    if settings.use_rsa_internal_jwt:
        pem: bytes | None = None
        if settings.internal_jwt_private_key_file:
            try:
                with open(settings.internal_jwt_private_key_file, 'rb') as f:
                    pem = f.read()
            except FileNotFoundError:
                pass
        if not pem and settings.internal_jwt_private_key_pem:
            pem = settings.internal_jwt_private_key_pem.encode()
        if not pem:
            raise RuntimeError("RSA mode enabled but no private key configured")
        priv = serialization.load_pem_private_key(pem, password=None)
        pub_src = None
        if settings.internal_jwt_public_key_file:
            try:
                with open(settings.internal_jwt_public_key_file, 'r') as f:
                    pub_src = f.read()
            except FileNotFoundError:
                pass
        if not pub_src and settings.internal_jwt_public_key_pem:
            pub_src = settings.internal_jwt_public_key_pem
        if not pub_src:
            raise RuntimeError("RSA mode enabled but no public key provided for kid derivation")
        kid = _current_signing_kid(pub_src)
        return jwt.encode(payload, priv, algorithm="RS256", headers={"kid": kid})
    kid = _current_signing_kid(settings.internal_jwt_secret)
    return jwt.encode(payload, settings.internal_jwt_secret, algorithm="HS256", headers={"kid": kid})


def verify_guest_token(token: str):
    return settings.allow_guest_auth and secrets.compare_digest(token, settings.guest_secret)

def _has_scope(scope_str: str, required: str) -> bool:
    scopes = set(scope_str.split()) if scope_str else set()
    return required in scopes

ROLE_SCOPE_MAP = {
    "reader": {"user/DocumentReference.read"},
    "writer": {"user/DocumentReference.write"},
    "admin": {"user/DocumentReference.write", "admin:drain"},
}

def _role_allows(role: str | None, scope: str) -> bool:
    if not role:
        return False
    if role == 'guest':
        return False
    allowed = set()
    for r, scopes in ROLE_SCOPE_MAP.items():
        if r == role:
            allowed |= scopes
    return scope in allowed


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")
    token = credentials.credentials
    role = None  # ensure defined for later context var set
    if verify_guest_token(token):
        _user_role_var.set('guest')
        return {"role": "guest"}
    # Internal JWT (SMART session)
    internal = verify_internal_jwt(token)
    if internal:
        sid = internal.get("sid")
        sess = get_session_token(sid) if sid else None
        # Attempt refresh if expired
        if sess and sess.get('expires_at'):
            from datetime import datetime, timezone
            exp = sess['expires_at']
            try:
                if isinstance(exp, str):
                    # naive parse fallback
                    from dateutil import parser  # type: ignore
                    exp_dt = parser.isoparse(exp)
                else:
                    exp_dt = exp
                if isinstance(exp_dt, datetime) and exp_dt.tzinfo and exp_dt < datetime.now(timezone.utc):
                    refresh_session(sid)
                    sess = get_session_token(sid)
            except Exception:  # noqa: BLE001
                pass
        if not sess:
            raise HTTPException(status_code=401, detail="Session expired")
        # Map role based on scopes
        raw_scope = internal.get("scope", "")
        role = 'writer' if 'user/DocumentReference.write' in raw_scope.split() else 'reader'
        if 'admin:drain' in raw_scope.split():
            role = 'admin'
        _user_role_var.set(role)
        return {"role": role, "sid": sid, "scope": raw_scope, "fhir_access_token": sess.get("access_token")}
    external = verify_external_jwt(token)
    if external:
        # Map Keycloak / external roles -> internal roles using realm_access.roles or custom claim
        _user_role_var.set(role)
        try:
            if isinstance(external.get('realm_access'), dict):  # Keycloak style
                roles = external['realm_access'].get('roles', []) or []
        except Exception:
            roles = []
        # Fallback to single role claim
        if not roles and external.get('role'):
            roles = [external.get('role')]
        # Configurable role names (env) else defaults
        writer_match = settings.__dict__.get('keycloak_writer_role', 'writer')
        reader_match = settings.__dict__.get('keycloak_reader_role', 'reader')
        admin_match = settings.__dict__.get('keycloak_admin_role', 'admin')
        mapped_role = 'reader'
        if admin_match in roles:
            mapped_role = 'admin'
        elif writer_match in roles:
            mapped_role = 'writer'
        elif reader_match in roles:
            mapped_role = 'reader'
        external['role'] = mapped_role
        _user_role_var.set(mapped_role)
        return external
    raise HTTPException(status_code=401, detail="Invalid or expired token.")

@app.post("/login/guest")
async def login_guest():
    if not settings.allow_guest_auth:
        raise HTTPException(status_code=403, detail="Guest auth disabled")
    audit(AuditEvent.GUEST_LOGIN)
    return {"access_token": settings.guest_secret, "token_type": "bearer"}


@app.get("/auth/fhir/authorize")
def smart_authorize():
    url = build_authorize_url()
    return {"authorize_url": url}


@app.get("/auth/fhir/callback")
def smart_callback(code: str, state: str):
    try:
        token_payload = exchange_code(code, state)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")
    internal_token = issue_internal_jwt(token_payload['session_id'], token_payload.get('scope', ''))
    audit(AuditEvent.SMART_CALLBACK, session_id=token_payload['session_id'])
    return {"access_token": internal_token, "token_type": "bearer", "expires_in": token_payload.get("expires_in")}


@app.get("/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/.well-known/jwks.json")
def jwks():
    keys = []
    if settings.use_rsa_internal_jwt:
        pem_list = _get_all_internal_secrets()
        for pem in pem_list:
            try:
                pub = serialization.load_pem_public_key(pem.encode())
                numbers = pub.public_numbers()
                e = numbers.e
                n = numbers.n
                def b64url(i: int) -> str:
                    b = i.to_bytes((i.bit_length() + 7)//8, 'big')
                    return base64.urlsafe_b64encode(b).decode().rstrip('=')
                kid = _current_signing_kid(pem)
                keys.append({
                    "kty": "RSA",
                    "alg": "RS256",
                    "kid": kid,
                    "use": "sig",
                    "n": b64url(n),
                    "e": b64url(e),
                })
            except Exception:
                continue
    else:
        for secret in _get_all_internal_secrets():
            kid = _current_signing_kid(secret)
            keys.append({
                "kty": "oct",
                "alg": "HS256",
                "k": base64.urlsafe_b64encode(secret.encode()).decode().rstrip("="),
                "kid": kid,
                "use": "sig",
            })
    return {"keys": keys}

# ---------------------- Utility ---------------------- #
def _publish_transcription(filename: str, text: str, correlation_id: str | None = None):
    if _draining:
        raise HTTPException(status_code=503, detail="Service draining - no new publishes accepted")
    payload = {"filename": filename, "text": text, "source": "api", "publish_time": time.time()}
    if correlation_id:
        payload["correlation_id"] = correlation_id
    tracer = trace.get_tracer("publish")
    with tracer.start_as_current_span("publish_transcription") as span:
        span.set_attribute("filename", filename)
        attempt = 0
        last_err: Exception | None = None
        global _cb_fail_count, _cb_open_until
        now = time.time()
        if now < _cb_open_until:
            # fallback: store locally since circuit open
            from persistence import store_transcript
            store_transcript(filename, text, None, None, source="api-fallback")
            audit(AuditEvent.PUBLISH_FAILED, filename=filename, error="circuit_open_fallback", correlation_id=correlation_id)
            breaker_fallback_persist_total.inc()
            return
        while attempt < 3:
            try:
                send_to_rabbitmq(
                    queue=settings.transcription_queue,
                    message=payload,
                    rabbitmq_url=settings.rabbitmq_url,
                )
                transcripts_published_total.inc()
                _cb_fail_count = 0
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                publish_failures_total.inc()
                span.record_exception(e)
                attempt += 1
                if attempt < 3:
                    import time as _t
                    _t.sleep(0.5 * attempt)
        else:
            audit(AuditEvent.PUBLISH_FAILED, filename=filename, error=str(last_err))
            _cb_fail_count += 1
            if _cb_fail_count >= _CB_THRESHOLD:
                _cb_open_until = time.time() + _CB_RESET_SECONDS
                breaker_open_total.inc()
                audit(AuditEvent.PUBLISH_FAILED, filename=filename, error="circuit_open")
            # Instead of surfacing 503, persist locally for durability
            try:
                from persistence import store_transcript
                store_transcript(filename, text, None, None, source="api-fallback-error")
                breaker_fallback_persist_total.inc()
                return
            except Exception:
                raise HTTPException(status_code=503, detail="Queue unavailable")

def _require_scope(user: dict, required: str):
    if user.get('role') == 'guest':
        if not settings.allow_guest_auth:
            raise HTTPException(status_code=403, detail="Guest access disabled")
        # For dev, allow guest for read-only endpoints only
        if required.endswith('.write'):
            raise HTTPException(status_code=403, detail="Guest cannot perform write actions")
        return
    scope_str = user.get('scope', '')
    if not (_has_scope(scope_str, required) or _role_allows(user.get('role'), required)):
        raise HTTPException(status_code=403, detail=f"Missing scope or role disallows: {required}")

@app.get("/transcripts/{transcript_id}")
def fetch_transcript(transcript_id: int, current_user: dict = Depends(get_current_user)):
    # RBAC: require read scope
    _require_scope(current_user, 'user/DocumentReference.read')
    rec = get_transcript(transcript_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    # Remove internal encryption metadata if any lingered
    for f in ("text", "summary"):
        if isinstance(rec.get(f), dict):
            rec[f] = rec[f].get('v') if rec[f].get('v') else rec[f]
    # Heuristic: if enable_field_encryption and value still looks like JSON wrapper or base64 blob pattern
    if settings.enable_field_encryption:
        import re as _re
        suspicious = False
        b64re = _re.compile(r'^[A-Za-z0-9+/=]{20,}$')
        for f in ("text", "summary"):
            v = rec.get(f)
            if isinstance(v, str) and v.startswith('{"enc":'):  # wrapper leaked
                suspicious = True
            elif isinstance(v, str) and b64re.match(v) and len(v) > 40 and ' ' not in v:
                suspicious = True
        if suspicious:
            rec['decryption_warning'] = True
            decryption_warnings_total.inc()
    return rec

# ---------------------- Cloud Transcription ---------------------- #
@app.post("/transcribe/cloud/")
async def transcribe_cloud_endpoint(
    file: Optional[UploadFile] = File(None),
    request: Request = None,  # FastAPI injects Request
    current_user: dict = Depends(get_current_user)
):
    _require_scope(current_user, 'user/DocumentReference.write')
    logger.info("cloud_transcribe_request", has_file=bool(file), user=current_user.get("role"))
    if not settings.enable_cloud_transcription:
        raise HTTPException(status_code=403, detail="Cloud transcription disabled")
    # File upload path
    if file is not None:
        data = await file.read()
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        try:
            text = transcribe_cloud(data, file.filename, mime_type)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Cloud transcription failed: {e}")
        text = normalize_text(text)
        _publish_transcription(file.filename, text, getattr(request.state, 'correlation_id', None) if request else None)
        logger.info("cloud_transcribe_success", filename=file.filename, chars=len(text))
        if settings.mask_phi_in_responses:
            return {"text": mask_phi_for_response(text)}
        return {"text": text}
    # Ambient text JSON path
    if request is not None:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        raw_text = body.get("text")
        if not raw_text:
            raise HTTPException(status_code=400, detail="No text provided.")
        text = normalize_text(raw_text)
        _publish_transcription("ambient", text, getattr(request.state, 'correlation_id', None) if request else None)
        logger.info("ambient_text_ingested", chars=len(text))
        if settings.mask_phi_in_responses:
            return {"text": mask_phi_for_response(text)}
        return {"text": text}
    # Nothing provided
    raise HTTPException(status_code=400, detail="No input provided.")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_mime(file: UploadFile) -> str | None:
    return file.content_type or mimetypes.guess_type(file.filename)[0]

@app.post("/upload_chunk/")
async def upload_chunk(
    request: Request,
    chunk: UploadFile = File(...),
    upload_id: str = '',
    chunk_index: int = 0,
    total_chunks: int = 1,
    filename: str = '',
    current_user: dict = Depends(get_current_user),
):
    """Accept a chunk of a file and append to a temp file with auth + size limits."""
    _require_scope(current_user, 'user/DocumentReference.write')
    mime_type = _get_mime(chunk)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime_type}")
    raw = await chunk.read()
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Chunk too large")
    temp_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{filename}")
    mode = 'ab' if chunk_index > 0 else 'wb'
    current_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    if current_size + len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds max size")
    with open(temp_path, mode) as f:
        f.write(raw)
    if chunk_index + 1 == total_chunks:
        return {"status": "complete", "file_path": temp_path}
    return {"status": "incomplete", "received_chunk": chunk_index}


from persistence import async_task_create, async_task_update, async_task_get

def _run_local_transcription(data: bytes, filename: str, mime_type: str | None) -> str:
    with transcription_duration_seconds.time():
        return transcribe_local(data, filename, mime_type)

@app.post("/transcribe/local/")
async def transcribe_local_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None,  # injected
    async_mode: bool = True,
):
    # Allow test override / deterministic behavior
    if settings.force_sync_publish:
        async_mode = False
    if _draining:
        raise HTTPException(status_code=503, detail="Service draining - new requests rejected")
    _require_scope(current_user, 'user/DocumentReference.write')
    logger.info("local_transcribe_request", filename=file.filename, user=current_user.get("role"))
    if not settings.enable_local_transcription:
        raise HTTPException(status_code=403, detail="Local transcription disabled")
    mime_type = _get_mime(file)
    data = await file.read()
    if async_mode:
        # Offload to thread executor and return 202 with task id
        task_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        def _task():
            start = time.time()
            try:
                text = _run_local_transcription(data, file.filename, mime_type)
                text_n = normalize_text(text)
                _publish_transcription(file.filename, text_n, getattr(request.state,'correlation_id',None) if request else None)
                audit(AuditEvent.TRANSCRIPT_STORE, filename=file.filename, task_id=task_id, async_mode=True)
                async_task_update(task_id, 'done', result_text=text_n)
                async_tasks_completed_total.inc()
            except Exception as e:  # noqa: BLE001
                async_task_update(task_id, 'error', error=str(e))
                async_tasks_failed_total.inc()
            finally:
                async_task_duration_seconds.observe(time.time() - start)
        async_task_create(task_id, file.filename)
        async_tasks_started_total.inc()
        try:
            _submission_queue.put_nowait((_task, tuple(), {}))
            async_task_queue_size.set(_submission_queue.qsize())
        except _queue.Full:
            async_task_update(task_id, 'error', error='queue_full')
            async_tasks_failed_total.inc()
            raise HTTPException(status_code=503, detail="Async processing capacity exhausted")
        return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})
    # synchronous path
    try:
        text = _run_local_transcription(data, file.filename, mime_type)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Local transcription failed: {e}")
    text = normalize_text(text)
    _publish_transcription(file.filename, text, getattr(request.state, 'correlation_id', None) if request else None)
    logger.info("local_transcribe_success", filename=file.filename, chars=len(text))
    if settings.mask_phi_in_responses:
        return {"text": mask_phi_for_response(text)}
    return {"text": text}

@app.post("/transcribe/")
async def transcribe_unified(
    request: Request,
    file: UploadFile | None = File(default=None),
    async_mode: bool = True,
    use_cloud: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Unified transcription endpoint.

    Behaviors:
    - Multipart with 'file': delegates to local (default) or cloud model.
    - JSON body with {'text': '...','mode':'ambient'} treated as pre-transcribed ambient text (no model), published & stored.
    - async_mode only applies to local model path; cloud & ambient are synchronous for now.
    """
    if settings.force_sync_publish:
        async_mode = False
    if _draining:
        raise HTTPException(status_code=503, detail="Service draining - new requests rejected")
    _require_scope(current_user, 'user/DocumentReference.write')
    # Determine content type
    if file is not None:  # multipart path
        mime_type = _get_mime(file)
        data = await file.read()
        target_local = not use_cloud
        if target_local:
            # Reuse existing logic by constructing a pseudo UploadFile call path
            if async_mode:
                # minimal duplication: call existing local endpoint logic
                # Inline subset to avoid extra roundtrip
                task_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
                def _task():
                    start = time.time()
                    try:
                        text_loc = _run_local_transcription(data, file.filename, mime_type)
                        text_norm = normalize_text(text_loc)
                        _publish_transcription(file.filename, text_norm, getattr(request.state,'correlation_id',None))
                        audit(AuditEvent.TRANSCRIPT_STORE, filename=file.filename, task_id=task_id, async_mode=True)
                        async_task_update(task_id, 'done', result_text=text_norm)
                        async_tasks_completed_total.inc()
                    except Exception as e:  # noqa: BLE001
                        async_task_update(task_id, 'error', error=str(e))
                        async_tasks_failed_total.inc()
                    finally:
                        async_task_duration_seconds.observe(time.time() - start)
                async_task_create(task_id, file.filename)
                async_tasks_started_total.inc()
                try:
                    _submission_queue.put_nowait((_task, tuple(), {}))
                    async_task_queue_size.set(_submission_queue.qsize())
                except _queue.Full:
                    async_task_update(task_id, 'error', error='queue_full')
                    async_tasks_failed_total.inc()
                    raise HTTPException(status_code=503, detail="Async processing capacity exhausted")
                return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})
            # synchronous local
            try:
                text_loc = _run_local_transcription(data, file.filename, mime_type)
            except Exception as e:  # noqa: BLE001
                raise HTTPException(status_code=500, detail=f"Local transcription failed: {e}")
            text_norm = normalize_text(text_loc)
            _publish_transcription(file.filename, text_norm, getattr(request.state,'correlation_id',None))
            if settings.mask_phi_in_responses:
                return {"text": mask_phi_for_response(text_norm)}
            return {"text": text_norm}
        # cloud path
        if not settings.enable_cloud_transcription:
            raise HTTPException(status_code=403, detail="Cloud transcription disabled")
        try:
            raw_text = transcribe_cloud(data, file.filename, mime_type)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Cloud transcription failed: {e}")
        text_norm = normalize_text(raw_text)
        _publish_transcription(file.filename, text_norm, getattr(request.state,'correlation_id',None))
        if settings.mask_phi_in_responses:
            return {"text": mask_phi_for_response(text_norm), "cloud": True}
        return {"text": text_norm, "cloud": True}
    # JSON / ambient path
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Missing file or JSON body")
    ambient_text = body.get('text')
    if not ambient_text:
        raise HTTPException(status_code=400, detail="No text provided")
    mode = body.get('mode')
    filename = body.get('filename') or f"ambient_{int(time.time())}.txt"
    ambient_norm = normalize_text(ambient_text)
    # Publish without running model
    _publish_transcription(filename, ambient_norm, getattr(request.state,'correlation_id',None))
    audit(AuditEvent.TRANSCRIPT_STORE, filename=filename, ambient=True)
    if settings.mask_phi_in_responses:
        ambient_norm = mask_phi_for_response(ambient_norm)
    return {"text": ambient_norm, "ambient": True, "mode": mode}

@app.get("/transcribe/local/task/{task_id}")
def local_transcribe_task_status(task_id: str, current_user: dict = Depends(get_current_user)):
    _require_scope(current_user, 'user/DocumentReference.read')
    info = async_task_get(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": info['task_id'], "status": info['status'], "text": info.get('result_text'), "error": info.get('error')}


@app.get("/")
def root():
    return {"message": "MMT Backend is running."}


@app.get("/health/live")
def health_live():
    return {"status": "live"}


@app.get("/health/ready")
def health_ready():
    try:
        if _draining:
            raise RuntimeError("draining")
        send_to_rabbitmq(queue="health_check", message={"ok": True}, rabbitmq_url=settings.rabbitmq_url)
        return {"status": "ready"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")

def _require_admin(request: Request):
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin key not configured")
    supplied = request.headers.get("x-admin-key") or request.query_params.get("admin_key")
    if not supplied or not secrets.compare_digest(supplied, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/admin/drain", response_model=dict)
def initiate_drain(request: Request):
    _require_admin(request)
    global _draining
    _draining = True
    audit(AuditEvent.PUBLISH_FAILED, filename="*", error="drain_initiated")  # reuse event taxonomy for now
    drain_start_total.inc()
    structlog.get_logger(__name__).info("drain/start")
    return {"status": "draining", "message": "New transcription requests rejected with 503"}

@app.get("/admin/drain/status")
def drain_status(request: Request):
    _require_admin(request)
    return {"draining": _draining, "circuit_open_until": _cb_open_until, "cb_fail_count": _cb_fail_count}

@app.get("/network_advice/")
def network_advice(bandwidth_kbps: float = 0):
    if bandwidth_kbps > 500:
        return {"mode": "real_time"}
    return {"mode": "chunked"}


# ---------------------- WebSocket Streaming (prototype) ---------------------- #

class StreamSession:
    """Holds state for a single streaming transcription session."""
    def __init__(self):
        self.buffer = bytearray()
        self.started = time.time()
        self.last_chunk = self.started
        self.chunks = 0

    def add(self, data: bytes):
        self.buffer.extend(data)
        self.chunks += 1
        self.last_chunk = time.time()


@app.websocket("/ws/transcribe")
async def websocket_transcribe(ws: WebSocket):
    # Origin allowlist (support runtime mutation for tests)
    try:
        current_allowed = getattr(settings, 'websocket_allowed_origins', '*')
    except Exception:
        current_allowed = '*'
    allowed = [o.strip() for o in (current_allowed or '*').split(',')]
    origin = ws.headers.get('origin') or ws.headers.get('Origin')
    if allowed != ['*'] and origin not in allowed:
        try:
            await ws.close(code=4403)
        finally:
            websocket_rejected_total.labels(reason="origin").inc()
        return
    # Token via header or query
    token = ws.query_params.get('token') or ws.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token.split(' ',1)[1]
    user = None
    if token:
        creds = type('C', (), {'credentials': token})()
        try:
            user = get_current_user(credentials=creds)  # type: ignore[arg-type]
            _require_scope(user, 'user/DocumentReference.write')
        except Exception:
            user = None
    if user is None:
        try:
            await ws.close(code=4401)
        finally:
            websocket_rejected_total.labels(reason="auth").inc()
        return
    await ws.accept()
    session = StreamSession()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "error": "invalid_json"})
                continue
            if msg.get("type") != "chunk":
                await ws.send_json({"type": "error", "error": "unknown_message_type"})
                continue
            b64 = msg.get("data")
            if b64:
                try:
                    chunk_bytes = base64.b64decode(b64)
                    if len(session.buffer) + len(chunk_bytes) > settings.max_ws_buffer_bytes:
                        await ws.send_json({"type": "error", "error": "buffer_limit"})
                        break
                    session.add(chunk_bytes)
                except Exception:  # noqa: BLE001
                    await ws.send_json({"type": "error", "error": "bad_base64"})
                    continue
            await ws.send_json({
                "type": "ack",
                "received_bytes": len(session.buffer),
                "chunks": session.chunks,
            })
            if settings.enable_partial_streaming and session.chunks % 2 == 0 and len(session.buffer) > 4000:
                try:
                    partial_text = transcribe_local(bytes(session.buffer), msg.get("filename", "stream.wav"), "audio/wav")
                    partial_text = normalize_text(partial_text)
                    await ws.send_json({"type": "partial", "text": partial_text})
                    websocket_partial_sent_total.inc()
                except Exception:
                    pass
            if msg.get("final"):
                if not settings.enable_local_transcription:
                    await ws.send_json({"type": "error", "error": "local_transcription_disabled"})
                    break
                # Perform transcription
                try:
                    text = transcribe_local(bytes(session.buffer), msg.get("filename", "stream.wav"), "audio/wav")
                    text = normalize_text(text)
                    _publish_transcription(msg.get("filename", "stream.wav"), text)
                    await ws.send_json({"type": "final", "text": text})
                except Exception as e:  # noqa: BLE001
                    await ws.send_json({"type": "error", "error": f"transcription_failed: {e}"})
                break
    except WebSocketDisconnect:
        # Client dropped; best-effort cleanup
        pass


@app.get("/metrics")
def metrics_endpoint():
    data = generate_latest()
    return JSONResponse(content=data.decode(), media_type=CONTENT_TYPE_LATEST, headers={"Cache-Control":"no-store"})


@app.get("/fhir/patient/{patient_id}")
def fhir_patient_read(patient_id: str, current_user: dict = Depends(get_current_user)):
    _require_scope(current_user, 'user/Patient.read')
    token = current_user.get('fhir_access_token')
    if not token:
        raise HTTPException(status_code=401, detail="Missing FHIR token")
    settings = get_settings()
    import requests
    url = f"{settings.openemr_fhir_base_url}/apis/{settings.openemr_site}/fhir/Patient/{patient_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized to read patient")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Patient not found")
    resp.raise_for_status()
    return resp.json()

# startup handled by lifespan context

def _current_alembic_revision() -> str | None:
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(cfg)
        heads = script.get_heads()
        return heads[0] if heads else None
    except Exception:
        return None

def _db_revision_matches() -> bool:
    # naive: check alembic_version table vs script head
    head = _current_alembic_revision()
    if not head:
        return True  # skip if not available
    try:
        from sqlalchemy import text as _text
        from persistence import ENGINE
        with ENGINE.connect() as conn:
            res = conn.execute(_text("SELECT version_num FROM alembic_version")).scalar()
            return res == head
    except Exception:
        return False

def _start_migration_revision_check():
    if os.environ.get('ENV','dev') != 'prod':
        return
    if not _db_revision_matches():
        raise RuntimeError("Database migration revision mismatch – run alembic upgrade head")

def _start_retention_thread():
    if settings.retention_days and settings.retention_days > 0:
        import threading, time as _t
        from retention import purge_once
        def _loop():
            while True:
                try:
                    purge_once()
                except Exception:
                    pass
                _t.sleep(3600)  # hourly
        threading.Thread(target=_loop, daemon=True, name="retention-purge").start()

def cleanup_async_tasks_once() -> int:
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import delete
    from persistence import async_tasks, ENGINE
    from metrics import async_tasks_purged_total
    retention_days = getattr(settings, 'async_task_retention_days', 0)
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    try:
        with ENGINE.begin() as conn:
            res = conn.execute(delete(async_tasks).where(async_tasks.c.updated_at < cutoff))
            purged = res.rowcount or 0
        if purged:
            async_tasks_purged_total.inc(purged)
        return purged
    except Exception:  # pragma: no cover
        return 0

def _start_async_task_cleanup_thread():
    if getattr(settings, 'async_task_retention_days', 0) <= 0:
        return
    interval_h = max(1, getattr(settings, 'async_cleanup_interval_hours', 24))
    def _loop():
        while True:
            try:
                cleanup_async_tasks_once()
            except Exception:
                pass
            time.sleep(interval_h * 3600)
    threading.Thread(target=_loop, daemon=True, name="async-task-cleanup").start()

_start_async_task_cleanup_thread()



