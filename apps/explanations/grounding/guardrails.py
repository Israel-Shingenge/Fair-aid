"""
Deterministic output checks. The LLM's text is only ever shown if it passes these.

The model can't change an eligibility result (results come from the engine and are attached to the
response by our code, not by the model). These checks stop the *prose* from contradicting the engine,
making promises, inventing numbers or links.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from apps.prescreening.engine import LIKELY_ELIGIBLE, NOT_ELIGIBLE, POSSIBLY_ELIGIBLE

from .facts import SchemeFacts, allowed_numbers, extract_numbers

MAX_CHARS = 1200
_SMALL_INTS = set(range(0, 15))  # counts like "two criteria", "14 regions"

_NEGATIVE = re.compile(
    r"\b(not (?:currently |likely |yet |really )?(?:eligible|qualif\w*)|ineligible|"
    r"(?:do|does|did|will|would|can)\s*(?:not|n't)\s+qualify|don't qualify|won't qualify|cannot qualify|disqualif\w*)",
    re.I,
)
_POSITIVE = re.compile(
    r"\b(you(?: are|'re) (?:likely |definitely |fully |clearly )?eligible|you (?:do |will |would |can )?qualify|"
    r"you(?:'ll| will| would|'d) (?:now |then )?be (?:likely |definitely |fully |clearly )?eligible|likely eligible|meet all(?: the)? (?:criteria|requirements))",
    re.I,
)
_PROMISE = re.compile(
    r"\b(guarantee\w*|will be (?:awarded|approved|accepted|funded)|certain(?:ly)? (?:to )?(?:get|receive|win)|"
    r"you(?:'ll| will) (?:get|receive|be given) (?:the|a) (?:bursary|funding|grant|scholarship))",
    re.I,
)
_MISREPRESENT = re.compile(r"\b(lie|lying|falsify|fake|pretend|misrepresent|exaggerate)\b", re.I)
_LINK = re.compile(r"(https?://|www\.|\b\S+\.(?:com|org|na|gov)\b)", re.I)
_SENTENCES = re.compile(r"(?<=[.!?])\s+")
# Clause splitting + "this clause talks about the situation BEFORE the change" markers, used for what-if
# answers, where "you are not eligible now, but would be likely eligible with NQF 7" is a faithful sentence.
_CLAUSES = re.compile(r"(?<=[.!?])\s+|;\s*|,?\s+(?:but|however|whereas|while|though|yet)\s+", re.I)
_BEFORE_MARKER = re.compile(
    r"\b(before|previously|currently|right now|at the moment|today|originally|as it stands|at present|were|was|did)\b", re.I
)


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: Optional[str] = None


def _status_conflict(sentence: str, status: str) -> Optional[str]:
    has_negative = bool(_NEGATIVE.search(sentence))
    positive_text = _NEGATIVE.sub(" ", sentence)  # "not likely eligible" must not count as positive
    has_positive = bool(_POSITIVE.search(positive_text))
    if status == NOT_ELIGIBLE and has_positive:
        return "claims eligibility for a scheme the engine marked 'Not eligible'"
    if status == LIKELY_ELIGIBLE and has_negative:
        return "claims ineligibility for a scheme the engine marked 'Likely eligible'"
    if status == POSSIBLY_ELIGIBLE and (has_positive or has_negative):
        return "states a definite verdict for a scheme the engine marked 'Possibly eligible'"
    return None


def validate_text(
    text: str,
    facts: Iterable[SchemeFacts],
    scope: Optional[SchemeFacts] = None,
    question: str = "",
    prior_statuses: Optional[dict] = None,
) -> Verdict:
    """
    ``scope``: the single scheme this text is about (every sentence is checked against it, unless the
    sentence names a different scheme). With no scope, sentences are checked against the scheme(s) they name.
    """
    facts = list(facts)
    if not text or not text.strip():
        return Verdict(False, "empty text")
    if len(text) > MAX_CHARS:
        return Verdict(False, "too long")
    if _LINK.search(text):
        return Verdict(False, "contains a link")
    if _PROMISE.search(text):
        return Verdict(False, "makes a promise about funding")
    if _MISREPRESENT.search(text):
        return Verdict(False, "mentions misrepresenting circumstances")

    allowed: Set[float] = _SMALL_INTS | allowed_numbers(facts, extra_text=question)
    for number in extract_numbers(text):
        if number not in allowed:
            return Verdict(False, f"number {number:g} is not in the engine's facts")

    splitter = _CLAUSES if prior_statuses else _SENTENCES
    for sentence in splitter.split(text.strip()):
        if not sentence:
            continue
        named = [f for f in facts if f.scheme_name.lower() in sentence.lower()]
        targets: List[SchemeFacts] = named or ([scope] if scope else [])
        for target in targets:
            conflict = _status_conflict(sentence, target.match_status)
            if conflict and prior_statuses and _BEFORE_MARKER.search(sentence):
                # A clause about the situation before the change may state the BEFORE result.
                prior = prior_statuses.get(target.scheme_name)
                if prior and _status_conflict(sentence, prior) is None:
                    conflict = None
            if conflict:
                return Verdict(False, f"{target.scheme_name}: {conflict}")
    return Verdict(True)
