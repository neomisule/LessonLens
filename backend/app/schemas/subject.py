from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    color: str | None = Field(default=None, max_length=20)
    icon: str | None = Field(default=None, max_length=10)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    color: str | None = Field(default=None, max_length=20)
    icon: str | None = Field(default=None, max_length=10)


class SubjectRead(BaseModel):
    id: str
    name: str
    description: str | None
    color: str | None
    icon: str | None
    lecture_count: int = 0

    model_config = {"from_attributes": True}
