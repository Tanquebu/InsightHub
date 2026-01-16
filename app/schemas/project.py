from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True
