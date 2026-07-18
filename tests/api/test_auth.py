from fastapi.testclient import TestClient

from app.db.models.user import User
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


def test_login_with_valid_credentials_returns_token(
    unauthenticated_client: TestClient, test_user: User
):
    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_invalid_password_returns_401(
    unauthenticated_client: TestClient, test_user: User
):
    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER_EMAIL, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_with_unknown_user_returns_401(unauthenticated_client: TestClient):
    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@insighthub.dev", "password": "whatever"},
    )
    assert response.status_code == 401


def test_protected_route_without_token_returns_401(unauthenticated_client: TestClient):
    response = unauthenticated_client.get("/api/v1/projects")
    assert response.status_code == 401


def test_protected_route_with_invalid_token_returns_401(unauthenticated_client: TestClient):
    response = unauthenticated_client.get(
        "/api/v1/projects", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_protected_route_with_valid_token_returns_200(client: TestClient):
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
