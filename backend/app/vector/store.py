"""Vector embeddings store.

Only OpenAI has a public embeddings API we can call.
Anthropic does NOT provide embeddings — attempts to call it waste 60 s on a timeout.
If no OpenAI key is set, embeddings are skipped and the pipeline falls back to
keyword/fixed-window segmentation (which still works well).
"""
from typing import Any
import httpx

from app.config import get_settings

settings = get_settings()

_OPENAI_EMBED_URL   = "https://api.openai.com/v1/embeddings"
_OPENAI_EMBED_MODEL = "text-embedding-3-small"


def embeddings_available() -> bool:
    """True only when a real embeddings API key is configured."""
    return bool(settings.openai_api_key)


async def _post(url: str, headers: dict, payload: dict) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()


async def create_embedding(text: str) -> list[float]:
    if not settings.openai_api_key:
        raise RuntimeError("No embeddings API key configured (need OPENAI_API_KEY)")
    data = await _post(
        _OPENAI_EMBED_URL,
        {"Authorization": f"Bearer {settings.openai_api_key}"},
        {"input": text, "model": _OPENAI_EMBED_MODEL},
    )
    return data["data"][0]["embedding"]


async def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.openai_api_key:
        raise RuntimeError("No embeddings API key configured (need OPENAI_API_KEY)")
    data = await _post(
        _OPENAI_EMBED_URL,
        {"Authorization": f"Bearer {settings.openai_api_key}"},
        {"input": texts, "model": _OPENAI_EMBED_MODEL},
    )
    items = sorted(data.get("data", []), key=lambda x: x["index"])
    return [item["embedding"] for item in items]
