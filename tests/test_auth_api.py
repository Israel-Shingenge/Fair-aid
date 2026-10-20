import pytest
from tests.conftest import form_login
from apps.accounts.models import RefreshToken, User
pytestmark = pytest.mark.django_db

def bearer(client, token):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

def test_signup_creates_student_and_normalises_email(client):
    r = client.post("/api/auth/signup", {"email": " New@Example.COM ", "full_name": "New", "password": "password123"}, format="json")
    assert r.status_code == 201
    assert r.json()["email"] == "new@example.com" and r.json()["role"] == "student"
    assert "password" not in r.json()

def test_signup_duplicate_is_409_and_short_password_is_400(client, student):
    assert client.post("/api/auth/signup", {"email": student.email, "full_name": "x", "password": "password123"}, format="json").status_code == 409
    assert client.post("/api/auth/signup", {"email": "a@b.com", "full_name": "x", "password": "short"}, format="json").status_code == 400

def test_login_wrong_password_and_unknown_email_look_identical(client, student):
    a = form_login(client, student.email, "nope")
    b = form_login(client, "ghost@example.com", "nope")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {"detail": "Incorrect email or password"}
    assert a["WWW-Authenticate"] == "Bearer"

def test_me_requires_valid_token(client, student, auth_as):
    assert client.get("/api/auth/me").status_code == 401
    auth_as(student)
    assert client.get("/api/auth/me").json()["email"] == student.email

def test_refresh_rotates_and_reuse_revokes_session(client, student, login):
    first = login(student.email)
    second = client.post("/api/auth/refresh", {"refresh_token": first["refresh_token"]}, format="json")
    assert second.status_code == 200
    new = second.json()

    bearer(client, new["access_token"])
    assert client.get("/api/auth/me").status_code == 200

    replay = client.post("/api/auth/refresh", {"refresh_token": first["refresh_token"]}, format="json")
    assert replay.status_code == 401 and "reuse" in replay.json()["detail"]

    # the whole session (including the legitimately rotated tokens) is now dead
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/refresh", {"refresh_token": new["refresh_token"]}, format="json").status_code == 401


def test_logout_revokes_access_token_immediately(client, student, auth_as):
    auth_as(student)
    assert client.post("/api/auth/logout", {}, format="json").status_code == 200
    assert client.get("/api/auth/me").status_code == 401

def test_logout_without_credentials_is_400(client):
    assert client.post("/api/auth/logout", {}, format="json").status_code == 400

def test_logout_all_ends_every_session(client, student, login):
    one, two = login(student.email), login(student.email)
    bearer(client, one["access_token"])
    assert client.post("/api/auth/logout-all").status_code == 200
    bearer(client, two["access_token"])
    assert client.get("/api/auth/me").status_code == 401

def test_refresh_token_cannot_be_used_as_access_token(client, student, login):
    bearer(client, login(student.email)["refresh_token"])
    assert client.get("/api/auth/me").status_code == 401

def test_deactivated_user_loses_access(client, student, superuser, auth_as):
    from rest_framework.test import APIClient

    student_client = APIClient()
    token = form_login(student_client, student.email).json()["access_token"]
    student_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert student_client.get("/api/auth/me").status_code == 200

    auth_as(superuser)
    assert client.patch(f"/api/users/{student.pk}/status", {"is_active": False}, format="json").status_code == 200
    assert student_client.get("/api/auth/me").status_code == 401
    assert not RefreshToken.objects.filter(user=student, revoked_at__isnull=True).exists()
    assert form_login(client, student.email).status_code == 401
