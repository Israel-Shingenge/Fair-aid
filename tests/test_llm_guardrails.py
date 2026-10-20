from apps.explanations.grounding.facts import facts_from_results, resolve_scheme
from apps.explanations.grounding.guardrails import validate_text
from apps.prescreening.engine import StudentProfile, evaluate_scheme
from apps.prescreening.adapters import scheme_to_criteria  # noqa: F401
from apps.fairness.benchmarks import get_default_schemes
import dataclasses, json

def facts_for(**student):
    profile = StudentProfile(**{"nqf_level": 6, "field_of_study": "Agriculture", "household_income": 250000.0,
                                "region": "Karas", "has_disability": False, **student})
    results = [json.loads(json.dumps(dataclasses.asdict(evaluate_scheme(profile, s)))) for s in get_default_schemes()]
    return facts_from_results(results)

FACTS = facts_for()
BY = {f.scheme_name: f for f in FACTS}
NOT = BY["MTC Tech Innovation Bursary"]            # Not eligible
LIKELY = BY["NSFAF Core Grant"]                    # Likely eligible

def ok(text, scope=None, q=""):
    return validate_text(text, FACTS, scope=scope, question=q).ok

def test_status_sanity():
    assert NOT.match_status == "Not eligible" and LIKELY.match_status == "Likely eligible"

def test_accepts_faithful_text():
    assert ok("The engine found you are not eligible for this scheme because your NQF level is below 7.", NOT)
    assert ok("You appear likely eligible for the NSFAF Core Grant, and your income is within the limit.", LIKELY)

def test_rejects_claiming_eligibility_when_engine_said_no():
    assert not ok("Good news, you are eligible for the MTC Tech Innovation Bursary!", NOT)
    assert not ok("You qualify for this bursary.", NOT)
    assert not ok("You are likely eligible for the MTC Tech Innovation Bursary.", NOT)

def test_negated_positive_phrases_are_fine():
    assert ok("You are not likely eligible for the MTC Tech Innovation Bursary right now.", NOT)
    assert ok("You do not qualify at the moment, but your NQF level could change that.", NOT)

def test_rejects_denying_a_likely_match():
    assert not ok("Unfortunately you are not eligible for the NSFAF Core Grant.", LIKELY)

def test_possibly_eligible_must_not_get_definite_verdict():
    possibly = next(f for f in facts_for(nqf_level=5) if f.match_status == "Possibly eligible")
    assert ok("One criterion is not met yet, so this is a close call.", possibly)
    assert not ok("You are eligible for this scheme.", possibly)
    assert not ok("You do not qualify for this scheme.", possibly)

def test_sentence_naming_another_scheme_is_checked_against_that_scheme():
    text = "You are likely eligible for the NSFAF Core Grant. You are eligible for the MTC Tech Innovation Bursary."
    assert not ok(text)  # unscoped: the second sentence contradicts MTC's 'Not eligible'
    assert ok("You are likely eligible for the NSFAF Core Grant. MTC Tech Innovation Bursary needs NQF level 7.")

def test_rejects_promises_links_and_misrepresentation():
    assert not ok("This bursary is guaranteed to fund you.", LIKELY)
    assert not ok("You will be awarded the NSFAF Core Grant.", LIKELY)
    assert not ok("Apply at https://nsfaf.example.com now.", LIKELY)
    assert not ok("You could pretend your income is lower.", NOT)

def test_rejects_numbers_not_in_the_facts():
    assert not ok("Your household income should be below 123,456 NAD.", NOT)
    assert ok("The income limit for NSFAF is 500,000.00 NAD, written 500 000 or 500000.", LIKELY)

def test_question_numbers_may_be_echoed():
    assert ok("I can't say what would happen with 90,000 NAD; please re-run the pre-screening.", NOT, q="what if my income was 90000?")
    assert not ok("With 90,000 NAD you would qualify.", NOT)  # also asserts eligibility

def test_empty_or_oversized_text_rejected():
    assert not ok("   ")
    assert not ok("x " * 700)

def test_resolve_scheme():
    assert resolve_scheme("why not MTC Tech Innovation Bursary?", None, FACTS).scheme_name == "MTC Tech Innovation Bursary"
    assert resolve_scheme("why wasn't I matched to namdeb?", None, FACTS).scheme_name == "Namdeb STEM Bursary"
    assert resolve_scheme("how do I apply?", None, FACTS) is None
    assert resolve_scheme("whatever", "nsfaf core grant", FACTS).scheme_name == "NSFAF Core Grant"
    assert resolve_scheme("whatever", "Nonexistent", FACTS) is None
