from django.core.management.base import BaseCommand

from apps.fairness.audit import run_fairness_audit

RULE = "-" * 78
BOLD_RULE = "=" * 78


def _pct_delta(after: float, before: float) -> str:
    return f"{after - before:+.2f}%"


def format_group(report: dict) -> str:
    b, m, imp = report["baseline"], report["mitigated"], report["improvement"]
    dir_before = "PASS" if b["passes_80_percent_rule"] else "FAIL (Bias)"
    dir_after = "PASS (Fair)" if m["passes_80_percent_rule"] else "FAIL"
    lines = [
        f"\n[AUDIT] {report['grouping'].upper()}",
        f"  Unprivileged: {report['unprivileged_group']}",
        f"  Privileged:   {report['privileged_group']}",
        RULE,
        "  METRIC                            BASELINE           AFTER MITIGATION   IMPACT",
        RULE,
        f"  Unprivileged Approval Rate:      {b['unprivileged_rate']:>6.2f}%              {m['unprivileged_rate']:>6.2f}%       {_pct_delta(m['unprivileged_rate'], b['unprivileged_rate'])}",
        f"  Privileged Approval Rate:        {b['privileged_rate']:>6.2f}%              {m['privileged_rate']:>6.2f}%       {_pct_delta(m['privileged_rate'], b['privileged_rate'])}",
        f"  Disparate Impact Ratio (DIR):    {b['disparate_impact_ratio']:>6.4f}              {m['disparate_impact_ratio']:>6.4f}       {imp['dir_increase']:+.4f}",
        f"  DIR 80% Rule (Threshold >= 0.8): {dir_before:>11}           {dir_after:>11}      {'RESOLVED' if imp['resolved_adverse_impact'] else 'MAINTAINED'}",
        f"  Statistical Parity Diff (SPD):   {b['statistical_parity_difference']:>+6.4f}              {m['statistical_parity_difference']:>+6.4f}       Gap closed: {imp['spd_reduction']:.4f}",
        f"  Parity Assessment:               {b['parity_status']:>18}    {m['parity_status']:>18}",
    ]
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Print the algorithmic fairness audit report (DIR / SPD, baseline vs mitigated)."

    def add_arguments(self, parser):
        parser.add_argument("--applicants", type=int, default=300)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        audit = run_fairness_audit(n_applicants=options["applicants"], seed=options["seed"])
        out = self.stdout.write
        out(BOLD_RULE)
        out("      FAIRAID ALGORITHMIC FAIRNESS AUDIT REPORT")
        out(BOLD_RULE)
        out("Metrics:   1. Disparate Impact Ratio (DIR) [80% Rule / 0.8 Threshold]")
        out("           2. Statistical Parity Difference (SPD) [Parity = 0.0]")
        out(BOLD_RULE)
        out(format_group(audit["group_1_region"]))
        out(format_group(audit["group_2_disability"]))
        out("\n" + BOLD_RULE)
        out("MITIGATION: " + audit["metadata"]["mitigation_strategy"])
        out(BOLD_RULE)
