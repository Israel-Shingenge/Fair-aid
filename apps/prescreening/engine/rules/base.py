from abc import ABC, abstractmethod

from ..types import RuleOutcome, SchemeCriteria, StudentProfile


class EligibilityRule(ABC):
    """One independently testable eligibility criterion."""

    name: str
    condition_desc: str
    is_hard_gate: bool = False

    @abstractmethod
    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        """Whether the scheme defines this criterion at all."""

    @abstractmethod
    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        """Evaluate the student against this rule for the given scheme."""
