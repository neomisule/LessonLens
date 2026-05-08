"""Internal dataclasses for the Break It Down pipeline.

These are NOT Pydantic API schemas — pure Python dataclasses used as
intermediate containers between agents and services.
"""
from dataclasses import dataclass, field
from enum import Enum


class ExplanationStyle(str, Enum):
    SIMPLE      = "simple"       # plainer language, less jargon
    ANALOGY     = "analogy"      # relatable comparison or metaphor
    EXAMPLE     = "example"      # concrete real-world application
    PREREQUISITE = "prerequisite" # what you need to know first
    DIAGRAM     = "diagram"      # textual description of a visual
    ELI5        = "eli5"         # explain like I'm 5


# ISO-639-1 codes supported by ElevenLabs eleven_multilingual_v2
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "tr": "Turkish",
}


@dataclass
class ExplanationResult:
    concept_id: str
    style: ExplanationStyle
    language: str                      # ISO-639-1 code
    content: str                       # the generated explanation text
    source_quote: str                  # transcript quote used as evidence
    timestamp_start: float | None      # from source concept
    cached: bool = False               # True if retrieved from cache


@dataclass
class AudioResult:
    explanation_id: str
    audio_url: str                     # relative URL served by breakdown router
    duration_ms: int | None
    cached: bool = False
    error: str | None = None           # set if ElevenLabs call failed


@dataclass
class RevisitRecommendation:
    concept_id: str
    concept_name: str
    reason: str                        # human-readable reason for revisiting
    priority: int                      # 1 = highest
    timestamp_start: float | None
