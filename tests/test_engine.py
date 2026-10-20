from apps.prescreening.engine import (
    LIKELY_ELIGIBLE, NOT_ELIGIBLE, POSSIBLY_ELIGIBLE, SchemeCriteria, StudentProfile, evaluate_scheme,
)

SCHEME = SchemeCriteria(
    name="Test Tech Bursary", description="For tech students", min_nqf_level=6, max_household_income=300000.0,
    eligible_fields_of_study=("Computer Science", "IT"), eligible_regions=("Khomas", "Erongo"),
)

def student(**over):
    base = dict(nqf_level=7, field_of_study="Computer Science", household_income=250000.0, region="Khomas")
    return StudentProfile(**{**base, **over})

def test_perfect_match_is_likely_eligible():
    r = evaluate_scheme(student(), SCHEME)
    assert (r.match_status, r.match_score) == (LIKELY_ELIGIBLE, 100.0)
    assert r.factors_that_hurt == [] and r.what_would_change_this == []

def test_one_soft_failure_is_possibly_eligible():
    r = evaluate_scheme(student(nqf_level=5), SCHEME)
    assert r.match_status == POSSIBLY_ELIGIBLE
    assert [c.criterion for c in r.what_would_change_this] == ["Minimum NQF Level"]

def test_two_soft_failures_are_not_eligible_and_all_rules_still_reported():
    r = evaluate_scheme(student(nqf_level=5, field_of_study="Agriculture", household_income=400000.0, region="Oshana"), SCHEME)
    assert r.match_status == NOT_ELIGIBLE
    assert len(r.decision_path) == 4 and len(r.actionable_feedback) == 4

def test_hard_gate_failure_stops_evaluation_with_zero_score():
    scheme = SchemeCriteria(name="Disability", requires_disability=True, max_household_income=400000.0)
    r = evaluate_scheme(student(has_disability=False), scheme)
    assert r.match_status == NOT_ELIGIBLE and r.match_score == 0.0
    assert len(r.decision_path) == 1

def test_scheme_without_criteria_is_likely_eligible():
    r = evaluate_scheme(student(), SchemeCriteria(name="Open"))
    assert r.match_status == LIKELY_ELIGIBLE and r.match_score == 100.0

def test_matching_is_case_and_whitespace_insensitive():
    assert evaluate_scheme(student(region=" khomas ", field_of_study="computer science"), SCHEME).match_status == LIKELY_ELIGIBLE
