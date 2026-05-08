from langgraph.graph import StateGraph, END

from app.orchestration.state import PipelineState
from app.agents.transcript_agent import TranscriptAgent
from app.agents.segmentation_agent import SegmentationAgent
from app.agents.concept_agent import ConceptAgent
from app.agents.student_tutor_agent import StudentTutorAgent
from app.agents.concept_mapper_agent import ConceptMapperAgent
from app.agents.grounding_agent import GroundingAgent
from app.agents.flashcard_agent import FlashcardAgent
from app.agents.mindmap_agent import MindMapAgent


def build_pipeline() -> StateGraph:
    """
    Constructs and compiles the LangGraph processing pipeline.

    Graph topology:
        transcript_extraction
            └─► segmentation
                    └─► concept_extraction
                            ├─► learn_mode (chapters + summaries)
                            │       └─► concept_mapping (exam scoring, why-it-matters)
                            │               └─► grounding (transcript verification)
                            │                       └─► mindmap_generation ─► END
                            └─► flashcard_generation ─────────────────────────────┘
    """
    transcript_agent = TranscriptAgent()
    segmentation_agent = SegmentationAgent()
    concept_agent = ConceptAgent()
    student_tutor_agent = StudentTutorAgent()
    concept_mapper_agent = ConceptMapperAgent()
    grounding_agent = GroundingAgent()
    flashcard_agent = FlashcardAgent()
    mindmap_agent = MindMapAgent()

    graph = StateGraph(PipelineState)

    # ── Register nodes ─────────────────────────────────────────────────────
    graph.add_node("transcript_extraction", transcript_agent)
    graph.add_node("segmentation", segmentation_agent)
    graph.add_node("concept_extraction", concept_agent)

    # Learn Mode chain
    graph.add_node("learn_mode", student_tutor_agent)
    graph.add_node("concept_mapping", concept_mapper_agent)
    graph.add_node("grounding", grounding_agent)

    # Parallel branch
    graph.add_node("flashcard_generation", flashcard_agent)

    # Convergence
    graph.add_node("mindmap_generation", mindmap_agent)

    # ── Edges ──────────────────────────────────────────────────────────────
    graph.set_entry_point("transcript_extraction")
    graph.add_edge("transcript_extraction", "segmentation")
    graph.add_edge("segmentation", "concept_extraction")

    # Fan-out: learn_mode chain + flashcard_generation in parallel
    graph.add_edge("concept_extraction", "learn_mode")
    graph.add_edge("concept_extraction", "flashcard_generation")

    # Learn Mode sequential chain
    graph.add_edge("learn_mode", "concept_mapping")
    graph.add_edge("concept_mapping", "grounding")

    # Both branches converge at mindmap_generation
    graph.add_edge("grounding", "mindmap_generation")
    graph.add_edge("flashcard_generation", "mindmap_generation")

    graph.add_edge("mindmap_generation", END)

    return graph.compile()
