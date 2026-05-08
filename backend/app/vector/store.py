from typing import Any
import httpx

from app.config import get_settings

settings = get_settings()

_OPENAI_EMBED_URL = "https://api.openai.com/v1/embeddings"
_EMBED_MODEL = "text-embedding-3-small"


async def create_embedding(text: str) -> list[float]:
    """Return a 1536-dim embedding for a single text string."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            _OPENAI_EMBED_URL,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"input": text, "model": _EMBED_MODEL},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


async def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a batch of texts in a single API call."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            _OPENAI_EMBED_URL,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"input": texts, "model": _EMBED_MODEL},
        )
        response.raise_for_status()
        data = response.json()
        # API returns items sorted by index
        return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
