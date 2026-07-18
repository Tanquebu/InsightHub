import pytest
from celery.exceptions import Retry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.dataset import Dataset
from app.db.models.project import Project
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

    def observe_processing(_dataset: Dataset) -> None:
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

    def fail(_dataset: Dataset) -> None:
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

    def fail(_dataset: Dataset) -> None:
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
