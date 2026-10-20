"""
Regression guard for the FastAPI -> Django port: the refactored engine, mitigations and fairness
audit must reproduce the output of the original FastAPI code (captured in tests/golden) exactly.
"""
import dataclasses
import json
from pathlib import Path

import pytest

from apps.fairness.audit import run_fairness_audit
from apps.fairness.benchmarks import get_default_schemes
from apps.fairness.mitigations import evaluate_scheme_mitigated
from apps.prescreening.engine import StudentProfile, evaluate_scheme

SNAPSHOT = json.loads((Path(__file__).parent / "golden" / "old_fastapi_snapshot.json").read_text())

def _plain(result):
    return json.loads(json.dumps(dataclasses.asdict(result)))

@pytest.mark.parametrize("case", SNAPSHOT["cases"], ids=lambda c: str(c["student"]["nqf_level"]) + c["student"]["region"])
def test_engine_and_mitigations_match_original(case):
    student = StudentProfile(**case["student"])
    for scheme, base, mit in zip(get_default_schemes(), case["base"], case["mit"]):
        assert _plain(evaluate_scheme(student, scheme)) == base
        assert _plain(evaluate_scheme_mitigated(student, scheme)) == mit

def test_fairness_audit_matches_original():
    assert json.loads(json.dumps(run_fairness_audit(300, 42))) == SNAPSHOT["audit"]
