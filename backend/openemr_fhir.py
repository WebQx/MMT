"""OpenEMR FHIR integration utilities.

Provides helper functions to obtain an OAuth2 password-grant token and
create a DocumentReference resource carrying the transcription text.
"""
from __future__ import annotations

import base64
import time
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings


_cached_token: Optional[str] = None
_cached_expiry: float = 0.0


def _token_scopes(settings) -> str:
    if settings.openemr_fhir_scopes:
        return settings.openemr_fhir_scopes
    return "openid profile site:default user/DocumentReference.read user/DocumentReference.$docref user/Patient.read"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_token(force: bool = False) -> str:
    global _cached_token, _cached_expiry
    settings = get_settings()
    if not settings.openemr_fhir_base_url:
        raise RuntimeError("OPENEMR_FHIR_BASE_URL not configured")

    if (not force) and _cached_token and time.time() < _cached_expiry - 30:
        return _cached_token

    url = f"{settings.openemr_fhir_base_url}/oauth2/{settings.openemr_site}/token"
    auth = (settings.openemr_fhir_client_id, settings.openemr_fhir_client_secret)
    if settings.openemr_fhir_grant_type == "client_credentials":
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.openemr_fhir_client_id,
            "scope": _token_scopes(settings),
        }
    else:
        data = {
            "grant_type": "password",
            "client_id": settings.openemr_fhir_client_id,
            "username": settings.openemr_fhir_username,
            "password": settings.openemr_fhir_password,
            "user_role": "users",
            "scope": _token_scopes(settings),
        }
    resp = requests.post(url, data=data, auth=auth, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    token = j.get("access_token")
    if not token:
        raise RuntimeError("No access_token in response")
    _cached_token = token
    _cached_expiry = time.time() + int(j.get("expires_in", 3600))
    return token


def create_document_reference(text: str, filename: str = "transcription.txt") -> dict:
    settings = get_settings()
    if not settings.openemr_fhir_base_url:
        raise RuntimeError("FHIR base URL not configured")
    token = fetch_token()
    url = f"{settings.openemr_fhir_base_url}/apis/{settings.openemr_site}/fhir/DocumentReference"
    content_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    resource = {
        "resourceType": "DocumentReference",
        "status": "current",
        "docStatus": "final",
        "type": {"text": "Clinical Transcription"},
        "description": filename,
        "content": [
            {
                "attachment": {
                    "contentType": "text/plain",
                    "language": "en",
                    "data": content_b64,
                    "title": filename,
                }
            }
        ],
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json"}
    resp = requests.post(url, json=resource, headers=headers, timeout=30)
    if resp.status_code >= 400:
        # Attempt token refresh once if unauthorized
        if resp.status_code == 401:
            fetch_token(force=True)
            headers["Authorization"] = f"Bearer {_cached_token}"  # type: ignore[arg-type]
            resp = requests.post(url, json=resource, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()
