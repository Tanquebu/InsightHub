from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DatasetQualityIssue(Base):
    """A single quality-rule violation detected for a dataset's most recent profile.

    Unlike DatasetProfile (one row per dataset, overwritten in place), a dataset can
    have zero or many quality issues at once, so this table is fully cleared and
    re-inserted for a dataset every time quality rules are (re-)evaluated — mirroring
    how DatasetProfile overwrites, but at the row-set level instead of a single row.
    """

    __tablename__ = "dataset_quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )

    rule_code: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    dataset = relationship("Dataset")
