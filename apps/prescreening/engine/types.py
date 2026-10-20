"""
Plain value objects exchanged with the decision engine.

The engine knows nothing about Django, DRF or the database: it receives a ``StudentProfile`` and a
``SchemeCriteria`` and returns a ``SchemeMatchResult``. Adapters in the web layer translate to and
from these types, which keeps the engine unit-testable on its own.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

LIKELY_ELIGIBLE = "Likely eligible"
POSSIBLY_ELIGIBLE = "Possibly eligible"
NOT_ELIGIBLE = "Not eligible"

DEFAULT_GOVERNANCE_SAFEGUARD = (
    "ADVISORY ONLY: FairAid pre-screens and informs. It cannot submit applications or make "
    "binding funding decisions."
)

@dataclass(frozen=True)
class StudentProfile:
    nqf_level: int
    field_of_study: str
    household_income: float
    region: str
    has_disability: bool = False


@dataclass(frozen=True)
class SchemeCriteria:
    name: str
    description: str = ""
    min_nqf_level: Optional[int] = None
    max_household_income: Optional[float] = None
    requires_disability: bool = False
    eligible_fields_of_study: Optional[Tuple[str, ...]] = None
    eligible_regions: Optional[Tuple[str, ...]] = None

@dataclass(frozen=True)
class ChangeSuggestion:
    criterion: str
    current_circumstance: str
    required_to_qualify: str
    pathway: str
    suggestion: str


@dataclass(frozen=True)
class RuleOutcome:
    """What a single eligibility rule concluded for one student/scheme pair."""

    passed: bool
    details: str
    change: Optional[ChangeSuggestion] = None

@dataclass(frozen=True)
class MatchExplanation:
    criterion: str
    is_met: bool
    message: str

@dataclass(frozen=True)
class DecisionPathStep:
    step: int
    rule: str
    condition: str
    passed: bool
    details: str

@dataclass(frozen=True)
class SchemeMatchResult:
    scheme_name: str
    description: str
    match_status: str
    match_score: float
    plain_language_explanation: str
    decision_path: List[DecisionPathStep]
    explanations: List[MatchExplanation]
    factors_that_helped: List[str] = field(default_factory=list)
    factors_that_hurt: List[str] = field(default_factory=list)
    what_would_change_this: List[ChangeSuggestion] = field(default_factory=list)
    actionable_feedback: List[str] = field(default_factory=list)
    is_binding_decision: bool = False
    allows_automated_submission: bool = False
    governance_safeguard: str = DEFAULT_GOVERNANCE_SAFEGUARD
