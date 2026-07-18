import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.models.dataset import Dataset
from app.db.models.dataset_profile import DatasetProfile
from app.db.models.dataset_quality_issue import DatasetQualityIssue
from app.db.models.project import Project
from app.services.quality import (
    RULE_EMPTY_DATASET,
    RULE_HIGH_MISSING_COLUMN,
    RULE_LOW_COMPLETENESS_SCORE,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    compute_dataset_metrics,
    evaluate_quality_rules,
    get_dataset_quality_issues,
    persist_quality_issues,
)


def _profile(
    row_count: int,
    column_count: int,
    column_missing_counts: dict,
    column_dtypes: dict | None = None,
) -> DatasetProfile:
    return DatasetProfile(
        dataset_id=1,
        row_count=row_count,
        column_count=column_count,
        column_missing_counts=column_missing_counts,
        column_dtypes=column_dtypes or {},
    )


# --- compute_dataset_metrics -------------------------------------------------


def test_compute_dataset_metrics_computes_completeness_score():
    profile = _profile(
        row_count=10,
        column_count=2,
        column_missing_counts={"a": 2, "b": 0},
    )

    metrics = compute_dataset_metrics(profile)

    assert metrics["row_count"] == 10
    assert metrics["column_count"] == 2
    assert metrics["total_missing_values"] == 2
    assert metrics["column_missing_ratios"] == {"a": 0.2, "b": 0.0}
    # 1 - 2/(10*2) = 0.9
    assert metrics["completeness_score"] == pytest.approx(0.9)


def test_compute_dataset_metrics_handles_zero_rows_without_dividing_by_zero():
    profile = _profile(
        row_count=0, column_count=3, column_missing_counts={"a": 0, "b": 0, "c": 0}
    )

    metrics = compute_dataset_metrics(profile)

    assert metrics["column_missing_ratios"] == {"a": 0.0, "b": 0.0, "c": 0.0}
    assert metrics["completeness_score"] == 1.0


def test_compute_dataset_metrics_handles_zero_columns():
    profile = _profile(row_count=5, column_count=0, column_missing_counts={})

    metrics = compute_dataset_metrics(profile)

    assert metrics["total_missing_values"] == 0
    assert metrics["completeness_score"] == 1.0


# --- rule evaluation ---------------------------------------------------------


def test_empty_dataset_rule_triggers_when_row_count_is_zero():
    profile = _profile(
        row_count=0, column_count=2, column_missing_counts={"a": 0, "b": 0}
    )

    issues = evaluate_quality_rules(profile)

    codes = [issue["rule_code"] for issue in issues]
    assert RULE_EMPTY_DATASET in codes
    empty_issue = next(i for i in issues if i["rule_code"] == RULE_EMPTY_DATASET)
    assert empty_issue["severity"] == SEVERITY_CRITICAL


def test_empty_dataset_rule_does_not_trigger_with_rows():
    profile = _profile(
        row_count=5, column_count=2, column_missing_counts={"a": 0, "b": 0}
    )

    issues = evaluate_quality_rules(profile)

    codes = [issue["rule_code"] for issue in issues]
    assert RULE_EMPTY_DATASET not in codes


def test_high_missing_column_rule_triggers_warning_between_thresholds():
    # warning threshold 0.2, critical 0.5 by default; 30% missing -> warning
    profile = _profile(row_count=10, column_count=1, column_missing_counts={"a": 3})

    issues = evaluate_quality_rules(profile)

    high_missing = [i for i in issues if i["rule_code"] == RULE_HIGH_MISSING_COLUMN]
    assert len(high_missing) == 1
    assert high_missing[0]["severity"] == SEVERITY_WARNING
    assert "a" in high_missing[0]["message"]


def test_high_missing_column_rule_triggers_critical_above_critical_threshold():
    profile = _profile(row_count=10, column_count=1, column_missing_counts={"a": 6})

    issues = evaluate_quality_rules(profile)

    high_missing = [i for i in issues if i["rule_code"] == RULE_HIGH_MISSING_COLUMN]
    assert len(high_missing) == 1
    assert high_missing[0]["severity"] == SEVERITY_CRITICAL


def test_high_missing_column_rule_does_not_trigger_below_warning_threshold():
    profile = _profile(row_count=10, column_count=1, column_missing_counts={"a": 1})

    issues = evaluate_quality_rules(profile)

    high_missing = [i for i in issues if i["rule_code"] == RULE_HIGH_MISSING_COLUMN]
    assert high_missing == []


def test_high_missing_column_rule_reports_one_issue_per_offending_column():
    profile = _profile(
        row_count=10,
        column_count=3,
        column_missing_counts={"a": 6, "b": 0, "c": 3},
    )

    issues = evaluate_quality_rules(profile)

    columns_flagged = [
        i["message"] for i in issues if i["rule_code"] == RULE_HIGH_MISSING_COLUMN
    ]
    assert len(columns_flagged) == 2  # "a" (critical) and "c" (warning), not "b"


def test_low_completeness_rule_triggers_below_threshold():
    # completeness threshold defaults to 0.7. total_missing=8, total_cells=20
    # -> completeness = 0.6, below threshold.
    profile = _profile(
        row_count=10,
        column_count=2,
        column_missing_counts={"a": 4, "b": 4},
    )

    issues = evaluate_quality_rules(profile)

    codes = [issue["rule_code"] for issue in issues]
    assert RULE_LOW_COMPLETENESS_SCORE in codes


def test_low_completeness_rule_does_not_trigger_above_threshold():
    profile = _profile(
        row_count=10, column_count=2, column_missing_counts={"a": 0, "b": 0}
    )

    issues = evaluate_quality_rules(profile)

    codes = [issue["rule_code"] for issue in issues]
    assert RULE_LOW_COMPLETENESS_SCORE not in codes


def test_thresholds_are_read_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "quality_missing_warning_threshold", 0.05)
    monkeypatch.setattr(settings, "quality_missing_critical_threshold", 0.9)
    profile = _profile(row_count=10, column_count=1, column_missing_counts={"a": 1})

    issues = evaluate_quality_rules(profile)

    high_missing = [i for i in issues if i["rule_code"] == RULE_HIGH_MISSING_COLUMN]
    assert len(high_missing) == 1
    assert high_missing[0]["severity"] == SEVERITY_WARNING


# --- persistence --------------------------------------------------------


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


def _make_dataset(db_session) -> Dataset:
    project = Project(name="Quality tests")
    db_session.add(project)
    db_session.flush()
    dataset = Dataset(project_id=project.id, name="sample.csv")
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_persist_quality_issues_stores_rows(db_session):
    dataset = _make_dataset(db_session)
    issues = [
        {
            "rule_code": RULE_EMPTY_DATASET,
            "severity": SEVERITY_CRITICAL,
            "message": "no rows",
        },
    ]

    persisted = persist_quality_issues(db_session, dataset.id, issues)

    assert len(persisted) == 1
    stored = get_dataset_quality_issues(db_session, dataset.id)
    assert len(stored) == 1
    assert stored[0].rule_code == RULE_EMPTY_DATASET


def test_persist_quality_issues_overwrites_previous_run(db_session):
    dataset = _make_dataset(db_session)
    persist_quality_issues(
        db_session,
        dataset.id,
        [
            {
                "rule_code": RULE_EMPTY_DATASET,
                "severity": SEVERITY_CRITICAL,
                "message": "no rows",
            }
        ],
    )

    persist_quality_issues(
        db_session,
        dataset.id,
        [
            {
                "rule_code": RULE_HIGH_MISSING_COLUMN,
                "severity": SEVERITY_WARNING,
                "message": "col a missing",
            }
        ],
    )

    stored = get_dataset_quality_issues(db_session, dataset.id)
    assert len(stored) == 1
    assert stored[0].rule_code == RULE_HIGH_MISSING_COLUMN
    assert db_session.query(DatasetQualityIssue).count() == 1


def test_persist_quality_issues_with_empty_list_clears_issues(db_session):
    dataset = _make_dataset(db_session)
    persist_quality_issues(
        db_session,
        dataset.id,
        [
            {
                "rule_code": RULE_EMPTY_DATASET,
                "severity": SEVERITY_CRITICAL,
                "message": "no rows",
            }
        ],
    )

    persist_quality_issues(db_session, dataset.id, [])

    assert get_dataset_quality_issues(db_session, dataset.id) == []


def test_get_dataset_quality_issues_returns_empty_list_when_none_persisted(db_session):
    dataset = _make_dataset(db_session)

    assert get_dataset_quality_issues(db_session, dataset.id) == []
