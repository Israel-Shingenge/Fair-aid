"""
Fact sheets: the ONLY information the LLM is allowed to see and talk about.

Built from the stored output of the interpretable engine (a ``PrescreenRecord.results`` entry), never
from the student's raw input and never re-evaluated. Pure Python, no Django.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class RuleFact:
    criterion: str
    met: bool
    detail: str

@dataclass(frozen=True)
class ChangeFact:
    criterion: str
    required_to_qualify: str
    pathway: str

@dataclass(frozen=True)
class SchemeFacts:
    scheme_name: str
    match_status: str  # authoritative: copied from the engine, never from the LLM
    match_score: float
    rules: Tuple[RuleFact, ...]
    changes: Tuple[ChangeFact, ...]
    engine_summary: str  # the engine's own deterministic explanation (used as fallback)
    helped: Tuple[str, ...] = ()
    hurt: Tuple[str, ...] = ()

    def for_prompt(self) -> Dict[str, Any]:
        return {
            "scheme_name": self.scheme_name,
            "engine_result": self.match_status,
            "criteria_met_percent": self.match_score,
            "criteria_checked": [
                {"criterion": r.criterion, "met": r.met, "detail": r.detail} for r in self.rules
            ],
            "legitimate_pathways_that_could_change_the_result": [
                {"criterion": c.criterion, "required": c.required_to_qualify, "pathway": c.pathway}
                for c in self.changes
            ],
        }

def scheme_facts_from_result(result: Dict[str, Any]) -> SchemeFacts:
    return SchemeFacts(
        scheme_name=result["scheme_name"],
        match_status=result["match_status"],
        match_score=float(result["match_score"]),
        rules=tuple(RuleFact(e["criterion"], bool(e["is_met"]), e["message"]) for e in result.get("explanations", [])),
        changes=tuple(
            ChangeFact(c["criterion"], c["required_to_qualify"], c["pathway"])
            for c in result.get("what_would_change_this", [])
        ),
        engine_summary=result.get("plain_language_explanation", ""),
        helped=tuple(result.get("factors_that_helped", [])),
        hurt=tuple(result.get("factors_that_hurt", [])),
    )

def facts_from_results(results: Iterable[Dict[str, Any]]) -> List[SchemeFacts]:
    return [scheme_facts_from_result(r) for r in results]


# --- numbers ------------------------------------------------------------------------------------
_NUMBER = re.compile(r"\d[\d,\s]*(?:\.\d+)?")

def extract_numbers(text: str) -> Set[float]:
    """Numeric values in ``text``; '250,000.00', '250 000' and '250000' all parse to 250000.0."""
    values: Set[float] = set()
    for token in _NUMBER.findall(text):
        cleaned = re.sub(r"[,\s]", "", token)
        try:
            values.add(float(cleaned))
        except ValueError:
            continue
    return values

def allowed_numbers(facts: Iterable[SchemeFacts], extra_text: str = "") -> Set[float]:
    text = " ".join(
        [extra_text]
        + [
            " ".join([f.scheme_name, f.match_status, str(f.match_score)]
                     + [r.detail for r in f.rules]
                     + [c.required_to_qualify for c in f.changes])
            for f in facts
        ]
    )
    return extract_numbers(text)

# --- which scheme is a question about? -----------------------------------------------------------
def resolve_scheme(question: str, scheme_name: Optional[str], facts: List[SchemeFacts]) -> Optional[SchemeFacts]:
    """Explicit ``scheme_name`` wins; otherwise a scheme is chosen only if the question clearly names exactly one."""
    if scheme_name:
        wanted = scheme_name.strip().lower()
        return next((f for f in facts if f.scheme_name.lower() == wanted), None)

    q = question.lower()
    mentioned = [f for f in facts if f.scheme_name.lower() in q]
    if not mentioned:
        first_words = {f.scheme_name: f.scheme_name.split()[0].lower() for f in facts}
        mentioned = [
            f for f in facts
            if len(first_words[f.scheme_name]) >= 3
            and sum(w == first_words[f.scheme_name] for w in first_words.values()) == 1
            and re.search(rf"\b{re.escape(first_words[f.scheme_name])}\b", q)
        ]
    return mentioned[0] if len(mentioned) == 1 else None
