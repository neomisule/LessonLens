from datetime import datetime
from pydantic import BaseModel, Field


class LectureCreate(BaseModel):
    youtube_url: str = Field(..., description="YouTube video URL")
    title: str | None = Field(default=None, max_length=500)
    subject_id: str


class LectureUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    processing_status: str | None = None


class LectureRead(BaseModel):
    id: str
    subject_id: str
    youtube_url: str
    youtube_id: str                  # matches Lecture.youtube_id
    title: str | None
    description: str | None = None
    duration_seconds: int | None
    thumbnail_url: str | None
    channel_name: str | None = None
    processing_status: str
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
