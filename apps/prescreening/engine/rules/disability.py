from ..types import ChangeSuggestion, RuleOutcome, SchemeCriteria, StudentProfile
from .base import EligibilityRule


class DisabilityRequirementRule(EligibilityRule):
    name = "Disability Requirement Gate"
    condition_desc = "applicant.has_disability == True"
    is_hard_gate = True

    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        return bool(scheme.requires_disability)

    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        if student.has_disability:
            return RuleOutcome(True, "Meets the recognized disability requirement.")

        change = ChangeSuggestion(
            criterion="Disability Requirement",
            current_circumstance="No recognised disability declared",
            required_to_qualify="Recognised disability required by sponsor policy",
            pathway="Alternative Scheme Selection",
            suggestion=(
                "This scheme is strictly earmarked by policy for students with recognised disabilities. "
                "Because medical and disability status should never be misrepresented, this requirement cannot be altered. "
                "We strongly recommend redirecting your application to general national schemes (such as the NSFAF Core Grant) "
                "that do not require disability criteria."
            ),
        )
        return RuleOutcome(
            False, "This scheme is strictly reserved for applicants with recognised disabilities.", change
        )
