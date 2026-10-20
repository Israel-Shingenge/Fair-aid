from ..types import ChangeSuggestion, RuleOutcome, SchemeCriteria, StudentProfile
from .base import EligibilityRule


class HouseholdIncomeRule(EligibilityRule):
    name = "Household Income Ceiling"
    condition_desc = "applicant.household_income <= scheme.max_household_income"

    def is_applicable(self, scheme: SchemeCriteria) -> bool:
        return scheme.max_household_income is not None

    def evaluate(self, student: StudentProfile, scheme: SchemeCriteria) -> RuleOutcome:
        max_income = scheme.max_household_income
        if student.household_income <= max_income:
            return RuleOutcome(
                True,
                f"Household income ({student.household_income:,.2f} NAD) is within the maximum limit ({max_income:,.2f} NAD).",
            )

        diff = student.household_income - max_income
        change = ChangeSuggestion(
            criterion="Household Income",
            current_circumstance=f"{student.household_income:,.2f} NAD annual household income",
            required_to_qualify=f"At or below {max_income:,.2f} NAD (currently exceeds by {diff:,.2f} NAD)",
            pathway="Future Circumstance Review or Official Allowable Deductions",
            suggestion=(
                f"If your family's financial situation changes in a future semester (e.g., changes in primary breadwinner "
                f"employment or additional dependents enrolling in tertiary education), or if the sponsor allows formal deductions "
                f"(such as medical expenses or dependents) that bring verified net income below {max_income:,.2f} NAD, you could qualify. "
                "Do not alter declared figures without valid documentation."
            ),
        )
        return RuleOutcome(
            False,
            f"Household income ({student.household_income:,.2f} NAD) exceeds the maximum limit ({max_income:,.2f} NAD) by {diff:,.2f} NAD.",
            change,
        )
