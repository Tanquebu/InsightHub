import pytest
from celery.exceptions import Retry
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.dataset import Dataset
from app.db.models.dataset_profile import DatasetProfile
from app.db.models.dataset_quality_issue import DatasetQualityIssue
from app.db.models.project import Project
from app.services.quality import RULE_HIGH_MISSING_COLUMN
from app.workers import tasks


@pytest.fixture
def worker_db(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with session_factory() as db:
        project = Project(name="Worker tests")
        db.add(project)
        db.flush()
        dataset = Dataset(
            project_id=project.id,
            name="input.csv",
            status="pending",
        )
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id

    monkeypatch.setattr(tasks, "SessionLocal", session_factory)
    yield session_factory, dataset_id
    Base.metadata.drop_all(engine)
    engine.dispose()


def _status(session_factory: sessionmaker, dataset_id: int) -> str:
    with session_factory() as db:
        dataset = db.get(Dataset, dataset_id)
        assert dataset is not None
        return dataset.status


def test_ingestion_transitions_from_processing_to_completed(
    worker_db, monkeypatch: pytest.MonkeyPatch
):
    session_factory, dataset_id = worker_db
    observed_statuses: list[str] = []

    def observe_processing(_dataset: Dataset, _db: Session) -> None:
        observed_statuses.append(_status(session_factory, dataset_id))

    monkeypatch.setattr(tasks, "perform_ingestion", observe_processing)

    result = tasks.ingest_dataset.run(dataset_id)

    assert observed_statuses == ["processing"]
    assert result == {"dataset_id": dataset_id, "status": "completed"}
    assert _status(session_factory, dataset_id) == "completed"


def test_ingestion_failure_is_left_pending_for_retry(
    worker_db, monkeypatch: pytest.MonkeyPatch
):
    session_factory, dataset_id = worker_db
    retry_calls: list[dict] = []

    def fail(_dataset: Dataset, _db: Session) -> None:
        raise OSError("temporary source error")

    def retry(**kwargs):
        retry_calls.append(kwargs)
        raise Retry("scheduled retry")

    monkeypatch.setattr(tasks, "perform_ingestion", fail)
    monkeypatch.setattr(tasks.ingest_dataset, "retry", retry)

    with pytest.raises(Retry):
        tasks.ingest_dataset.run(dataset_id)

    assert _status(session_factory, dataset_id) == "pending"
    assert retry_calls[0]["countdown"] == tasks.settings.ingestion_retry_delay_seconds
    assert isinstance(retry_calls[0]["exc"], OSError)


def test_ingestion_is_marked_failed_after_last_retry(
    worker_db, monkeypatch: pytest.MonkeyPatch
):
    session_factory, dataset_id = worker_db

    def fail(_dataset: Dataset, _db: Session) -> None:
        raise ValueError("invalid input")

    monkeypatch.setattr(tasks, "perform_ingestion", fail)
    tasks.ingest_dataset.push_request(retries=tasks.ingest_dataset.max_retries)
    try:
        with pytest.raises(ValueError, match="invalid input"):
            tasks.ingest_dataset.run(dataset_id)
    finally:
        tasks.ingest_dataset.pop_request()

    assert _status(session_factory, dataset_id) == "failed"


def test_ingestion_of_missing_dataset_is_a_noop(worker_db):
    session_factory, _dataset_id = worker_db

    result = tasks.ingest_dataset.run(999_999)

    assert result == {"dataset_id": 999_999, "status": "not_found"}
    with session_factory() as db:
        assert db.get(Dataset, 999_999) is None


@pytest.fixture
def worker_db_with_csv(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Like `worker_db`, but the dataset points at a real CSV file on disk and
    `perform_ingestion` is left untouched, so profiling actually runs."""
    csv_path = tmp_path / "input.csv"
    csv_path.write_text("id,name,score\n1,Alice,1.5\n2,Bob,\n3,Carol,3.2\n")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with session_factory() as db:
        project = Project(name="Worker profiling tests")
        db.add(project)
        db.flush()
        dataset = Dataset(
            project_id=project.id,
            name="input.csv",
            status="pending",
            file_path=str(csv_path),
        )
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id

    monkeypatch.setattr(tasks, "SessionLocal", session_factory)
    yield session_factory, dataset_id
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_ingest_dataset_persists_profile_end_to_end(worker_db_with_csv):
    session_factory, dataset_id = worker_db_with_csv

    result = tasks.ingest_dataset.run(dataset_id)

    assert result == {"dataset_id": dataset_id, "status": "completed"}
    with session_factory() as db:
        profile = db.scalars(
            select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)
        ).one()
        assert profile.row_count == 3
        assert profile.column_count == 3
        assert profile.column_missing_counts == {"id": 0, "name": 0, "score": 1}
        assert profile.column_dtypes["id"] == "int64"


def test_ingest_dataset_without_file_path_skips_profiling(worker_db):
    session_factory, dataset_id = worker_db

    result = tasks.ingest_dataset.run(dataset_id)

    assert result == {"dataset_id": dataset_id, "status": "completed"}
    with session_factory() as db:
        profile = db.scalars(
            select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)
        ).one_or_none()
        assert profile is None


def test_ingest_dataset_persists_quality_issues_end_to_end(worker_db_with_csv):
    """The CSV fixture has 1/3 missing values in the "score" column (33%), which
    exceeds the default quality_missing_warning_threshold (20%) but not the
    critical one (50%), so a single warning-level issue should be persisted."""
    session_factory, dataset_id = worker_db_with_csv

    result = tasks.ingest_dataset.run(dataset_id)

    assert result == {"dataset_id": dataset_id, "status": "completed"}
    with session_factory() as db:
        issues = db.scalars(
            select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset_id)
        ).all()
        assert len(issues) == 1
        assert issues[0].rule_code == RULE_HIGH_MISSING_COLUMN
        assert issues[0].severity == "warning"
        assert "score" in issues[0].message


def test_ingest_dataset_without_file_path_produces_no_quality_issues(worker_db):
    session_factory, dataset_id = worker_db

    tasks.ingest_dataset.run(dataset_id)

    with session_factory() as db:
        issues = db.scalars(
            select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset_id)
        ).all()
        assert issues == []


def test_ingest_dataset_overwrites_quality_issues_on_rerun(tmp_path, monkeypatch):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text("id,name\n1,Alice\n2,\n3,\n4,\n")  # 3/4 missing -> critical

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with session_factory() as db:
        project = Project(name="Requery tests")
        db.add(project)
        db.flush()
        dataset = Dataset(
            project_id=project.id,
            name="input.csv",
            status="pending",
            file_path=str(csv_path),
        )
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id

    monkeypatch.setattr(tasks, "SessionLocal", session_factory)

    tasks.ingest_dataset.run(dataset_id)
    with session_factory() as db:
        first_run_issues = db.scalars(
            select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset_id)
        ).all()
        # 3/4 missing trips both HIGH_MISSING_COLUMN (critical) and, since it
        # also drags completeness to 0.625, LOW_COMPLETENESS_SCORE (warning).
        assert len(first_run_issues) == 2
        severities = {issue.severity for issue in first_run_issues}
        assert "critical" in severities

        dataset = db.get(Dataset, dataset_id)
        dataset.status = "pending"
        db.commit()

    # Overwrite the CSV so the column is now clean and no issues should remain.
    csv_path.write_text("id,name\n1,Alice\n2,Bob\n")
    tasks.ingest_dataset.run(dataset_id)

    with session_factory() as db:
        second_run_issues = db.scalars(
            select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset_id)
        ).all()
        assert second_run_issues == []

    Base.metadata.drop_all(engine)
    engine.dispose()
