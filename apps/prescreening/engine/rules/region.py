from ..types import ChangeSuggestion, RuleOutcome, SchemeCriteria, StudentProfile
from .base import EligibilityRule


class RegionalEligibilityRule(EligibilityRule):
    name = "Eligible Region"
    condition_desc = "applicant.region in scheme.eligible_regions"

    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        return bool(scheme.eligible_regions)

    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        regions_lower = [r.lower().strip() for r in scheme.eligible_regions]
        supported = ", ".join(scheme.eligible_regions)

        if student.region.lower().strip() in regions_lower:
            return RuleOutcome(True, f"Region '{student.region}' is eligible for this regional scheme.")

        change = ChangeSuggestion(
            criterion="Regional Eligibility",
            current_circumstance=student.region,
            required_to_qualify=f"One of: {supported}",
            pathway="Official Domicile Verification / National Alternatives",
            suggestion=(
                f"This regional development fund is earmarked for students originating from {supported}. "
                "If you completed secondary schooling or have registered family domicile in one of these regions with valid proof "
                "of residence, submit that documentation. Otherwise, focus on nationwide schemes open across all 14 regions."
            ),
        )
        return RuleOutcome(
            False,
            f"Region '{student.region}' is not eligible. Supported regions: {supported}.",
            change,
        )
