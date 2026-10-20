"""Eligibility rules. Add a new criterion by creating a module here and registering it below."""
from .base import EligibilityRule
from .disability import DisabilityRequirementRule
from .field_of_study import FieldOfStudyRule
from .income import HouseholdIncomeRule
from .nqf import MinimumNQFLevelRule
from .region import RegionalEligibilityRule

# Order matters: it is the order of the tree's levels and of the decision-path steps.
DEFAULT_RULES: list[EligibilityRule] = [
    DisabilityRequirementRule(),
    HouseholdIncomeRule(),
    MinimumNQFLevelRule(),
    FieldOfStudyRule(),
    RegionalEligibilityRule(),
]

__all__ = [
    "EligibilityRule",
    "DisabilityRequirementRule",
    "HouseholdIncomeRule",
    "MinimumNQFLevelRule",
    "FieldOfStudyRule",
    "RegionalEligibilityRule",
    "DEFAULT_RULES",
]
