import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset

log = structlog.get_logger(__name__)


def create_dataset(db: Session, project_id: int, name: str, source_type: str) -> Dataset:
    dataset = Dataset(project_id=project_id, name=name, source_type=source_type)
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
) -> Dataset:
    if name is not None:
        dataset.name = name
    if status is not None:
        dataset.status = status
    if source_type is not None:
        dataset.source_type = source_type
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset: Dataset) -> None:
    log.info("dataset.deleted", dataset_id=dataset.id, project_id=dataset.project_id)
    db.delete(dataset)
    db.commit()
