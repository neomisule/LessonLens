"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── subjects ─────────────────────────────────────────────────────────────
    op.create_table(
        "subjects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("icon", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── lectures ──────────────────────────────────────────────────────────────
    op.create_table(
        "lectures",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "subject_id",
            sa.String(36),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("youtube_url", sa.Text, nullable=False),
        sa.Column("youtube_video_id", sa.String(20), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_lectures_subject_id", "lectures", ["subject_id"])
    op.create_index("ix_lectures_processing_status", "lectures", ["processing_status"])

    # ── transcript_segments ───────────────────────────────────────────────────
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("timestamp_start", sa.Float, nullable=True),
        sa.Column("timestamp_end", sa.Float, nullable=True),
        sa.Column("speaker", sa.String(100), nullable=True),
    )
    op.create_index("ix_transcript_segments_lecture_id", "transcript_segments", ["lecture_id"])

    # ── semantic_segments (with pgvector) ─────────────────────────────────────
    op.create_table(
        "semantic_segments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("timestamp_start", sa.Float, nullable=True),
        sa.Column("timestamp_end", sa.Float, nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("segment_index", sa.Integer, nullable=False),
    )
    op.create_index("ix_semantic_segments_lecture_id", "semantic_segments", ["lecture_id"])

    # pgvector IVFFlat index for cosine similarity search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_semantic_segments_embedding
        ON semantic_segments
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )

    # ── concepts ──────────────────────────────────────────────────────────────
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            sa.String(36),
            sa.ForeignKey("semantic_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("definition", sa.Text, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("examples", postgresql.JSON, nullable=True),
        sa.Column("importance", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("timestamp_start", sa.Float, nullable=True),
        sa.Column("timestamp_end", sa.Float, nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
    )
    op.create_index("ix_concepts_lecture_id", "concepts", ["lecture_id"])

    # ── flashcards ────────────────────────────────────────────────────────────
    op.create_table(
        "flashcards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.String(36),
            sa.ForeignKey("concepts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("front", sa.Text, nullable=False),
        sa.Column("back", sa.Text, nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("tags", postgresql.JSON, nullable=True),
    )
    op.create_index("ix_flashcards_lecture_id", "flashcards", ["lecture_id"])

    # ── summaries ─────────────────────────────────────────────────────────────
    op.create_table(
        "summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sections", postgresql.JSON, nullable=True),
    )
    op.create_index("ix_summaries_lecture_id", "summaries", ["lecture_id"])

    # ── quiz_questions ────────────────────────────────────────────────────────
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("options", postgresql.JSON, nullable=True),
        sa.Column("correct_answer", sa.Text, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
    )
    op.create_index("ix_quiz_questions_lecture_id", "quiz_questions", ["lecture_id"])

    # ── user_mastery ──────────────────────────────────────────────────────────
    op.create_table(
        "user_mastery",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.String(36),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "flashcard_id",
            sa.String(36),
            sa.ForeignKey("flashcards.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("mastery_level", sa.String(20), nullable=False, server_default="unseen"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_mastery_lecture_id", "user_mastery", ["lecture_id"])
    op.create_index("ix_user_mastery_concept_id", "user_mastery", ["concept_id"])
    op.create_index("ix_user_mastery_flashcard_id", "user_mastery", ["flashcard_id"])

    # ── mind_map_nodes ────────────────────────────────────────────────────────
    op.create_table(
        "mind_map_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.String(36),
            sa.ForeignKey("concepts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("node_type", sa.String(20), nullable=False, server_default="leaf"),
        sa.Column("position_x", sa.Float, nullable=False, server_default="0"),
        sa.Column("position_y", sa.Float, nullable=False, server_default="0"),
        sa.Column("color", sa.String(20), nullable=True),
    )
    op.create_index("ix_mind_map_nodes_lecture_id", "mind_map_nodes", ["lecture_id"])

    # ── mind_map_edges ────────────────────────────────────────────────────────
    op.create_table(
        "mind_map_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_node_id",
            sa.String(36),
            sa.ForeignKey("mind_map_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_node_id",
            sa.String(36),
            sa.ForeignKey("mind_map_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("edge_type", sa.String(20), nullable=False, server_default="hierarchical"),
    )
    op.create_index("ix_mind_map_edges_lecture_id", "mind_map_edges", ["lecture_id"])

    # ── generated_audio ───────────────────────────────────────────────────────
    op.create_table(
        "generated_audio",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("audio_type", sa.String(30), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_generated_audio_lecture_id", "generated_audio", ["lecture_id"])

    # ── processing_jobs ───────────────────────────────────────────────────────
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("current_step", sa.String(100), nullable=True),
        sa.Column("steps_completed", postgresql.JSON, nullable=True),
        sa.Column("steps_total", sa.Integer, nullable=False, server_default="7"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_processing_jobs_lecture_id", "processing_jobs", ["lecture_id"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("generated_audio")
    op.drop_table("mind_map_edges")
    op.drop_table("mind_map_nodes")
    op.drop_table("user_mastery")
    op.drop_table("quiz_questions")
    op.drop_table("summaries")
    op.drop_table("flashcards")
    op.drop_table("concepts")
    op.drop_table("semantic_segments")
    op.drop_table("transcript_segments")
    op.drop_table("lectures")
    op.drop_table("subjects")
    op.execute("DROP EXTENSION IF EXISTS vector")
