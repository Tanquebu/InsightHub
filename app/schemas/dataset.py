from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DatasetStatus = Literal["uploaded", "pending", "processing", "completed", "failed"]
DatasetSourceType = Literal["upload", "url", "api"]


class DatasetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    source_type: DatasetSourceType = "upload"


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    status: DatasetStatus | None = None
    source_type: DatasetSourceType | None = None


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    status: str
    source_type: str


class DatasetIngestionOut(BaseModel):
    dataset_id: int
    status: DatasetStatus
    task_id: str
