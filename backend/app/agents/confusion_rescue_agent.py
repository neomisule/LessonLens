"""ConfusionRescueAgent — generates alternative explanations on demand.

This is NOT a background pipeline node. It runs synchronously per HTTP
request when a student asks to re-explain a concept in a different style
or language.

Flow per request:
  1. Check ExplanationCache for (concept_id, style, language) — return if hit.
  2. Load concept from DB (definition, explanation, examples, evidence_quote).
  3. Build a style-specific, grounded LLM prompt.
  4. Call LLM → parse JSON response.
  5. Persist to ExplanationCache.
  6. Return ExplanationResult.
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.concept import Concept
from app.models.explanation_cache import ExplanationCache
from app.learn.llm_client import LLMClient
from app.breakdown.schemas import ExplanationStyle, ExplanationResult, SUPPORTED_LANGUAGES
from app.breakdown.prompts import (
    BREAKDOWN_SYSTEM,
    STYLE_PROMPT_MAP,
    language_instruction,
)

logger = logging.getLogger(__name__)


async def _load_concept(db: AsyncSession, concept_id: str) -> Concept | None:
    result = await db.execute(
        select(Concept).where(Concept.id == concept_id)
    )
    return result.scalar_one_or_none()


async def _check_cache(
    db: AsyncSession,
    concept_id: str,
    style: str,
    language: str,
) -> ExplanationCache | None:
    result = await db.execute(
        select(ExplanationCache).where(
            ExplanationCache.concept_id == concept_id,
            ExplanationCache.style == style,
            ExplanationCache.language == language,
        )
    )
    return result.scalar_one_or_none()


def _build_user_prompt(
    concept: Concept,
    style: ExplanationStyle,
    lang_code: str,
) -> str:
    lang_name = SUPPORTED_LANGUAGES.get(lang_code, "English")
    lang_inst = language_instruction(lang_code, lang_name)
    template = STYLE_PROMPT_MAP[style.value]

    examples_str = (
        "; ".join(concept.examples[:3]) if concept.examples else "none provided"
    )

    return template.format(
        name=concept.name,
        definition=concept.definition[:400],
        explanation=(concept.explanation or "")[:400],
        examples=examples_str,
        evidence_quote=(concept.evidence_quote or "")[:300],
        timestamp=concept.timestamp_start or 0.0,
        language_instruction=lang_inst,
    )


class ConfusionRescueAgent:
    """
    Generates grounded alternative explanations for a concept.

    Usage::
        agent = ConfusionRescueAgent(llm)
        result = await agent.explain(db, concept_id, style, language)
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def explain(
        self,
        db: AsyncSession,
        concept_id: str,
        style: ExplanationStyle,
        language: str = "en",
    ) -> ExplanationResult | None:
        """
        Return an ExplanationResult, hitting cache first.

        Returns None if concept not found or LLM unavailable with no cache.
        """
        # ── Cache check ───────────────────────────────────────────────────────
        cached_row = await _check_cache(db, concept_id, style.value, language)
        if cached_row:
            logger.debug(
                "[confusion_rescue] Cache HIT concept=%s style=%s lang=%s",
                concept_id[:8], style.value, language,
            )
            return ExplanationResult(
                concept_id=concept_id,
                style=style,
                language=language,
                content=cached_row.content,
                source_quote=cached_row.source_quote or "",
                timestamp_start=cached_row.timestamp_start,
                cached=True,
            )

        # ── Load concept ──────────────────────────────────────────────────────
        concept = await _load_concept(db, concept_id)
        if not concept:
            logger.warning("[confusion_rescue] Concept not found: %s", concept_id)
            return None

        # ── LLM call ──────────────────────────────────────────────────────────
        if not self._llm.available:
            logger.info("[confusion_rescue] LLM unavailable — returning None")
            return None

        user_prompt = _build_user_prompt(concept, style, language)
        response = await self._llm.extract_json(BREAKDOWN_SYSTEM, user_prompt)

        explanation_text = str(response.get("explanation", "")).strip()
        source_quote = str(response.get("source_quote", "")).strip()

        if not explanation_text:
            logger.warning(
                "[confusion_rescue] Empty LLM response for concept=%s style=%s",
                concept_id[:8], style.value,
            )
            return None

        # ── Persist to cache ──────────────────────────────────────────────────
        row = ExplanationCache(
            concept_id=concept_id,
            lecture_id=concept.lecture_id,
            style=style.value,
            language=language,
            content=explanation_text,
            source_quote=source_quote or concept.evidence_quote,
            timestamp_start=concept.timestamp_start,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)

        logger.info(
            "[confusion_rescue] Generated: concept=%s style=%s lang=%s id=%s",
            concept.name[:30], style.value, language, row.id[:8],
        )

        return ExplanationResult(
            concept_id=concept_id,
            style=style,
            language=language,
            content=explanation_text,
            source_quote=source_quote,
            timestamp_start=concept.timestamp_start,
            cached=False,
        )
