"""Audit logging utilities.

Provides a simple append-only JSONL audit log for security-relevant events.
In production you would forward these to a SIEM. Minimal overhead version.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, UTC
from typing import Any
from config import get_settings
from metrics import audit_events_total
from metrics import phi_redactions_total
import structlog
import contextvars

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("audit_request_id", default=None)
_user_role_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("audit_user_role", default=None)

_settings = get_settings()

def _line(event: str, **fields: Any) -> str:
    rec = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    return json.dumps(rec, ensure_ascii=False)


class AuditEvent:
    GUEST_LOGIN = "guest_login"
    SMART_CALLBACK = "smart_callback"
    PUBLISH_FAILED = "publish_failed"
    TRANSCRIPT_STORE = "transcript_store"
    RETENTION_PURGE = "retention_purge"


_logger = structlog.get_logger(__name__)

def audit(event: str, **fields: Any) -> None:
    rid = _request_id_var.get()
    role = _user_role_var.get()
    if rid and 'correlation_id' not in fields:
        fields['correlation_id'] = rid
    if role and 'user_role' not in fields:
        fields['user_role'] = role
    path = _settings.audit_log_file
    try:
        audit_events_total.labels(event=event).inc()
    except Exception:  # pragma: no cover
        pass
    rec_line = _line(event, **fields)
    if not path:
        # Fallback to structured logger if no file configured; rename to avoid structlog 'event' clash
        _logger.info("audit/event", audit_event=event, **fields)
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(rec_line + "\n")
    except Exception:  # noqa: BLE001
        _logger.warning("audit/write-failed", event=event)
        return


MASK_TOKEN = "[REDACTED]"
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MRN_RE = re.compile(r"\bMRN[:#]?\s*\d{4,}\b", re.IGNORECASE)
NAME_RE = re.compile(r"\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b")
ADDRESS_RE = re.compile(r"\b\d{1,4}\s+[A-Z][A-Za-z]+\s+(Street|St|Ave|Avenue|Road|Rd|Boulevard|Blvd)\b", re.IGNORECASE)


def _mask_patterns(text: str) -> str:
    text = PHONE_RE.sub(MASK_TOKEN, text)
    text = EMAIL_RE.sub(MASK_TOKEN, text)
    text = MRN_RE.sub(MASK_TOKEN, text)
    text = NAME_RE.sub(MASK_TOKEN, text)
    text = ADDRESS_RE.sub(MASK_TOKEN, text)
    return text


def mask_phi(text: str | None) -> str | None:
    if text is None:
        return None
    if _settings.store_phi:
        return text
    masked = _mask_patterns(text)
    try:
        phi_redactions_total.labels(scope="persist").inc()
    except Exception:
        pass
    # Optional advanced masking using Presidio if enabled and installed
    if _settings.advanced_phi_masking:
        try:  # pragma: no cover
            from presidio_analyzer import AnalyzerEngine  # type: ignore
            analyzer = AnalyzerEngine()
            results = analyzer.analyze(text=text, language="en")
            # Replace detected spans (reverse order to keep indices valid)
            for r in sorted(results, key=lambda r: r.start, reverse=True):
                masked = masked[:r.start] + MASK_TOKEN + masked[r.end:]
        except Exception:
            pass
    if len(masked) > 256:
        masked = MASK_TOKEN + f" ({len(masked)} chars masked)"
    return masked


def mask_phi_for_response(text: str | None) -> str | None:
    """Mask PHI for outbound API responses when response masking flag enabled.

    Unlike persistence masking (`mask_phi`), this always applies pattern masking
    regardless of `store_phi` so that sensitive data isn't echoed back to the caller
    when `MASK_PHI_IN_RESPONSES` is enabled. Lengthy masked payloads are truncated
    similarly to persistence masking for parity.
    """
    if text is None:
        return None
    original = text
    masked = _mask_patterns(text)
    if masked != original:
        try:
            phi_redactions_total.labels(scope="response").inc()
        except Exception:
            pass
    if len(masked) > 256:
        masked = MASK_TOKEN + f" ({len(masked)} chars masked)"
    return masked
