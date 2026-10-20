from ..types import ChangeSuggestion, RuleOutcome, SchemeCriteria, StudentProfile
from .base import EligibilityRule


class MinimumNQFLevelRule(EligibilityRule):
    name = "Minimum NQF Level"
    condition_desc = "applicant.nqf_level >= scheme.min_nqf_level"

    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        return scheme.min_nqf_level is not None

    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        min_nqf = scheme.min_nqf_level
        if student.nqf_level >= min_nqf:
            return RuleOutcome(
                True,
                f"Current NQF level ({student.nqf_level}) meets or exceeds the required level ({min_nqf}).",
            )

        change = ChangeSuggestion(
            criterion="Minimum NQF Level",
            current_circumstance=f"NQF Level {student.nqf_level}",
            required_to_qualify=f"NQF Level {min_nqf} or higher",
            pathway="Applying in a Later Intake / Academic Progression",
            suggestion=(
                f"Applying in a later intake or subsequent academic year once you have progressed in your curriculum or graduated "
                f"to NQF Level {min_nqf} will naturally qualify you for this scheme without misrepresenting your current academic standing."
            ),
        )
        return RuleOutcome(
            False,
            f"Current NQF level ({student.nqf_level}) is below the required level ({min_nqf}).",
            change,
        )
