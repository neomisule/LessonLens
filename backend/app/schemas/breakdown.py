from datetime import datetime
from pydantic import BaseModel, Field
from app.breakdown.schemas import ExplanationStyle, SUPPORTED_LANGUAGES


# ── Request schemas ───────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    concept_id: str
    style: ExplanationStyle = ExplanationStyle.SIMPLE
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")

    def validated_language(self) -> str:
        return self.language if self.language in SUPPORTED_LANGUAGES else "en"


class AudioRequest(BaseModel):
    explanation_id: str


# ── Response schemas ──────────────────────────────────────────────────────────

class ExplanationRead(BaseModel):
    id: str
    concept_id: str
    style: str
    language: str
    content: str
    source_quote: str | None = None
    timestamp_start: float | None = None
    audio_url: str | None = None         # set when audio has been generated
    audio_duration_ms: int | None = None
    cached: bool = False
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AudioRead(BaseModel):
    explanation_id: str
    audio_url: str
    duration_ms: int | None = None
    cached: bool = False
    error: str | None = None


class RevisitRecommendationRead(BaseModel):
    concept_id: str
    concept_name: str
    reason: str
    priority: int
    timestamp_start: float | None = None
    exam_likelihood: float = 0.5
    importance: str = "supporting"


class SupportedLanguagesRead(BaseModel):
    languages: dict[str, str]   # {code: name}
