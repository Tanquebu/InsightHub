from pathlib import Path

import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.db.models.dataset_profile import DatasetProfile

log = structlog.get_logger(__name__)


class DatasetFileMissing(Exception):
    """Raised when a dataset has no file_path to profile, or the file cannot be read."""


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Compute basic profiling metrics for a pandas DataFrame."""
    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "column_missing_counts": {col: int(df[col].isna().sum()) for col in df.columns},
        "column_dtypes": {col: str(df[col].dtype) for col in df.columns},
    }


def _read_dataset_file(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise DatasetFileMissing(f"File not found: {file_path}")
    return pd.read_csv(path)


def profile_dataset(db: Session, dataset: Dataset) -> DatasetProfile:
    """Read a dataset's backing file, compute profiling metrics and persist them.

    Raises DatasetFileMissing if the dataset has no file_path or the file is unreadable.
    Overwrites any previously persisted profile for the same dataset.
    """
    if not dataset.file_path:
        raise DatasetFileMissing(f"Dataset {dataset.id} has no file_path")

    df = _read_dataset_file(dataset.file_path)
    metrics = profile_dataframe(df)

    profile = db.scalars(
        select(DatasetProfile).where(DatasetProfile.dataset_id == dataset.id)
    ).one_or_none()
    if profile is None:
        profile = DatasetProfile(dataset_id=dataset.id)
        db.add(profile)

    profile.row_count = metrics["row_count"]
    profile.column_count = metrics["column_count"]
    profile.column_missing_counts = metrics["column_missing_counts"]
    profile.column_dtypes = metrics["column_dtypes"]

    db.commit()
    db.refresh(profile)
    log.info(
        "dataset.profile.persisted",
        dataset_id=dataset.id,
        row_count=profile.row_count,
        column_count=profile.column_count,
    )
    return profile


def get_dataset_profile(db: Session, dataset_id: int) -> DatasetProfile | None:
    return db.scalars(
        select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)
    ).one_or_none()
