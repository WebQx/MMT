"""Nextcloud storage integration for transcript artifacts.

Provides a thin wrapper around the WebDAV interface exposed by Nextcloud to
persist structured transcription payloads. Uploads both JSON metadata and a
plain-text transcript for quick review while keeping the SQLite/MySQL database
as the system of record for indexing/search.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from threading import RLock
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth
import structlog

from config import get_settings
from metrics import nextcloud_upload_success_total, nextcloud_upload_failure_total

_log = structlog.get_logger(__name__)


class NextcloudStorageError(RuntimeError):
    """Raised when interactions with Nextcloud fail."""


@dataclass(frozen=True)
class _NextcloudConfig:
    base_url: str
    username: str
    password: str
    root_path: str
    timeout: float
    verify_tls: bool


class NextcloudClient:
    """Simple WebDAV client targeting the files endpoint."""

    def __init__(self, config: _NextcloudConfig):
        self._config = config
        self._auth = HTTPBasicAuth(config.username, config.password)
        self._base_files_url = self._build_base_url()
        self._lock = RLock()
        self._created_paths: set[str] = set()

    def _build_base_url(self) -> str:
        base = self._config.base_url.rstrip("/")
        user = quote(self._config.username.strip("/"))
        return f"{base}/remote.php/dav/files/{user}"

    def _full_path(self, rel_path: str) -> str:
        rel_path = rel_path.strip("/")
        parts = []
        if self._config.root_path:
            parts.append(self._config.root_path.strip("/"))
        if rel_path:
            parts.append(rel_path)
        encoded = "/".join(quote(part, safe="@!$&'()*+,;=:") for part in parts)
        return f"{self._base_files_url}/{encoded}" if encoded else self._base_files_url

    def _ensure_collection(self, rel_dir: str) -> None:
        """Ensure a directory (collection) exists by issuing MKCOL calls."""
        rel_dir = rel_dir.strip("/")
        if not rel_dir and self._config.root_path:
            rel_dir = self._config.root_path.strip("/")
        elif self._config.root_path:
            rel_dir = f"{self._config.root_path.strip('/')}/{rel_dir}" if rel_dir else self._config.root_path.strip("/")
        if not rel_dir:
            return
        segments = []
        with self._lock:
            for segment in rel_dir.split('/'):
                segments.append(segment)
                target = "/".join(segments)
                if target in self._created_paths:
                    continue
                url = self._full_path(target)
                resp = requests.request(
                    "MKCOL",
                    url,
                    auth=self._auth,
                    timeout=self._config.timeout,
                    verify=self._config.verify_tls,
                )
                if resp.status_code in (201, 405):
                    self._created_paths.add(target)
                    continue
                if resp.status_code == 409:
                    # Parent missing; retry next iteration which will attempt parent first
                    continue
                if resp.status_code >= 400:
                    raise NextcloudStorageError(
                        f"Failed to ensure collection '{target}': {resp.status_code} {resp.text}"
                    )
                self._created_paths.add(target)

    def upload_document(self, rel_path: str, content: bytes, content_type: str) -> None:
        """Upload a document to Nextcloud, creating any missing directories."""
        rel_path = rel_path.strip("/")
        directory = str(PurePosixPath(rel_path).parent)
        if directory and directory != ".":
            self._ensure_collection(directory)
        elif self._config.root_path:
            # Ensure root exists before uploading to top-level file
            self._ensure_collection("")
        url = self._full_path(rel_path)
        resp = requests.put(
            url,
            data=content,
            headers={"Content-Type": content_type, "OCS-APIREQUEST": "true"},
            auth=self._auth,
            timeout=self._config.timeout,
            verify=self._config.verify_tls,
        )
        if resp.status_code not in (200, 201, 204):
            raise NextcloudStorageError(
                f"Upload failed for '{rel_path}': {resp.status_code} {resp.text}"
            )


_client: Optional[NextcloudClient] = None
_client_lock = RLock()


def _slugify(value: str, replacement: str = "_") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", replacement, value)
    cleaned = cleaned.strip(replacement)
    return cleaned or "transcript"


def _select_client() -> NextcloudClient:
    global _client
    with _client_lock:
        if _client is not None:
            return _client
        settings = get_settings()
        if not settings.nextcloud_base_url or not settings.nextcloud_username or not settings.nextcloud_password:
            raise NextcloudStorageError("Nextcloud configuration is incomplete")
        config = _NextcloudConfig(
            base_url=settings.nextcloud_base_url,
            username=settings.nextcloud_username,
            password=settings.nextcloud_password,
            root_path=settings.nextcloud_root_path,
            timeout=float(settings.nextcloud_timeout_seconds),
            verify_tls=bool(settings.nextcloud_verify_tls),
        )
        _client = NextcloudClient(config)
        # Ensure root path exists upfront to avoid races on first upload
        try:
            _client._ensure_collection("")
        except NextcloudStorageError:
            _client = None
            raise
        return _client


def store_transcript_payload(
    record_id: int,
    filename: str,
    text: str,
    summary: Optional[str],
    enrichment: Optional[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist structured transcript data to Nextcloud.

    Parameters
    ----------
    record_id: int
        Identifier returned from the SQL persistence layer.
    filename: str
        Original filename of the audio asset.
    text: str
        Full transcript text.
    summary: Optional[str]
        Generated summary (if available).
    enrichment: Optional[Dict[str, Any]]
        Structured enrichment entities.
    metadata: Optional[Dict[str, Any]]
        Additional metadata such as source or correlation IDs.
    """
    settings = get_settings()
    if settings.storage_provider.lower() != "nextcloud":
        return
    try:
        client = _select_client()
    except NextcloudStorageError as exc:  # pragma: no cover - configuration errors
        _log.error("nextcloud/config-error", error=str(exc))
        return

    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    safe_name = _slugify(PurePosixPath(filename).stem or "transcript")
    base_name = f"{now.strftime('%H%M%S')}-{record_id}-{safe_name}"
    json_payload: Dict[str, Any] = {
        "record_id": record_id,
        "filename": filename,
        "text": text,
        "summary": summary,
        "enrichment": enrichment or {},
        "metadata": metadata or {},
        "stored_at": now.isoformat(),
    }
    json_rel_path = f"{date_path}/{base_name}.json"
    text_rel_path = f"{date_path}/{base_name}.txt"

    try:
        client.upload_document(
            json_rel_path,
            json.dumps(json_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            "application/json; charset=utf-8",
        )
        client.upload_document(
            text_rel_path,
            text.encode("utf-8"),
            "text/plain; charset=utf-8",
        )
        _log.info(
            "nextcloud/uploaded",
            json_path=json_rel_path,
            text_path=text_rel_path,
            record_id=record_id,
        )
        nextcloud_upload_success_total.inc()
    except NextcloudStorageError as exc:
        nextcloud_upload_failure_total.labels(reason="client_error").inc()
        _log.error(
            "nextcloud/upload-failed",
            error=str(exc),
            record_id=record_id,
            filename=filename,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors
        nextcloud_upload_failure_total.labels(reason="network_error").inc()
        _log.error(
            "nextcloud/network-error",
            error=str(exc),
            record_id=record_id,
            filename=filename,
        )