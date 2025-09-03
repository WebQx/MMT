"""Helper functions to break down large transcription functions."""

from typing import Optional
from fastapi import HTTPException
from postprocess import normalize_text
from audit import AuditEvent, audit
from persistence import async_task_create, async_task_update
from metrics import async_tasks_started_total, async_tasks_completed_total, async_tasks_failed_total
import hashlib
import os
import time


def create_async_task(filename: str) -> str:
    """Create async transcription task and return task ID."""
    task_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    async_task_create(task_id, filename)
    async_tasks_started_total.inc()
    return task_id


def handle_transcription_result(task_id: str, filename: str, text: str, 
                              publish_fn, correlation_id: Optional[str] = None):
    """Handle successful transcription result."""
    text_normalized = normalize_text(text)
    publish_fn(filename, text_normalized, correlation_id)
    audit(AuditEvent.TRANSCRIPT_STORE, filename=filename, task_id=task_id, async_mode=True)
    async_task_update(task_id, 'done', result_text=text_normalized)
    async_tasks_completed_total.inc()


def handle_transcription_error(task_id: str, error: Exception):
    """Handle transcription error."""
    async_task_update(task_id, 'error', error=str(error))
    async_tasks_failed_total.inc()


def validate_file_upload(file_data: bytes, max_size: int):
    """Validate uploaded file size."""
    if len(file_data) > max_size:
        raise HTTPException(status_code=413, detail="File too large")


def process_json_body(body: dict) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float]]:
    """Extract and validate JSON body parameters."""
    raw_text = body.get("text")
    audio_b64 = body.get("audio_b64")
    language = body.get("language")
    prompt = body.get("prompt")
    temperature = body.get("temperature")
    
    return raw_text, audio_b64, language, prompt, temperature