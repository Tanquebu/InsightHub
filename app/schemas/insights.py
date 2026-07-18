from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetMetricsOut(BaseModel):
    row_count: int
    column_count: int
    total_missing_values: int
    column_missing_ratios: dict[str, float]
    completeness_score: float


class DatasetQualityIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str
    severity: str
    message: str
    created_at: datetime


class DatasetInsightsOut(BaseModel):
    dataset_id: int
    metrics: DatasetMetricsOut
    issues: list[DatasetQualityIssueOut]
