import structlog
from celery.exceptions import CeleryError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.workers.tasks import ingest_dataset

log = structlog.get_logger(__name__)


class DatasetIngestionAlreadyStarted(Exception):
    pass


class DatasetIngestionDispatchError(Exception):
    pass


def create_dataset(
    db: Session,
    project_id: int,
    name: str,
    source_type: str,
    file_path: str | None = None,
) -> Dataset:
    dataset = Dataset(project_id=project_id, name=name, source_type=source_type, file_path=file_path)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    log.info("dataset.created", dataset_id=dataset.id, project_id=project_id, name=name)
    return dataset


def list_datasets(db: Session, project_id: int) -> list[Dataset]:
    return list(
        db.scalars(
            select(Dataset).where(Dataset.project_id == project_id).order_by(Dataset.id.desc())
        ).all()
    )


def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
    return db.get(Dataset, dataset_id)


def update_dataset(
    db: Session,
    dataset: Dataset,
    name: str | None,
    status: str | None,
    source_type: str | None,
    file_path: str | None = None,
) -> Dataset:
    if name is not None:
        dataset.name = name
    if status is not None:
        dataset.status = status
    if source_type is not None:
        dataset.source_type = source_type
    if file_path is not None:
        dataset.file_path = file_path
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset: Dataset) -> None:
    log.info("dataset.deleted", dataset_id=dataset.id, project_id=dataset.project_id)
    db.delete(dataset)
    db.commit()


def queue_ingestion(db: Session, dataset: Dataset) -> str:
    """Persist a pending job before publishing it to the Celery broker."""
    if dataset.status in {"pending", "processing", "completed"}:
        raise DatasetIngestionAlreadyStarted

    previous_status = dataset.status
    dataset.status = "pending"
    db.commit()

    try:
        result = ingest_dataset.delay(dataset.id)
    except (CeleryError, OSError) as exc:
        dataset.status = previous_status
        db.commit()
        log.exception("dataset.ingestion.dispatch_failed", dataset_id=dataset.id)
        raise DatasetIngestionDispatchError from exc

    log.info("dataset.ingestion.queued", dataset_id=dataset.id, task_id=result.id)
    return result.id
