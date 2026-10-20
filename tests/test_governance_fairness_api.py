import pytest

pytestmark = pytest.mark.django_db

def test_root_and_safeguards_are_public(client):
    assert client.get("/").json()["is_binding_decision"] is False
    body = client.get("/api/governance/safeguards").json()
    assert body["allows_automated_submission"] is False and len(body["student_submission_checklist"]) == 5

@pytest.mark.parametrize("path", ["/api/applications/submit", "/api/decisions/award"])
def test_automated_actions_are_always_403(client, path):
    r = client.post(path)
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "Automated Action Prohibited"

def test_fairness_audit_is_staff_only_and_validates_params(client, student, admin, auth_as):
    assert client.get("/api/fairness/audit").status_code == 401
    auth_as(student)
    assert client.get("/api/fairness/audit").status_code == 403
    auth_as(admin)
    r = client.get("/api/fairness/audit?n_applicants=100&seed=1")
    assert r.status_code == 200 and r.json()["metadata"]["sample_size"] == 100
    assert client.get("/api/fairness/audit?n_applicants=10").status_code == 400
    assert client.get("/api/fairness/audit?n_applicants=abc").status_code == 400

def test_openapi_schema_generates(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200 and "/api/prescreen" in r.content.decode()
