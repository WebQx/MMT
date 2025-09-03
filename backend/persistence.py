"""Persistence layer for transcripts using SQLAlchemy.

Uses MySQL if TRANSCRIPTS_DB_HOST is set, else falls back to local SQLite file.
Store minimal metadata + enrichment JSON + FHIR DocumentReference ID when available.
"""
from __future__ import annotations

import os
from datetime import datetime, UTC
import json
from typing import Any, Dict

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
)
from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON  # type: ignore
from sqlalchemy.types import JSON as SQLITE_JSON
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from audit import mask_phi, audit, AuditEvent
from config import get_settings
from sqlalchemy.orm import sessionmaker
from base64 import b64decode, b64encode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from metrics import (
    encryption_rotate_updated_total,
    encryption_key_reload_total,
    encryption_encrypt_failures_total,
    encryption_decrypt_failures_total,
    encryption_active_keys,
    encryption_rotate_attempt_total,
    encryption_rotate_failures_total,
)
import structlog
from threading import RLock

_enc_material: dict[str, bytes] = {}
_settings = get_settings()
_encryption_initialized = False
_enc_lock = RLock()
_log = structlog.get_logger(__name__)

def _load_encryption_material(force: bool = False) -> None:
    """Populate _enc_material from current settings if enabled.

    Safe to call multiple times; respects force flag. Sets _encryption_initialized.
    """
    global _enc_material, _settings, _encryption_initialized
    with _enc_lock:
        if not force and _encryption_initialized and _enc_material:
            return
        _settings = get_settings()
        _enc_material = {}
        _encryption_initialized = True
        if not (_settings.enable_field_encryption and _settings.encryption_keys and _settings.primary_encryption_key_id):
            if _settings.enable_field_encryption:
                _log.warning("encryption/config-missing", primary=_settings.primary_encryption_key_id, keys=bool(_settings.encryption_keys))
            return
        invalid = []
        try:
            for pair in _settings.encryption_keys.split(','):
                pair = pair.strip()
                if not pair or ':' not in pair:
                    continue
                kid, key_b64 = pair.split(':', 1)
                try:
                    key = b64decode(key_b64)
                except Exception:
                    invalid.append(kid)
                    continue
                if len(key) != 32:
                    invalid.append(kid)
                    continue
                if kid in _enc_material:
                    _log.warning("encryption/duplicate-key-id", kid=kid)
                    continue
                _enc_material[kid] = key
            if _settings.primary_encryption_key_id not in _enc_material:
                _log.error("encryption/primary-missing", primary=_settings.primary_encryption_key_id, loaded=list(_enc_material.keys()))
                _enc_material = {}
                if os.environ.get('ENV','dev') == 'prod':
                    raise RuntimeError("Primary encryption key id missing or invalid")
                return
            encryption_key_reload_total.inc()
            encryption_active_keys.set(len(_enc_material))
            if invalid:
                _log.warning("encryption/invalid-keys", invalid=invalid)
            _log.info("encryption/keys-loaded", count=len(_enc_material), primary=_settings.primary_encryption_key_id)
        except Exception as e:  # pragma: no cover
            _log.exception("encryption/load-failed")
            _enc_material = {}
            encryption_active_keys.set(0)
            if os.environ.get('ENV','dev') == 'prod':
                raise

def reload_encryption_keys() -> int:
    """Force reload encryption key material; returns active key count.

    Useful for tests or dynamic rotation setups.
    """
    _load_encryption_material(force=True)
    return len(_enc_material)

def _encrypt_field(plaintext: str | None) -> tuple[str | None, str | None]:
    if plaintext is None:
        return plaintext, None
    if not _enc_material:
        _load_encryption_material()
    if not _enc_material:
        return plaintext, None
    kid = _settings.primary_encryption_key_id
    key = _enc_material.get(kid)
    if not key:
        return plaintext, None
    try:
        aes = AESGCM(key)
        import os as _os
        nonce = _os.urandom(12)
        ct = aes.encrypt(nonce, plaintext.encode(), None)
        blob = b64encode(nonce + ct).decode()
        return blob, kid
    except Exception:  # pragma: no cover
        encryption_encrypt_failures_total.inc()
        _log.exception("encryption/encrypt-failed")
        return plaintext, None

def _maybe_encrypt_dict(d: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if d is None:
        return None
    if not _enc_material:
        return d
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            ev, kid = _encrypt_field(v)
            out[k] = {"enc": True, "kid": kid, "v": ev} if kid else v
        else:
            out[k] = v
    return out

def _decrypt_field(blob: str, kid: str | None) -> str:
    if not kid:
        return blob
    if kid not in _enc_material:
        _load_encryption_material()
    if kid not in _enc_material:
        return blob
    if blob.startswith('ENC:'):
        blob = blob[4:]
    try:
        raw = b64decode(blob)
        if len(raw) < 13:
            return blob
        nonce, ct = raw[:12], raw[12:]
        aes = AESGCM(_enc_material[kid])
        pt = aes.decrypt(nonce, ct, None)
        return pt.decode()
    except Exception:  # pragma: no cover
        encryption_decrypt_failures_total.inc()
        _log.exception("encryption/decrypt-failed")
        return blob

def _maybe_decrypt_enrichment(e: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if e is None:
        return None
    if not isinstance(e, dict):
        return e
    out = {}
    for k, v in e.items():
        if isinstance(v, dict) and v.get('enc') and 'v' in v:
            out[k] = _decrypt_field(v['v'], v.get('kid'))
        else:
            out[k] = v
    return out

def get_transcript(record_id: int) -> dict | None:
    try:
        with SessionLocal() as session:
            row = session.execute(transcripts.select().where(transcripts.c.id == record_id)).mappings().first()
            if not row:
                return None
            d = dict(row)
            # Decrypt fields if needed
            if _enc_material:
                for field in ("text", "summary"):
                    val = d.get(field)
                    if isinstance(val, str) and val.startswith('{'):
                        try:
                            val_obj = json.loads(val)
                        except Exception:
                            val_obj = None
                    else:
                        val_obj = val if isinstance(val, dict) else None
                    if isinstance(val_obj, dict) and val_obj.get("enc") and "v" in val_obj:
                        d[field] = _decrypt_field(val_obj["v"], val_obj.get("kid"))
                if isinstance(d.get("enrichment"), dict):
                    d["enrichment"] = _maybe_decrypt_enrichment(d.get("enrichment"))
            return d
    except Exception:
        return None

def rotate_encryption_keys(batch_size: int = 500, max_batches: int = 5) -> int:
    """Re-encrypt transcripts encrypted with non-primary keys.

    Processes up to max_batches * batch_size rows using pagination on id.
    Includes enrichment string fields.
    Returns count of rows updated.
    """
    if not _enc_material:
        _load_encryption_material()
    if not _enc_material or not _settings.enable_field_encryption:
        return 0
    primary = _settings.primary_encryption_key_id
    total_updated = 0
    encryption_rotate_attempt_total.inc()
    last_id = 0
    try:
        with SessionLocal() as session:
            for _ in range(max_batches):
                rows = session.execute(
                    transcripts.select().where(transcripts.c.id > last_id).order_by(transcripts.c.id.asc()).limit(batch_size)
                ).mappings().all()
                if not rows:
                    break
                for row in rows:
                    last_id = max(last_id, row['id'])
                    changed = False
                    updates = {}
                    # Handle text & summary (JSON string wrapper stored)
                    for field in ("text", "summary"):
                        val = row.get(field)
                        try:
                            if isinstance(val, str) and val.startswith('{'):
                                val_obj = json.loads(val)
                            else:
                                val_obj = None
                        except Exception:
                            val_obj = None
                        if isinstance(val_obj, dict) and val_obj.get('enc') and val_obj.get('kid') != primary:
                            dec = _decrypt_field(val_obj['v'], val_obj.get('kid'))
                            enc, kid = _encrypt_field(dec)
                            if kid:
                                updates[field] = json.dumps({"enc": True, "kid": kid, "v": enc}, separators=(',',':'))
                                changed = True
                    # Enrichment (JSON column) decrypt + re-encrypt string values with old key
                    enrichment = row.get('enrichment')
                    if isinstance(enrichment, dict):
                        new_enrichment = {}
                        enrichment_changed = False
                        for k, v in enrichment.items():
                            if isinstance(v, dict) and v.get('enc') and v.get('kid') != primary and 'v' in v:
                                dec = _decrypt_field(v['v'], v.get('kid'))
                                enc, kid = _encrypt_field(dec)
                                if kid:
                                    new_enrichment[k] = {"enc": True, "kid": kid, "v": enc}
                                    enrichment_changed = True
                                else:
                                    new_enrichment[k] = v
                            else:
                                new_enrichment[k] = v
                        if enrichment_changed:
                            updates['enrichment'] = new_enrichment
                            changed = True
                    if changed:
                        session.execute(transcripts.update().where(transcripts.c.id == row['id']).values(**updates))
                        total_updated += 1
                session.commit()
    except Exception:
        encryption_rotate_failures_total.inc()
        _log.exception("encryption/rotation-failed")
        return total_updated
    if total_updated:
        encryption_rotate_updated_total.inc(total_updated)
    return total_updated


def _database_url() -> str:
    host = os.environ.get("TRANSCRIPTS_DB_HOST")
    if host:
        user = os.environ.get("TRANSCRIPTS_DB_USER", "openemr")
        password = os.environ.get("TRANSCRIPTS_DB_PASSWORD", "openemr")
        db = os.environ.get("TRANSCRIPTS_DB_NAME", "openemr")
        port = os.environ.get("TRANSCRIPTS_DB_PORT", "3306")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return "sqlite:///transcripts.db"


ENGINE: Engine = create_engine(_database_url(), pool_pre_ping=True, future=True)
META = MetaData()

JSONType = MYSQL_JSON if ENGINE.url.get_backend_name().startswith("mysql") else SQLITE_JSON

transcripts = Table(
    "transcripts",
    META,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("filename", String(255), nullable=False),
    Column("text", Text, nullable=False),
    Column("summary", Text, nullable=True),
    Column("enrichment", JSONType, nullable=True),
    Column("source", String(32), nullable=False),
    Column("fhir_document_id", String(128), nullable=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True),
)

sessions = Table(
    "smart_sessions",
    META,
    Column("session_id", String(48), primary_key=True),
    Column("scope", Text, nullable=False),
    Column("access_token", Text, nullable=False),
    Column("refresh_token", Text, nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
)

async_tasks = Table(
    "async_tasks",
    META,
    Column("task_id", String(32), primary_key=True),
    Column("filename", String(255), nullable=False),
    Column("status", String(16), nullable=False),  # processing|done|error
    Column("result_text", Text, nullable=True),
    Column("error", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
)

idempotency_keys = Table(
    "idempotency_keys",
    META,
    Column("key", String(64), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True),
    Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
)

ENV = os.environ.get("ENV", "dev")
if ENV == "prod" and ENGINE.url.get_backend_name().startswith("sqlite"):
    raise RuntimeError("SQLite backend is not permitted in production. Configure a MySQL database via TRANSCRIPTS_DB_HOST.")

# Auto-create tables only outside production; production uses Alembic migrations
if ENV != "prod":
    META.create_all(ENGINE)

SessionLocal = sessionmaker(bind=ENGINE, expire_on_commit=False, future=True)
SESSION_MAKER = SessionLocal

def async_task_create(task_id: str, filename: str):
    with SessionLocal() as session:
        session.execute(async_tasks.insert().values(task_id=task_id, filename=filename, status="processing"))
        session.commit()

def async_task_update(task_id: str, status: str, result_text: str | None = None, error: str | None = None):
    with SessionLocal() as session:
        session.execute(async_tasks.update().where(async_tasks.c.task_id == task_id).values(status=status, result_text=result_text, error=error, updated_at=datetime.now(UTC)))
        session.commit()

def async_task_get(task_id: str) -> dict | None:
    with SessionLocal() as session:
        row = session.execute(async_tasks.select().where(async_tasks.c.task_id == task_id)).mappings().first()
        return dict(row) if row else None


def store_transcript(
    filename: str,
    text: str,
    summary: str | None,
    enrichment: Dict[str, Any] | None,
    source: str,
    fhir_document_id: str | None = None,
) -> int:
    # Input validation
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    if not source or not source.strip():
        raise ValueError("Source cannot be empty")
    settings = get_settings()
    try:
        with SessionLocal() as session:
            enc_text, text_kid = _encrypt_field(mask_phi(text))
            enc_summary = None
            summary_kid = None
            if summary:
                enc_summary, summary_kid = _encrypt_field(mask_phi(summary))
            enc_enrichment = _maybe_encrypt_dict(enrichment)
            text_value = {"enc": True, "kid": text_kid, "v": f"ENC:{enc_text}"} if text_kid else enc_text
            summary_value = {"enc": True, "kid": summary_kid, "v": f"ENC:{enc_summary}"} if summary_kid and enc_summary else enc_summary
            # Serialize dicts to JSON for Text columns
            if isinstance(text_value, dict):
                text_value = json.dumps(text_value, separators=(',',':'))
            if isinstance(summary_value, dict):
                summary_value = json.dumps(summary_value, separators=(',',':'))
            result = session.execute(
                transcripts.insert().values(
                    filename=filename,
                    text=text_value,
                    summary=summary_value,
                    enrichment=enc_enrichment,
                    source=source,
                    fhir_document_id=fhir_document_id,
                )
            )
            session.commit()
            audit(AuditEvent.TRANSCRIPT_STORE, filename=filename, masked=not settings.store_phi)
            return int(result.inserted_primary_key[0])
    except SQLAlchemyError as e:
        from metrics import transcripts_persist_failures_total
        transcripts_persist_failures_total.inc()
        _log.warning("persistence/store-failed", error=str(e))
        return -1


def update_fhir_id(record_id: int, fhir_id: str) -> None:
    if record_id <= 0:
        return
    try:
        with SessionLocal() as session:
            session.execute(
                transcripts.update().where(transcripts.c.id == record_id).values(fhir_document_id=fhir_id)
            )
            session.commit()
    except SQLAlchemyError:
        pass


# ---------------- SMART Session Helpers ---------------- #
def save_session(session_id: str, scope: str, access_token: str, refresh_token: str | None, expires_at: datetime) -> None:
    try:
        with SessionLocal() as session:
            existing = session.execute(sessions.select().where(sessions.c.session_id == session_id)).first()
            if existing:
                session.execute(
                    sessions.update().where(sessions.c.session_id == session_id).values(
                        scope=scope,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                        updated_at=datetime.now(UTC),
                    )
                )
            else:
                session.execute(
                    sessions.insert().values(
                        session_id=session_id,
                        scope=scope,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                    )
                )
            session.commit()
    except SQLAlchemyError:
        pass


def get_session(session_id: str) -> dict | None:
    from security_fixes import validate_session_id
    try:
        validate_session_id(session_id)
    except ValueError:
        return None
    try:
        with SessionLocal() as session:
            row = session.execute(sessions.select().where(sessions.c.session_id == session_id)).mappings().first()
            if row:
                return dict(row)
    except SQLAlchemyError:
        return None
    return None