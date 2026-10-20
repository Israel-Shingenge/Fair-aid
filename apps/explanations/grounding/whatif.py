"""
What-if questions ("what if my income were 200,000?") without letting the model decide anything.

The model may only *translate* the question into a change. This module validates that change strictly,
and the interpretable engine then re-runs on the changed profile. Pure Python (no Django).
"""
from __future__ import annotations

import dataclasses
import re
from typing import Any, Dict, Optional

from apps.prescreening.engine import StudentProfile

from .facts import extract_numbers

# Only circumstances a student could legitimately change. `has_disability` is deliberately NOT here:
# a what-if must never help someone "become" eligible by altering a medical status.
NUMERIC_FIELDS = {"nqf_level": (1, 10, True), "household_income": (0.0, 10_000_000.0, False)}  # (min, max, integer?)
TEXT_FIELDS = ("field_of_study", "region")
ALLOWED_FIELDS = tuple(NUMERIC_FIELDS) + TEXT_FIELDS

_K_SUFFIX = re.compile(r"(\d+(?:[.,]\d+)?)\s*k\b", re.I)


def numbers_in(text: str) -> set:
    """Numbers a student wrote, including shorthand like '200k'."""
    values = set(extract_numbers(text))
    for match in _K_SUFFIX.findall(text):
        try:
            values.add(float(match.replace(",", ".")) * 1000)
        except ValueError:
            continue
    return values


def validate_changes(changes: Any, source_text: str) -> Optional[Dict[str, Any]]:
    """
    Return a cleaned change set, or None if anything is off. Every value must be literally traceable to
    what the student wrote (``source_text``), so the model cannot invent or tweak parameters.
    """
    if not isinstance(changes, dict) or not changes:
        return None
    if any(key not in ALLOWED_FIELDS for key in changes):
        return None

    typed = numbers_in(source_text)
    lowered = source_text.lower()
    clean: Dict[str, Any] = {}
    for key, raw in changes.items():
        if key in NUMERIC_FIELDS:
            low, high, integer = NUMERIC_FIELDS[key]
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                return None
            value = float(raw)
            if not low <= value <= high or value not in typed:
                return None
            if integer:
                if value != int(value):
                    return None
                clean[key] = int(value)
            else:
                clean[key] = value
        else:
            if not isinstance(raw, str):
                return None
            value = " ".join(raw.split())
            if not value or len(value) > 60 or value.lower() not in lowered:
                return None
            clean[key] = value
    return clean


def apply_changes(profile: StudentProfile, changes: Dict[str, Any]) -> StudentProfile:
    return dataclasses.replace(profile, **changes)

def describe(changes: Dict[str, Any]) -> str:
    parts = []
    if "nqf_level" in changes:
        parts.append(f"your NQF level were {changes['nqf_level']}")
    if "household_income" in changes:
        parts.append(f"your household income were {changes['household_income']:,.0f} NAD")
    if "field_of_study" in changes:
        parts.append(f"you studied {changes['field_of_study']}")
    if "region" in changes:
        parts.append(f"you lived in {changes['region']}")
    return " and ".join(parts)
