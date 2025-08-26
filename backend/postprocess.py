"""Lightweight transcription post-processing utilities."""
from __future__ import annotations

import re
from typing import List


def normalize_text(text: str) -> str:
    """Basic cleanup: collapse whitespace and trim."""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
