import pytest

pytestmark = pytest.mark.django_db

def test_user_management_is_superuser_only(client, student, admin, superuser, auth_as):
    assert client.get("/api/users").status_code == 401
    auth_as(student)
    assert client.get("/api/users").status_code == 403
    auth_as(admin)
    assert client.get("/api/users").status_code == 403
    auth_as(superuser)
    assert len(client.get("/api/users").json()) == 3
    assert [u["role"] for u in client.get("/api/users?role=admin").json()] == ["admin"]

def test_superuser_can_create_admin_and_change_roles(client, superuser, student, auth_as):
    auth_as(superuser)
    r = client.post("/api/users", {"email": "adm@x.com", "full_name": "Adm", "password": "password123"}, format="json")
    assert r.status_code == 201 and r.json()["role"] == "admin"
    r = client.patch(f"/api/users/{student.pk}/role", {"role": "admin"}, format="json")
    assert r.status_code == 200 and r.json()["role"] == "admin"
    assert client.patch(f"/api/users/{student.pk}/role", {"role": "wizard"}, format="json").status_code == 400
    assert client.get("/api/users/99999").status_code == 404

def test_superuser_cannot_demote_or_deactivate_self(client, superuser, auth_as):
    auth_as(superuser)
    assert client.patch(f"/api/users/{superuser.pk}/role", {"role": "student"}, format="json").status_code == 403
    assert client.patch(f"/api/users/{superuser.pk}/status", {"is_active": False}, format="json").status_code == 403
