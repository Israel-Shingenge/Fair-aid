from ..types import ChangeSuggestion, RuleOutcome, SchemeCriteria, StudentProfile
from .base import EligibilityRule


class FieldOfStudyRule(EligibilityRule):
    name = "Eligible Field of Study"
    condition_desc = "applicant.field_of_study in scheme.eligible_fields_of_study"

    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        return bool(scheme.eligible_fields_of_study)

    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        eligible_lower = [f.lower().strip() for f in scheme.eligible_fields_of_study]
        supported = ", ".join(scheme.eligible_fields_of_study)

        if student.field_of_study.lower().strip() in eligible_lower:
            return RuleOutcome(True, f"Field of study '{student.field_of_study}' is supported by this scheme.")

        change = ChangeSuggestion(
            criterion="Field of Study",
            current_circumstance=student.field_of_study,
            required_to_qualify=f"One of: {supported}",
            pathway="Academic Program Choice / Dual Major / Related Qualification",
            suggestion=(
                f"If you are considering enrolling in a dual major, switching majors, or pursuing a postgraduate qualification "
                f"in one of the approved disciplines ({supported}), this bursary would become an option. "
                f"Alternatively, retain your current specialization and seek out bursaries supporting {student.field_of_study}."
            ),
        )
        return RuleOutcome(
            False,
            f"Field of study '{student.field_of_study}' is not covered. Supported: {supported}.",
            change,
        )
