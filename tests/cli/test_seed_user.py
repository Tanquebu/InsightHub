import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cli.seed_user import seed_user
from app.core.security import verify_password
from app.db.base import Base

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SeedSessionLocal = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def _reset_schema():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _use_test_db(monkeypatch):
    monkeypatch.setattr("app.cli.seed_user.SessionLocal", _SeedSessionLocal)


def test_seed_user_creates_new_user(monkeypatch):
    _use_test_db(monkeypatch)

    user = seed_user("alice@insighthub.dev", "a-secure-password")

    assert user.id is not None
    assert user.email == "alice@insighthub.dev"
    assert user.is_active is True
    assert verify_password("a-secure-password", user.password_hash)


def test_seed_user_creates_inactive_user(monkeypatch):
    _use_test_db(monkeypatch)

    user = seed_user("bob@insighthub.dev", "a-secure-password", is_active=False)

    assert user.is_active is False


def test_seed_user_updates_existing_user_password(monkeypatch):
    _use_test_db(monkeypatch)

    created = seed_user("alice@insighthub.dev", "first-password")
    updated = seed_user("alice@insighthub.dev", "second-password")

    assert updated.id == created.id
    assert verify_password("second-password", updated.password_hash)
    assert not verify_password("first-password", updated.password_hash)
