"""Simple rule-based entity extraction & summarization placeholders."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Any


MED_PATTERN = re.compile(r"\b(?:aspirin|ibuprofen|metformin|lisinopril)\b", re.IGNORECASE)
PROBLEM_PATTERN = re.compile(r"\b(?:diabetes|hypertension|asthma)\b", re.IGNORECASE)


@dataclass
class ExtractionResult:
    medications: List[str]
    problems: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"medications": self.medications, "problems": self.problems}


def extract_entities(text: str) -> ExtractionResult:
    meds = sorted({m.lower() for m in MED_PATTERN.findall(text)})
    probs = sorted({p.lower() for p in PROBLEM_PATTERN.findall(text)})
    return ExtractionResult(medications=meds, problems=probs)


def summarize_text(text: str, max_sentences: int = 2) -> str:
    # naive summary: pick first N sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:max_sentences])
