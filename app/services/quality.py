from typing import Callable

import structlog
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.dataset_profile import DatasetProfile
from app.db.models.dataset_quality_issue import DatasetQualityIssue

log = structlog.get_logger(__name__)

SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"

RULE_EMPTY_DATASET = "EMPTY_DATASET"
RULE_HIGH_MISSING_COLUMN = "HIGH_MISSING_COLUMN"
RULE_LOW_COMPLETENESS_SCORE = "LOW_COMPLETENESS_SCORE"


def compute_dataset_metrics(profile: DatasetProfile) -> dict:
    """Derive a small set of custom metrics from an already-persisted DatasetProfile.

    This is a thin layer on top of profiling data (row/column counts and per-column
    missing counts) — it does not re-read the source file.
    """
    row_count = profile.row_count
    column_count = profile.column_count
    missing_counts = profile.column_missing_counts or {}

    total_missing_values = sum(missing_counts.values())

    column_missing_ratios = {
        col: (count / row_count if row_count > 0 else 0.0)
        for col, count in missing_counts.items()
    }

    total_cells = row_count * column_count
    # A dataset with no rows and/or no columns has nothing to be missing from —
    # treat it as vacuously complete rather than dividing by zero. The dedicated
    # EMPTY_DATASET rule below is responsible for flagging that situation.
    completeness_score = (
        1.0 if total_cells == 0 else 1 - (total_missing_values / total_cells)
    )

    return {
        "row_count": row_count,
        "column_count": column_count,
        "total_missing_values": total_missing_values,
        "column_missing_ratios": column_missing_ratios,
        "completeness_score": completeness_score,
    }


def _rule_empty_dataset(profile: DatasetProfile, metrics: dict) -> list[dict]:
    if metrics["row_count"] == 0:
        return [
            {
                "rule_code": RULE_EMPTY_DATASET,
                "severity": SEVERITY_CRITICAL,
                "message": "Dataset has zero rows.",
            }
        ]
    return []


def _rule_high_missing_columns(profile: DatasetProfile, metrics: dict) -> list[dict]:
    issues = []
    warning_threshold = settings.quality_missing_warning_threshold
    critical_threshold = settings.quality_missing_critical_threshold

    for column, ratio in metrics["column_missing_ratios"].items():
        if ratio >= critical_threshold:
            severity = SEVERITY_CRITICAL
            threshold = critical_threshold
        elif ratio >= warning_threshold:
            severity = SEVERITY_WARNING
            threshold = warning_threshold
        else:
            continue

        issues.append(
            {
                "rule_code": RULE_HIGH_MISSING_COLUMN,
                "severity": severity,
                "message": (
                    f"Column '{column}' has {ratio:.0%} missing values "
                    f"(threshold: {threshold:.0%})."
                ),
            }
        )
    return issues


def _rule_low_completeness_score(profile: DatasetProfile, metrics: dict) -> list[dict]:
    threshold = settings.quality_min_completeness_score
    score = metrics["completeness_score"]
    if score < threshold:
        return [
            {
                "rule_code": RULE_LOW_COMPLETENESS_SCORE,
                "severity": SEVERITY_WARNING,
                "message": (
                    f"Dataset completeness score is {score:.2f}, below threshold {threshold:.2f}."
                ),
            }
        ]
    return []


# A small, explicit list of rule-check functions rather than a generic rule DSL —
# each takes the profile plus its derived metrics and returns zero or more issues.
# Adding a new rule means adding a function here.
RULES: list[Callable[[DatasetProfile, dict], list[dict]]] = [
    _rule_empty_dataset,
    _rule_high_missing_columns,
    _rule_low_completeness_score,
]


def evaluate_quality_rules(profile: DatasetProfile) -> list[dict]:
    """Run all configured quality rules against a dataset's profile.

    Returns a list of issue dicts with keys: rule_code, severity, message.
    """
    metrics = compute_dataset_metrics(profile)
    issues: list[dict] = []
    for rule in RULES:
        issues.extend(rule(profile, metrics))
    return issues


def persist_quality_issues(
    db: Session, dataset_id: int, issues: list[dict]
) -> list[DatasetQualityIssue]:
    """Overwrite the set of persisted quality issues for a dataset.

    Mirrors how DatasetProfile overwrites on each re-run, but since the number of
    issues can vary between runs, this deletes all previous rows for the dataset
    and inserts the freshly computed set.
    """
    db.execute(
        delete(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset_id)
    )

    persisted = []
    for issue in issues:
        row = DatasetQualityIssue(
            dataset_id=dataset_id,
            rule_code=issue["rule_code"],
            severity=issue["severity"],
            message=issue["message"],
        )
        db.add(row)
        persisted.append(row)

    db.commit()
    for row in persisted:
        db.refresh(row)

    log.info(
        "dataset.quality_issues.persisted",
        dataset_id=dataset_id,
        issue_count=len(persisted),
    )
    return persisted


def get_dataset_quality_issues(
    db: Session, dataset_id: int
) -> list[DatasetQualityIssue]:
    return list(
        db.scalars(
            select(DatasetQualityIssue)
            .where(DatasetQualityIssue.dataset_id == dataset_id)
            .order_by(DatasetQualityIssue.id)
        ).all()
    )
