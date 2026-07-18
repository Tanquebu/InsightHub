import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password
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


def test_protected_route_with_invalid_token_returns_401(
    unauthenticated_client: TestClient,
):
    response = unauthenticated_client.get(
        "/api/v1/projects", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_protected_route_with_valid_token_returns_200(client: TestClient):
    response = client.get("/api/v1/projects")
    assert response.status_code == 200


def test_login_inactive_user_returns_401(
    unauthenticated_client: TestClient, db_session
):
    user = User(
        email="inactive@insighthub.dev",
        password_hash=hash_password("some-password"),
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": "inactive@insighthub.dev", "password": "some-password"},
    )
    assert response.status_code == 401


def test_protected_route_with_token_missing_subject_returns_401(
    unauthenticated_client: TestClient,
):
    token = jwt.encode(
        {"foo": "bar"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    response = unauthenticated_client.get(
        "/api/v1/projects", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_protected_route_with_token_for_unknown_user_returns_401(
    unauthenticated_client: TestClient,
):
    token = create_access_token(subject="ghost@insighthub.dev")
    response = unauthenticated_client.get(
        "/api/v1/projects", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
