from typing import TypedDict


class PipelineState(TypedDict, total=False):
    """Shared state dict threaded through every LangGraph node."""

    # Input
    lecture_id: str
    job_id: str
    youtube_url: str
    youtube_video_id: str

    # Stage: transcript
    transcript_ready: bool
    transcript_segments: list[dict]

    # Stage: segmentation
    segmentation_ready: bool
    semantic_segments: list[dict]

    # Stage: concept extraction
    concepts_ready: bool
    concepts: list[dict]

    # Stage: flashcard generation (fan-out from concepts)
    flashcards_ready: bool
    flashcards: list[dict]

    # Stage: summary generation (fan-out from concepts, parallel with flashcards)
    summaries_ready: bool
    summaries: list[dict]

    # Stage: mind map (converges after flashcards + summaries)
    mindmap_ready: bool
    mindmap_nodes: list[dict]
    mindmap_edges: list[dict]

    # Error propagation
    error: str | None
