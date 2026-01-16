from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    source_type: str = Field(default="upload", max_length=30)


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    status: str | None = Field(default=None, max_length=30)
    source_type: str | None = Field(default=None, max_length=30)


class DatasetOut(BaseModel):
    id: int
    project_id: int
    name: str
    status: str
    source_type: str

    class Config:
        from_attributes = True
