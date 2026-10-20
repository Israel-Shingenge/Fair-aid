"""
Mitigated matching (in-processing fairness intervention).

Each mitigation is a small function that inspects the baseline result and either returns a
``Promotion`` (upgrade to "Likely eligible" with a reason) or ``None``. The first one that applies wins.

1. Rural Foundational Access Bridge (NSFAF Core Grant only).
2. Regional Equity Outreach for region-restricted schemes.
3. Disability Inclusion Bridge for universal schemes (1 NQF level below threshold).
"""
from dataclasses import dataclass, replace
from typing import Callable, List, Optional

from apps.prescreening.engine import LIKELY_ELIGIBLE, SchemeCriteria, SchemeMatchResult, StudentProfile, evaluate_scheme

from .demographics import URBAN_REGIONS

@dataclass(frozen=True)
class Promotion:
    score: float
    helper: str
    explanation: str


Mitigation = Callable[[StudentProfile, SchemeCriteria], Optional[Promotion]]


def _meets_hard_criteria(student: StudentProfile, scheme: SchemeCriteria) -> bool:
    eligible_fields = [f.lower().strip() for f in scheme.eligible_fields_of_study or ()]
    field_ok = not eligible_fields or student.field_of_study.lower().strip() in eligible_fields
    income_ok = scheme.max_household_income is None or student.household_income <= scheme.max_household_income
    nqf_ok = scheme.min_nqf_level is None or student.nqf_level >= scheme.min_nqf_level
    return field_ok and income_ok and nqf_ok

def rural_access_bridge(student: StudentProfile, scheme: SchemeCriteria) -> Optional[Promotion]:
    is_rural = student.region not in URBAN_REGIONS
    if is_rural and scheme.name == "NSFAF Core Grant" and student.nqf_level >= 5 and student.household_income <= 180000.0:
        return Promotion(
            95.0,
            f"Affirmative Rural Equity Bridge: Rural resident from {student.region} eligible under National TVET/Access Quota.",
            f"You are likely eligible for the {scheme.name} via the Affirmative Rural Equity Bridge. "
            "Your household need and foundational enrollment qualify you under national affirmative action policy.",
        )
    return None

def regional_outreach(student: StudentProfile, scheme: SchemeCriteria) -> Optional[Promotion]:
    is_rural = student.region not in URBAN_REGIONS
    if (
        is_rural
        and scheme.eligible_regions
        and student.region not in scheme.eligible_regions
        and _meets_hard_criteria(student, scheme)
        and student.household_income <= 200000.0
    ):
        return Promotion(
            90.0,
            f"Affirmative Regional Outreach: Rural resident from {student.region} qualifies under outreach inclusion.",
            f"You are likely eligible for the {scheme.name} via Affirmative Regional Outreach quota for {student.region}.",
        )
    return None

def disability_bridge(student: StudentProfile, scheme: SchemeCriteria) -> Optional[Promotion]:
    if (
        student.has_disability
        and not scheme.requires_disability
        and scheme.min_nqf_level
        and student.nqf_level == scheme.min_nqf_level - 1
        and (scheme.max_household_income is None or student.household_income <= scheme.max_household_income)
    ):
        return Promotion(
            90.0,
            "Affirmative Disability Bridge: Full academic access accommodation granted.",
            f"You are likely eligible for the {scheme.name} under an Affirmative Disability Access Bridge.",
        )
    return None


DEFAULT_MITIGATIONS: List[Mitigation] = [rural_access_bridge, regional_outreach, disability_bridge]

def evaluate_scheme_mitigated(
    student: StudentProfile,
    scheme: SchemeCriteria,
    mitigations: Optional[List[Mitigation]] = None,
) -> SchemeMatchResult:
    baseline = evaluate_scheme(student, scheme)
    if baseline.match_status == LIKELY_ELIGIBLE:
        return baseline

    for mitigation in mitigations if mitigations is not None else DEFAULT_MITIGATIONS:
        promotion = mitigation(student, scheme)
        if promotion is not None:
            return replace(
                baseline,
                match_status=LIKELY_ELIGIBLE,
                match_score=promotion.score,
                plain_language_explanation=promotion.explanation,
                factors_that_helped=[*baseline.factors_that_helped, promotion.helper],
                factors_that_hurt=[],
                what_would_change_this=[],
                actionable_feedback=[],
            )
    return baseline
