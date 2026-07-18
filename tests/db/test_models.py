"""DB-layer tests: constraints, defaults, and cascade behavior of the ORM models.

Uses its own SQLite engine (rather than the shared one in conftest.py) with
foreign-key enforcement turned on, since SQLite ignores FKs by default and the
rest of the suite doesn't need that enforcement. This exercises the same
`ondelete="CASCADE"` semantics the real Postgres schema relies on.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.models.dataset import Dataset
from app.db.models.dataset_profile import DatasetProfile
from app.db.models.dataset_quality_issue import DatasetQualityIssue
from app.db.models.project import Project
from app.db.models.user import User

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_Session = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def _reset_schema():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def session():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def test_project_name_unique_constraint(session):
    session.add(Project(name="Alpha"))
    session.commit()

    session.add(Project(name="Alpha"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_email_unique_constraint(session):
    session.add(User(email="a@example.com", password_hash=hash_password("secret")))
    session.commit()

    session.add(User(email="a@example.com", password_hash=hash_password("other")))
    with pytest.raises(IntegrityError):
        session.commit()


def test_dataset_defaults(session):
    project = Project(name="Alpha")
    session.add(project)
    session.commit()

    dataset = Dataset(project_id=project.id, name="orders.csv")
    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    assert dataset.status == "uploaded"
    assert dataset.source_type == "upload"
    assert dataset.file_path is None
    assert dataset.created_at is not None


def test_user_is_active_defaults_true(session):
    user = User(email="a@example.com", password_hash=hash_password("secret"))
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.is_active is True


def test_deleting_project_cascades_to_datasets(session):
    project = Project(name="Alpha")
    session.add(project)
    session.commit()

    dataset = Dataset(project_id=project.id, name="orders.csv")
    session.add(dataset)
    session.commit()
    dataset_id = dataset.id

    session.delete(project)
    session.commit()

    assert session.get(Dataset, dataset_id) is None


def test_deleting_dataset_cascades_to_profile_and_issues(session):
    project = Project(name="Alpha")
    session.add(project)
    session.commit()

    dataset = Dataset(project_id=project.id, name="orders.csv")
    session.add(dataset)
    session.commit()

    profile = DatasetProfile(
        dataset_id=dataset.id,
        row_count=10,
        column_count=2,
        column_missing_counts={"a": 0},
        column_dtypes={"a": "int64"},
    )
    issue = DatasetQualityIssue(
        dataset_id=dataset.id,
        rule_code="missing_values",
        severity="warning",
        message="too many nulls",
    )
    session.add_all([profile, issue])
    session.commit()
    profile_id, issue_id = profile.id, issue.id

    session.delete(dataset)
    session.commit()

    assert session.get(DatasetProfile, profile_id) is None
    assert session.get(DatasetQualityIssue, issue_id) is None


def test_dataset_profile_unique_per_dataset(session):
    project = Project(name="Alpha")
    session.add(project)
    session.commit()

    dataset = Dataset(project_id=project.id, name="orders.csv")
    session.add(dataset)
    session.commit()

    session.add(
        DatasetProfile(
            dataset_id=dataset.id,
            row_count=10,
            column_count=2,
            column_missing_counts={},
            column_dtypes={},
        )
    )
    session.commit()

    session.add(
        DatasetProfile(
            dataset_id=dataset.id,
            row_count=20,
            column_count=3,
            column_missing_counts={},
            column_dtypes={},
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
