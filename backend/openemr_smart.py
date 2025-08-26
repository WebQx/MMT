"""SMART-on-FHIR (authorization_code) helper utilities for OpenEMR.

Provides utilities to build an authorize URL (with optional PKCE) and
exchange an authorization code for tokens. Minimal in-memory storage
for PKCE code_verifier and issued session tokens (non-production).
"""
from __future__ import annotations

import base64
import hashlib
import os
import time
from datetime import datetime, UTC, timedelta
from typing import Dict, Optional
import secrets
import requests
from config import get_settings
from persistence import save_session, get_session

_pkce_store: Dict[str, str] = {}


def _scopes(settings) -> str:
    if settings.openemr_fhir_scopes:
        return settings.openemr_fhir_scopes
    # Include SMART basic + Patient.read for demo; DocumentReference scopes if needed
    return "openid profile launch/patient user/Patient.read user/DocumentReference.read"


def build_authorize_url() -> str:
    settings = get_settings()
    if not all([
        settings.openemr_fhir_base_url,
        settings.openemr_fhir_client_id,
        settings.openemr_fhir_redirect_uri,
    ]):
        raise RuntimeError("SMART configuration incomplete (base_url, client_id, redirect_uri)")
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": settings.openemr_fhir_client_id,
        "redirect_uri": settings.openemr_fhir_redirect_uri,
        "scope": _scopes(settings),
        "state": state,
        "aud": f"{settings.openemr_fhir_base_url}/apis/{settings.openemr_site}/fhir",
    }
    if settings.openemr_fhir_use_pkce:
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
        _pkce_store[state] = code_verifier
    q = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return f"{settings.openemr_fhir_base_url}/oauth2/{settings.openemr_site}/authorize?{q}"


def exchange_code(code: str, state: str) -> dict:
    settings = get_settings()
    if not settings.openemr_fhir_base_url:
        raise RuntimeError("FHIR base URL not configured")
    token_url = f"{settings.openemr_fhir_base_url}/oauth2/{settings.openemr_site}/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.openemr_fhir_redirect_uri,
        "client_id": settings.openemr_fhir_client_id,
    }
    code_verifier = _pkce_store.pop(state, None)
    if settings.openemr_fhir_use_pkce and code_verifier:
        data["code_verifier"] = code_verifier
    auth = (settings.openemr_fhir_client_id, settings.openemr_fhir_client_secret)
    resp = requests.post(token_url, data=data, auth=auth, timeout=30)
    resp.raise_for_status()
    token_payload = resp.json()
    session_id = secrets.token_urlsafe(16)
    token_payload['session_id'] = session_id
    token_payload['created_at'] = int(time.time())
    expires_in = int(token_payload.get('expires_in', 3600))
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    save_session(
        session_id=session_id,
        scope=token_payload.get('scope', ''),
        access_token=token_payload.get('access_token', ''),
        refresh_token=token_payload.get('refresh_token'),
        expires_at=expires_at,
    )
    return token_payload


def get_session_token(session_id: str) -> Optional[dict]:
    return get_session(session_id)


def refresh_session(session_id: str) -> Optional[dict]:
    sess = get_session(session_id)
    if not sess or not sess.get('refresh_token'):
        return None
    settings = get_settings()
    token_url = f"{settings.openemr_fhir_base_url}/oauth2/{settings.openemr_site}/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": sess['refresh_token'],
        "client_id": settings.openemr_fhir_client_id,
    }
    auth = (settings.openemr_fhir_client_id, settings.openemr_fhir_client_secret)
    resp = requests.post(token_url, data=data, auth=auth, timeout=30)
    if resp.status_code >= 400:
        return None
    payload = resp.json()
    expires_in = int(payload.get('expires_in', 3600))
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    save_session(
        session_id=session_id,
        scope=payload.get('scope', sess.get('scope', '')),
        access_token=payload.get('access_token', ''),
        refresh_token=payload.get('refresh_token', sess.get('refresh_token')),
        expires_at=expires_at,
    )
    return get_session(session_id)