import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.dataset import Dataset
from app.db.models.dataset_profile import DatasetProfile
from app.db.models.project import Project
from app.services.profiling import (
    DatasetFileMissing,
    get_dataset_profile,
    profile_dataframe,
    profile_dataset,
)


def test_profile_dataframe_computes_row_and_column_counts():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", None],
            "score": [1.5, None, 3.2],
        }
    )

    metrics = profile_dataframe(df)

    assert metrics["row_count"] == 3
    assert metrics["column_count"] == 3


def test_profile_dataframe_counts_missing_values_per_column():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", None, None],
            "score": [1.5, None, 3.2, 4.1],
        }
    )

    metrics = profile_dataframe(df)

    assert metrics["column_missing_counts"] == {"id": 0, "name": 2, "score": 1}


def test_profile_dataframe_reports_dtypes():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
            "score": [1.5, 2.5, 3.5],
        }
    )

    metrics = profile_dataframe(df)

    assert metrics["column_dtypes"]["id"] == "int64"
    assert metrics["column_dtypes"]["score"] == "float64"
    # pandas >= 3.0 reports plain Python string columns as the "str" dtype
    # (previously "object" in pandas < 3.0); this project pins pandas ^3.0.
    assert metrics["column_dtypes"]["name"] == "str"


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as db:
        yield db
    Base.metadata.drop_all(engine)
    engine.dispose()


def _make_dataset(db_session, file_path: str | None) -> Dataset:
    project = Project(name="Profiling tests")
    db_session.add(project)
    db_session.flush()
    dataset = Dataset(project_id=project.id, name="sample.csv", file_path=file_path)
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_profile_dataset_reads_csv_and_persists_profile(tmp_path, db_session):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("id,name,score\n1,Alice,1.5\n2,Bob,\n3,,3.2\n")
    dataset = _make_dataset(db_session, str(csv_path))

    profile = profile_dataset(db_session, dataset)

    assert profile.row_count == 3
    assert profile.column_count == 3
    assert profile.column_missing_counts == {"id": 0, "name": 1, "score": 1}
    assert profile.column_dtypes["id"] == "int64"

    persisted = get_dataset_profile(db_session, dataset.id)
    assert persisted is not None
    assert persisted.row_count == 3


def test_profile_dataset_overwrites_existing_profile(tmp_path, db_session):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n")
    dataset = _make_dataset(db_session, str(csv_path))

    first = profile_dataset(db_session, dataset)
    assert first.row_count == 2

    csv_path.write_text("a,b\n1,2\n3,4\n5,6\n")
    second = profile_dataset(db_session, dataset)

    assert second.row_count == 3
    assert second.id == first.id
    assert db_session.query(DatasetProfile).count() == 1


def test_profile_dataset_raises_when_file_path_missing(db_session):
    dataset = _make_dataset(db_session, None)

    with pytest.raises(DatasetFileMissing):
        profile_dataset(db_session, dataset)


def test_profile_dataset_raises_when_file_does_not_exist(db_session):
    dataset = _make_dataset(db_session, "/nonexistent/path/does-not-exist.csv")

    with pytest.raises(DatasetFileMissing):
        profile_dataset(db_session, dataset)


def test_get_dataset_profile_returns_none_when_absent(db_session):
    dataset = _make_dataset(db_session, None)

    assert get_dataset_profile(db_session, dataset.id) is None
