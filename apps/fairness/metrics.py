from typing import Any, Dict

def compute_fairness_metrics(
    unprivileged_approved: int,
    unprivileged_total: int,
    privileged_approved: int,
    privileged_total: int,
) -> Dict[str, Any]:
    """
    * Disparate Impact Ratio (DIR) = rate_unprivileged / rate_privileged
    * Statistical Parity Difference (SPD) = rate_unprivileged - rate_privileged
    """
    unprivileged_rate = unprivileged_approved / unprivileged_total if unprivileged_total > 0 else 0.0
    privileged_rate = privileged_approved / privileged_total if privileged_total > 0 else 0.0

    if privileged_rate > 0:
        dir_value = round(unprivileged_rate / privileged_rate, 4)
    else:
        dir_value = 1.0 if unprivileged_rate == 0 else float("inf")

    spd_value = round(unprivileged_rate - privileged_rate, 4)

    # Parity gap check (acceptable if -0.10 <= SPD <= 0.10)
    if abs(spd_value) <= 0.10:
        parity_status = "Acceptable Parity"
    elif spd_value < -0.10:
        parity_status = "Adverse Disparity"
    else:
        parity_status = "Favorable Disparity"

    return {
        "unprivileged_rate": round(unprivileged_rate * 100, 2),
        "privileged_rate": round(privileged_rate * 100, 2),
        "disparate_impact_ratio": dir_value,
        "passes_80_percent_rule": dir_value >= 0.80,
        "statistical_parity_difference": spd_value,
        "parity_status": parity_status,
        "unprivileged_count": unprivileged_total,
        "privileged_count": privileged_total,
    }
