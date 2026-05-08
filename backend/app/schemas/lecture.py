from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


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
    youtube_video_id: str | None
    title: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    processing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
