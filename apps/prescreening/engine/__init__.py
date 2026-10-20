"""Framework-free eligibility decision engine (pure Python, no Django imports)."""
from .evaluator import BursaryDecisionTree, evaluate_scheme
from .types import (
    LIKELY_ELIGIBLE,
    NOT_ELIGIBLE,
    POSSIBLY_ELIGIBLE,
    ChangeSuggestion,
    DecisionPathStep,
    MatchExplanation,
    SchemeCriteria,
    SchemeMatchResult,
    StudentProfile,
)

__all__ = [
    "BursaryDecisionTree",
    "evaluate_scheme",
    "StudentProfile",
    "SchemeCriteria",
    "SchemeMatchResult",
    "ChangeSuggestion",
    "DecisionPathStep",
    "MatchExplanation",
    "LIKELY_ELIGIBLE",
    "POSSIBLY_ELIGIBLE",
    "NOT_ELIGIBLE",
]
