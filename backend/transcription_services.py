"""Transcription service layer.

Contains pluggable backends for cloud (OpenAI) and local Whisper inference.
"""
from __future__ import annotations

from typing import Optional
import os
import tempfile
import subprocess

import requests

from config import get_settings

# Defer whisper import unless local transcription explicitly enabled
settings_for_import = get_settings()
if settings_for_import.enable_local_transcription:
    try:  # lazy import whisper only if enabled
        import whisper  # type: ignore
    except Exception:  # pragma: no cover
        whisper = None  # fallback if not installed
else:  # pragma: no cover
    whisper = None


_whisper_model = None


def _load_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        settings = get_settings()
        # Bypass heavy load in test mode or when whisper not installed in non-prod
        if os.environ.get("FAST_TEST_MODE") == "1" or (whisper is None and os.environ.get('ENV','dev') != 'prod'):
            class _Dummy:  # pragma: no cover
                def transcribe(self, path):
                    return {"text": "dummy transcription"}
            _whisper_model = _Dummy()
        else:
            if whisper is None:
                raise RuntimeError("whisper package not available")
            _whisper_model = whisper.load_model(settings.whisper_model_size)
    return _whisper_model


ALLOWED_MIME_TYPES = {
    "audio/ogg",
    "audio/opus",
    "audio/aac",
    "audio/mp3",
    "audio/mpeg",
    "audio/webm",
    "audio/mp4",
    "audio/wav",
}


def validate_audio_mime(mime: str | None):
    if not mime or mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {mime}")


def downsample(input_path: str, output_path: str, sample_rate: int = 16000) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def transcribe_local(data: bytes, filename: str, mime_type: str | None) -> str:
    validate_audio_mime(mime_type)
    model = _load_whisper_model()
    with tempfile.TemporaryDirectory() as td:
        raw = os.path.join(td, filename)
        with open(raw, "wb") as f:
            f.write(data)
        downsampled = os.path.join(td, f"ds_{filename}")
        downsample(raw, downsampled)
        result = model.transcribe(downsampled)
    return result.get("text", "")


def transcribe_cloud(
    data: bytes,
    filename: str,
    mime_type: str | None,
    *,
    prompt: str | None = None,
    language: str | None = None,
    temperature: float | None = None,
) -> str:
    """Call OpenAI Whisper API.

    Parameters
    ----------
    data: raw audio bytes
    filename: original filename
    mime_type: detected/declared mime type
    prompt: optional vocabulary / context prompt to bias decoding
    language: optional ISO language code (e.g. 'en', 'es'); if None let model auto-detect
    temperature: optional decoding temperature (0.0 – 1.0). Lower = more deterministic.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    validate_audio_mime(mime_type)
    openai_url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    files = {"file": (filename, data, mime_type or "audio/mpeg")}
    # Build form fields. Only include optional params if provided (API rejects unknown empty fields sometimes).
    data_form: dict[str, object] = {"model": "whisper-1"}
    if prompt:
        data_form["prompt"] = prompt[:2000]  # guard length
    if language and language.lower() != "auto":
        data_form["language"] = language
    if temperature is not None:
        # clamp for safety
        if temperature < 0:
            temperature = 0.0
        if temperature > 1.0:
            temperature = 1.0
        data_form["temperature"] = temperature
    resp = requests.post(openai_url, headers=headers, files=files, data=data_form, timeout=120)
    resp.raise_for_status()
    return resp.json().get("text", "")


def preload_models_if_configured():  # startup helper
    try:
        settings = get_settings()
        # Skip heavy load in fast test mode
        if os.environ.get("FAST_TEST_MODE") == "1":
            return
        if settings.enable_local_transcription:
            _load_whisper_model()
    except Exception:
        pass
