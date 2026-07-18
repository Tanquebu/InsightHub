import structlog
from celery import Task
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.dataset import Dataset
from app.db.session import SessionLocal
from app.services.profiling import profile_dataset
from app.workers.celery_app import celery_app

log = structlog.get_logger(__name__)


def perform_ingestion(dataset: Dataset, db: Session) -> None:
    """Run the ingestion step.

    Milestone 2 establishes asynchronous orchestration. Milestone 3 adds profiling:
    when the dataset has a `file_path`, read it with pandas and persist row/column
    counts, missing-value counts and dtypes as a DatasetProfile. Datasets without a
    file_path are logged and skipped — that's an acceptable no-op for now. A
    file_path that points to a file that can't be read is a genuine ingestion
    failure and is left to the normal retry/failure handling below.
    """
    log.info(
        "dataset.ingestion.executed",
        dataset_id=dataset.id,
        source_type=dataset.source_type,
    )

    if not dataset.file_path:
        log.info("dataset.profiling.skipped_no_file_path", dataset_id=dataset.id)
        return

    profile_dataset(db, dataset)


def _set_status(db: Session, dataset: Dataset, status: str) -> None:
    dataset.status = status
    db.commit()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingest_dataset",
    max_retries=settings.ingestion_max_retries,
)
def ingest_dataset(self: Task, dataset_id: int) -> dict[str, int | str]:
    """Ingest a dataset and persist its processing state."""
    db = SessionLocal()
    try:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            log.warning("dataset.ingestion.not_found", dataset_id=dataset_id)
            return {"dataset_id": dataset_id, "status": "not_found"}

        _set_status(db, dataset, "processing")
        log.info("dataset.ingestion.started", dataset_id=dataset_id)

        try:
            perform_ingestion(dataset, db)
        except Exception as exc:
            db.rollback()
            # Refresh after rollback so that status handling always uses a valid ORM object.
            dataset = db.get(Dataset, dataset_id)
            if dataset is None:
                raise

            retries = int(getattr(self.request, "retries", 0))
            if retries >= self.max_retries:
                _set_status(db, dataset, "failed")
                log.exception(
                    "dataset.ingestion.failed",
                    dataset_id=dataset_id,
                    retries=retries,
                )
                raise

            _set_status(db, dataset, "pending")
            log.warning(
                "dataset.ingestion.retrying",
                dataset_id=dataset_id,
                retry=retries + 1,
                error=str(exc),
            )
            raise self.retry(
                exc=exc,
                countdown=settings.ingestion_retry_delay_seconds,
            )

        _set_status(db, dataset, "completed")
        log.info("dataset.ingestion.completed", dataset_id=dataset_id)
        return {"dataset_id": dataset_id, "status": "completed"}
    finally:
        db.close()
