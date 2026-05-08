from typing import Any

from app.agents.base import BaseAgent


class TranscriptAgent(BaseAgent):
    """
    Downloads and extracts the transcript from a YouTube lecture.

    TODO: Implement using yt-dlp or YouTube Data API v3 to fetch
    auto-generated or manual captions, then store raw segments in
    the `transcript_segments` table.
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # Stub — not yet implemented
        return {
            "transcript_ready": False,
            "error": "TranscriptAgent not yet implemented",
        }
