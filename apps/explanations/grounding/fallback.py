"""
Deterministic explanations built straight from the engine's output. Used whenever the LLM is
unavailable, rate-limited, disabled, or its text fails validation. The product never depends on the LLM.
"""
from typing import List, Optional
from apps.prescreening.engine import LIKELY_ELIGIBLE
from .facts import SchemeFacts

def explain_scheme(f: SchemeFacts) -> str:
    return f.engine_summary or f"Pre-screening result for {f.scheme_name}: {f.match_status}."

def answer_about_scheme(f: SchemeFacts) -> str:
    parts = [f"For {f.scheme_name}, the pre-screening result was: {f.match_status}."]
    if f.hurt:
        parts.append("What counted against the match: " + " ".join(h.rstrip(".") + "." for h in f.hurt))
    if f.helped:
        parts.append("What helped: " + " ".join(h.rstrip(".") + "." for h in f.helped))
    if f.changes:
        parts.append(
            "What could change this: "
            + "; ".join(f"{c.criterion} ({c.pathway})" for c in f.changes)
            + "."
        )
    elif f.match_status == LIKELY_ELIGIBLE:
        parts.append("All the criteria we checked were met.")
    return " ".join(parts)

def answer_general(facts: List[SchemeFacts], hint: bool = True) -> str:
    lines = [f"{f.scheme_name}: {f.match_status}." for f in facts]
    text = "Here is your pre-screening result for each scheme. " + " ".join(lines)
    if hint:
        text += " Name a scheme in your question (for example, \"Why wasn't I matched to <scheme>?\") for a detailed explanation."
    return text

def overall_summary(facts: List[SchemeFacts]) -> str:
    """Deterministic headline (counts only), so no verdict wording ever comes from the model."""
    counts = {}
    for f in facts:
        counts[f.match_status] = counts.get(f.match_status, 0) + 1
    if not facts:
        return "There were no bursary schemes to pre-screen against."
    breakdown = ", ".join(f"{n} {status.lower()}" for status, n in counts.items())
    return f"You were pre-screened against {len(facts)} scheme(s): {breakdown}."

def whatif_answer(description: str, diffs: List[dict], focus_name: Optional[str] = None) -> str:
    """Engine-worded what-if answer: built only from the before/after results the engine produced."""
    text = f"If {description}, the pre-screening engine would give these results (a what-if only; nothing is saved)."
    changed = [d for d in diffs if d["changed"]]
    if changed:
        text += " " + " ".join(f"{d['scheme_name']}: {d['before_status']} would become {d['after_status']}." for d in changed)
    else:
        text += " None of the schemes would change result."
    if focus_name:
        focus = next((d for d in diffs if d["scheme_name"] == focus_name and not d["changed"]), None)
        if focus:
            text += f" {focus_name} would stay {focus['after_status']}."
    text += " For an official record, run the pre-screening again with your updated details."
    return text
