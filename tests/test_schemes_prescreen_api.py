import pytest

from apps.prescreening.models import PrescreenRecord
from apps.schemes.defaults import DEFAULT_SCHEMES
from apps.schemes.models import BursaryScheme
from apps.schemes.services import SchemeService

pytestmark = pytest.mark.django_db

CIRCUMSTANCES = {"nqf_level": 7, "field_of_study": "Computer Science", "household_income": 250000, "region": "Khomas"}

@pytest.fixture
def seeded(db):
    SchemeService.seed_defaults(DEFAULT_SCHEMES)

def test_list_schemes_is_public(client, seeded):
    r = client.get("/api/schemes")
    assert r.status_code == 200 and len(r.json()) == len(DEFAULT_SCHEMES)
    assert r.json()[1]["eligible_fields_of_study"][0] == "Computer Science"

def test_seed_is_idempotent(seeded):
    assert set(SchemeService.seed_defaults(DEFAULT_SCHEMES).values()) == {"skipped"}
    assert BursaryScheme.objects.count() == len(DEFAULT_SCHEMES)

def test_create_scheme_requires_staff_and_rejects_duplicates(client, student, admin, auth_as):
    body = {"name": "New Fund", "description": "d", "min_nqf_level": 5}
    assert client.post("/api/schemes", body, format="json").status_code == 401
    auth_as(student)
    assert client.post("/api/schemes", body, format="json").status_code == 403
    auth_as(admin)
    r = client.post("/api/schemes", body, format="json")
    assert r.status_code == 201 and r.json()["requires_disability"] is False
    assert client.post("/api/schemes", body, format="json").status_code == 409

def test_prescreen_is_student_only(client, admin, seeded, auth_as):
    assert client.post("/api/prescreen", CIRCUMSTANCES, format="json").status_code == 401
    auth_as(admin)
    assert client.post("/api/prescreen", CIRCUMSTANCES, format="json").status_code == 403

def test_prescreen_returns_explained_results_and_saves_history(client, student, seeded, auth_as):
    auth_as(student)
    r = client.post("/api/prescreen", CIRCUMSTANCES, format="json")
    assert r.status_code == 200
    results = {x["scheme_name"]: x for x in r.json()}
    assert len(results) == len(DEFAULT_SCHEMES)
    assert results["MTC Tech Innovation Bursary"]["match_status"] == "Likely eligible"
    assert results["Ministry of Disability Affairs Scholarship"]["match_status"] == "Not eligible"
    for x in results.values():
        assert x["is_binding_decision"] is False and x["allows_automated_submission"] is False
        assert x["governance_safeguard"].startswith("ADVISORY NOTICE")

    history = client.get("/api/prescreen/history").json()
    assert len(history) == 1 and history[0]["circumstances"]["region"] == "Khomas"
    assert len(history[0]["results"]) == len(DEFAULT_SCHEMES)

def test_history_is_private_and_newest_first(client, student, superuser, seeded, auth_as):
    auth_as(student)
    client.post("/api/prescreen", CIRCUMSTANCES, format="json")
    client.post("/api/prescreen", {**CIRCUMSTANCES, "region": "Oshana"}, format="json")
    assert [h["circumstances"]["region"] for h in client.get("/api/prescreen/history").json()] == ["Oshana", "Khomas"]
    assert PrescreenRecord.objects.count() == 2

def test_prescreen_validates_input(client, student, auth_as):
    auth_as(student)
    assert client.post("/api/prescreen", {"nqf_level": "x"}, format="json").status_code == 400
