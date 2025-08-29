"""Chart template definitions and parsing / prompt generation.

Provides:
 - Data models for sections/fields
 - Registry of templates (initial: general_soap)
 - Simple rule-based parser to extract structured fields from raw transcript
 - Prompt generator for improved transcription guidance
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re


@dataclass
class ChartField:
    key: str
    label: str
    description: str
    required: bool = False
    hints: List[str] = field(default_factory=list)


@dataclass
class ChartSection:
    key: str
    label: str
    fields: List[ChartField]


@dataclass
class ChartTemplate:
    key: str
    label: str
    sections: List[ChartSection]
    version: str = "1.0"
    guidance: Optional[str] = None


# Initial SOAP style template
SOAP_TEMPLATE = ChartTemplate(
    key="general_soap",
    label="General SOAP Encounter",
    guidance="Capture concise, clinically relevant details. Avoid PHI beyond what is necessary.",
    sections=[
        ChartSection(
            key="subjective",
            label="Subjective",
            fields=[
                ChartField("chief_complaint", "Chief Complaint", "Primary reason for visit", True, ["1-2 short sentences"]),
                ChartField("hpi", "History of Present Illness", "Chronological narrative of symptoms", True),
                ChartField("ros", "Review of Systems", "Pertinent positives/negatives", False),
            ],
        ),
        ChartSection(
            key="objective",
            label="Objective",
            fields=[
                ChartField("vitals", "Vitals", "Key vital signs if stated", False),
                ChartField("exam", "Physical Exam", "Pertinent exam findings", True),
            ],
        ),
        ChartSection(
            key="assessment",
            label="Assessment",
            fields=[
                ChartField("impression", "Impression", "Primary working diagnosis or differential", True),
            ],
        ),
        ChartSection(
            key="plan",
            label="Plan",
            fields=[
                ChartField("tests", "Tests/Orders", "Diagnostics or labs ordered", False),
                ChartField("treatment", "Therapies/Medications", "Treatment steps or meds", False),
                ChartField("follow_up", "Follow-up", "Timing or contingencies", False),
            ],
        ),
    ],
)

TEMPLATES: Dict[str, ChartTemplate] = {SOAP_TEMPLATE.key: SOAP_TEMPLATE}


def list_templates() -> List[dict]:
    return [template_summary(t) for t in TEMPLATES.values()]


def template_summary(t: ChartTemplate) -> dict:
    return {
        "key": t.key,
        "label": t.label,
        "version": t.version,
        "sections": [
            {
                "key": s.key,
                "label": s.label,
                "fields": [
                    {
                        "key": f.key,
                        "label": f.label,
                        "required": f.required,
                        "description": f.description,
                        "hints": f.hints,
                    }
                    for f in s.fields
                ],
            }
            for s in t.sections
        ],
        "guidance": t.guidance,
    }


def get_template(key: str) -> ChartTemplate | None:
    return TEMPLATES.get(key)


def parse_transcript(raw: str, template_key: str = SOAP_TEMPLATE.key) -> dict:
    """Very lightweight heuristic parser using section headers.

    Looks for lines starting with a known field label or common synonyms.
    This is intentionally simple; can be replaced with ML/NLP later.
    """
    tpl = get_template(template_key)
    if not tpl:
        raise ValueError("Unknown template")
    # Pre-build patterns
    field_patterns: Dict[str, re.Pattern] = {}
    for sec in tpl.sections:
        for f in sec.fields:
            variants = [f.label, f.label.replace(' ', ''), f.key.replace('_', ' ')]
            pat = r'^(?:' + '|'.join(re.escape(v) for v in variants) + r')[:\-]\s*(.*)$'
            field_patterns[f.key] = re.compile(pat, re.IGNORECASE)
    results = {f.key: None for sec in tpl.sections for f in sec.fields}
    # Scan line by line
    for line in raw.splitlines():
        line = line.strip()
        for key, rgx in field_patterns.items():
            m = rgx.match(line)
            if m:
                val = m.group(1).strip()
                if results[key]:  # append if multiple
                    results[key] = results[key] + ' ' + val
                else:
                    results[key] = val
    return results


def build_prompt(template_key: str = SOAP_TEMPLATE.key) -> str:
    tpl = get_template(template_key)
    if not tpl:
        raise ValueError("Unknown template")
    lines = [f"You are assisting in creating a structured clinical note: {tpl.label} (v{tpl.version})."]
    if tpl.guidance:
        lines.append(f"Guidance: {tpl.guidance}")
    for sec in tpl.sections:
        lines.append(f"Section: {sec.label}")
        for f in sec.fields:
            req = 'required' if f.required else 'optional'
            hint = f" Hints: {', '.join(f.hints)}" if f.hints else ''
            lines.append(f" - {f.label} ({req}): {f.description}.{hint}")
    lines.append("Return concise, clinically relevant phrasing. Avoid duplicating patient identifiers.")
    return '\n'.join(lines)


__all__ = [
    'ChartField', 'ChartSection', 'ChartTemplate', 'list_templates', 'get_template', 'parse_transcript', 'build_prompt'
]
