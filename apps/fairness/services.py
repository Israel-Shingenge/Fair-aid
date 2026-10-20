from typing import Any, Dict
from .audit import run_fairness_audit

class FairnessService:
    @staticmethod
    def audit_demographic_fairness(n_applicants: int = 300, seed: int = 42) -> Dict[str, Any]:
        return run_fairness_audit(n_applicants=n_applicants, seed=seed)
