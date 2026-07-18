from pydantic import BaseModel, ConfigDict


class DatasetProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_id: int
    row_count: int
    column_count: int
    column_missing_counts: dict[str, int]
    column_dtypes: dict[str, str]
