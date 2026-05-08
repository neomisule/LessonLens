from langgraph.graph import StateGraph, END

from app.orchestration.state import PipelineState
from app.agents.transcript_agent import TranscriptAgent
from app.agents.segmentation_agent import SegmentationAgent
from app.agents.concept_agent import ConceptAgent
from app.agents.flashcard_agent import FlashcardAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.mindmap_agent import MindMapAgent


def build_pipeline() -> StateGraph:
    """
    Constructs and compiles the LangGraph processing pipeline.

    Graph topology:
        transcript_extraction
            └─► segmentation
                    └─► concept_extraction
                            ├─► flashcard_generation  ─┐
                            └─► summary_generation    ──┤
                                                        └─► mindmap_generation ─► END
    """
    transcript_agent = TranscriptAgent()
    segmentation_agent = SegmentationAgent()
    concept_agent = ConceptAgent()
    flashcard_agent = FlashcardAgent()
    summary_agent = SummaryAgent()
    mindmap_agent = MindMapAgent()

    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("transcript_extraction", transcript_agent)
    graph.add_node("segmentation", segmentation_agent)
    graph.add_node("concept_extraction", concept_agent)
    graph.add_node("flashcard_generation", flashcard_agent)
    graph.add_node("summary_generation", summary_agent)
    graph.add_node("mindmap_generation", mindmap_agent)

    # Linear edges
    graph.set_entry_point("transcript_extraction")
    graph.add_edge("transcript_extraction", "segmentation")
    graph.add_edge("segmentation", "concept_extraction")

    # Fan-out: concept_extraction → flashcard_generation AND summary_generation
    graph.add_edge("concept_extraction", "flashcard_generation")
    graph.add_edge("concept_extraction", "summary_generation")

    # Converge: both parallel branches → mindmap_generation
    graph.add_edge("flashcard_generation", "mindmap_generation")
    graph.add_edge("summary_generation", "mindmap_generation")

    graph.add_edge("mindmap_generation", END)

    return graph.compile()
