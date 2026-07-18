import os

# The rate limiter's storage backend is read from settings at import time (see
# app/core/rate_limit.py), so this must be set before `app.main` (and therefore
# app.core.config) is imported. Tests use the `limits` in-memory backend instead
# of real Redis: it exercises the exact same slowapi wiring as production without
# depending on a live Redis instance or leaking rate-limit state across test runs.
os.environ.setdefault("REDIS_URL", "memory://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models.user import User
from app.main import app

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine)

TEST_USER_EMAIL = "test.user@insighthub.dev"
TEST_USER_PASSWORD = "a-very-secure-password"


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    # Each test gets a fresh rate-limit budget so per-test request volume can
    # never trip a limit that was consumed by a previous, unrelated test.
    limiter.reset()
    yield


@pytest.fixture
def test_user(db_session) -> User:
    user = User(email=TEST_USER_EMAIL, password_hash=hash_password(TEST_USER_PASSWORD))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unauthenticated_client():
    """A TestClient with no Authorization header, for auth/rate-limit edge cases."""

    def override_get_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client(auth_headers):
    """A TestClient pre-authenticated as `test_user`.

    Milestone 5 protects every `/api/v1/projects` and `/api/v1/datasets` route
    behind JWT auth, so the shared `client` fixture carries a valid bearer
    token by default — this keeps the existing project/dataset/profile/insights
    tests unchanged. Use `unauthenticated_client` for auth-specific tests.
    """

    def override_get_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers=auth_headers) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """A session bound to the same in-memory engine used by the `client` fixture.

    Useful for tests that need to set up or inspect rows (e.g. persisting a
    DatasetProfile directly) without exercising the full ingestion pipeline.
    """
    db = _Session()
    try:
        yield db
    finally:
        db.close()
