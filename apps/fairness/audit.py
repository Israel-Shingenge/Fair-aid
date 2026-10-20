"""Runs the baseline-vs-mitigated fairness audit over a synthetic cohort."""
from dataclasses import dataclass
from typing import Any, Dict, List

from apps.prescreening.engine import LIKELY_ELIGIBLE, SchemeCriteria, StudentProfile, evaluate_scheme

from .benchmarks import get_default_schemes
from .demographics import generate_synthetic_applicants
from .metrics import compute_fairness_metrics
from .mitigations import evaluate_scheme_mitigated

def evaluate_applicant_recommendation(
    student: StudentProfile, schemes: List[SchemeCriteria], mitigated: bool = False
) -> bool:
    """True when at least one scheme comes back "Likely eligible"."""
    evaluate = evaluate_scheme_mitigated if mitigated else evaluate_scheme
    return any(evaluate(student, scheme).match_status == LIKELY_ELIGIBLE for scheme in schemes)

@dataclass
class GroupTally:
    """Approval counts for one side (privileged / unprivileged) of one grouping."""

    total: int = 0
    approved_baseline: int = 0
    approved_mitigated: int = 0

    def record(self, baseline: bool, mitigated: bool) -> None:
        self.total += 1
        self.approved_baseline += baseline
        self.approved_mitigated += mitigated

def _metrics(unprivileged: GroupTally, privileged: GroupTally, mitigated: bool) -> Dict[str, Any]:
    pick = (lambda t: t.approved_mitigated) if mitigated else (lambda t: t.approved_baseline)
    return compute_fairness_metrics(pick(unprivileged), unprivileged.total, pick(privileged), privileged.total)

def _group_report(
    grouping: str, unprivileged_label: str, privileged_label: str, unprivileged: GroupTally, privileged: GroupTally
) -> Dict[str, Any]:
    baseline = _metrics(unprivileged, privileged, mitigated=False)
    mitigated = _metrics(unprivileged, privileged, mitigated=True)
    return {
        "grouping": grouping,
        "unprivileged_group": unprivileged_label,
        "privileged_group": privileged_label,
        "baseline": baseline,
        "mitigated": mitigated,
        "improvement": {
            "dir_increase": round(mitigated["disparate_impact_ratio"] - baseline["disparate_impact_ratio"], 4),
            "spd_reduction": round(
                abs(baseline["statistical_parity_difference"]) - abs(mitigated["statistical_parity_difference"]), 4
            ),
            "resolved_adverse_impact": (not baseline["passes_80_percent_rule"]) and mitigated["passes_80_percent_rule"],
        },
    }

def run_fairness_audit(n_applicants: int = 300, seed: int = 42) -> Dict[str, Any]:
    applicants = generate_synthetic_applicants(n=n_applicants, seed=seed)
    schemes = get_default_schemes()

    rural, urban = GroupTally(), GroupTally()
    disabled, nondisabled = GroupTally(), GroupTally()

    for applicant in applicants:
        student: StudentProfile = applicant["circumstances"]
        baseline = evaluate_applicant_recommendation(student, schemes, mitigated=False)
        mitigated = evaluate_applicant_recommendation(student, schemes, mitigated=True)

        (rural if applicant["is_rural"] else urban).record(baseline, mitigated)
        (disabled if student.has_disability else nondisabled).record(baseline, mitigated)

    return {
        "metadata": {
            "sample_size": n_applicants,
            "metrics_used": [
                "Disparate Impact Ratio (DIR) with 80% rule evaluation",
                "Statistical Parity Difference (SPD) / Demographic Parity Difference",
            ],
            "mitigation_strategy": "In-Processing Fairness Intervention: Affirmative Regional Outreach & Disability Access Bridge",
        },
        "group_1_region": _group_report(
            "Region (Rural vs Urban)", "Rural / Peripheral Regions", "Urban / Central Hubs", rural, urban
        ),
        "group_2_disability": _group_report(
            "Disability Status (Disabled vs Non-Disabled)",
            "Applicants with disabilities",
            "Non-disabled applicants",
            disabled,
            nondisabled,
        ),
    }
