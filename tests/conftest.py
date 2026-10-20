from urllib.parse import urlencode
import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRole

def form_login(client, email, password="password123"):
    """The login endpoint is the OAuth2 password flow: form-encoded body, email in `username`."""
    return client.post(
        "/api/auth/login",
        urlencode({"username": email, "password": password}),
        content_type="application/x-www-form-urlencoded",
    )

@pytest.fixture
def client():
    return APIClient()

def _make(email, role):
    return User.objects.create_user(email=email, full_name=email.split("@")[0], password="password123", role=role)

@pytest.fixture
def student(db):
    return _make("student@example.com", UserRole.STUDENT)

@pytest.fixture
def admin(db):
    return _make("admin@example.com", UserRole.ADMIN)

@pytest.fixture
def superuser(db):
    return _make("root@example.com", UserRole.SUPERUSER)

@pytest.fixture
def login(client):
    def _login(email, password="password123"):
        response = form_login(client, email, password)
        assert response.status_code == 200, response.content
        return response.json()

    return _login

@pytest.fixture
def auth_as(client, login):
    def _auth(user):
        tokens = login(user.email)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        return tokens

    return _auth
