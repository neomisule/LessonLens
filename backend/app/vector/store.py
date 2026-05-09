from typing import Any
import httpx

from app.config import get_settings

settings = get_settings()

_OPENAI_EMBED_URL = "https://api.openai.com/v1/embeddings"
_ANTHROPIC_EMBED_URL = "https://api.anthropic.com/v1/embeddings"
_OPENAI_EMBED_MODEL = "text-embedding-3-small"
_ANTHROPIC_EMBED_MODEL = "claude-3.5-embedding"


def _uses_openai() -> bool:
    return bool(settings.openai_api_key)


def _uses_anthropic() -> bool:
    return bool(settings.anthropic_api_key)


def _openai_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.openai_api_key}"}


def _anthropic_headers() -> dict[str, str]:
    return {
        "x-api-key": settings.anthropic_api_key,
        "Authorization": f"Bearer {settings.anthropic_api_key}",
    }


async def _post_embedding_request(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def create_embedding(text: str) -> list[float]:
    """Return an embedding for a single text string."""
    if _uses_openai():
        data = await _post_embedding_request(
            _OPENAI_EMBED_URL,
            _openai_headers(),
            {"input": text, "model": _OPENAI_EMBED_MODEL},
        )
        return data["data"][0]["embedding"]

    if _uses_anthropic():
        data = await _post_embedding_request(
            _ANTHROPIC_EMBED_URL,
            _anthropic_headers(),
            {"input": text, "model": _ANTHROPIC_EMBED_MODEL},
        )
        return data["data"][0]["embedding"]

    raise RuntimeError(
        "No embedding API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
    )


async def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a batch of texts in a single API call."""
    if _uses_openai():
        data = await _post_embedding_request(
            _OPENAI_EMBED_URL,
            _openai_headers(),
            {"input": texts, "model": _OPENAI_EMBED_MODEL},
        )
    elif _uses_anthropic():
        data = await _post_embedding_request(
            _ANTHROPIC_EMBED_URL,
            _anthropic_headers(),
            {"input": texts, "model": _ANTHROPIC_EMBED_MODEL},
        )
    else:
        raise RuntimeError(
            "No embedding API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
        )

    embeddings = data.get("data", [])
    if not embeddings:
        return []

    if all(isinstance(item, dict) and "index" in item for item in embeddings):
        embeddings = sorted(embeddings, key=lambda x: x["index"])

    return [item["embedding"] for item in embeddings]
