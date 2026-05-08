"""ingestion fields

Adds transcript ingestion columns to existing tables and creates the
transcript_quality table.  Also renames the youtube_video_id column on
the lectures table to youtube_id to match the ORM model.

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Rename youtube_video_id → youtube_id on lectures ─────────────────────
    op.alter_column("lectures", "youtube_video_id", new_column_name="youtube_id")

    # ── Add ingestion source + confidence to transcript_segments ──────────────
    op.add_column(
        "transcript_segments",
        sa.Column("source", sa.String(30), nullable=False, server_default="youtube_captions"),
    )
    op.add_column(
        "transcript_segments",
        sa.Column("confidence", sa.Float, nullable=True),
    )

    # ── Add segmentation metadata to semantic_segments ────────────────────────
    op.add_column(
        "semantic_segments",
        sa.Column("token_count", sa.Integer, nullable=True),
    )
    op.add_column(
        "semantic_segments",
        sa.Column("topic_label", sa.String(200), nullable=True),
    )
    op.add_column(
        "semantic_segments",
        sa.Column("topic_boundary_score", sa.Float, nullable=True),
    )

    # ── Fix embedding column to use pgvector vector type ──────────────────────
    # Drop old ARRAY(float) column if it exists, add proper vector column
    # (Safe: if already vector type, this is a no-op for existing data)
    op.execute("ALTER TABLE semantic_segments ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")
    op.execute("ALTER TABLE concepts ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")

    # ── Add progress_metadata to processing_jobs ──────────────────────────────
    op.add_column(
        "processing_jobs",
        sa.Column("progress_metadata", postgresql.JSON, nullable=True),
    )

    # ── Add additional fields to lectures ─────────────────────────────────────
    op.add_column(
        "lectures",
        sa.Column("description", sa.Text, nullable=True),
    )
    op.add_column(
        "lectures",
        sa.Column("channel_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "lectures",
        sa.Column("processing_error", sa.Text, nullable=True),
    )
    op.add_column(
        "lectures",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "lectures",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── transcript_quality table ──────────────────────────────────────────────
    op.create_table(
        "transcript_quality",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("is_fallback", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence_avg", sa.Float, nullable=False),
        sa.Column("confidence_min", sa.Float, nullable=False),
        sa.Column("noise_ratio", sa.Float, nullable=False, server_default="0"),
        sa.Column("coverage_pct", sa.Float, nullable=False),
        sa.Column("gap_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("gap_locations", postgresql.JSON, nullable=True),
        sa.Column("word_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("segment_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_duration", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_transcript_quality_lecture_id", "transcript_quality", ["lecture_id"])


def downgrade() -> None:
    op.drop_table("transcript_quality")

    op.drop_column("lectures", "updated_at")
    op.drop_column("lectures", "processed_at")
    op.drop_column("lectures", "processing_error")
    op.drop_column("lectures", "channel_name")
    op.drop_column("lectures", "description")

    op.drop_column("processing_jobs", "progress_metadata")

    op.drop_column("semantic_segments", "topic_boundary_score")
    op.drop_column("semantic_segments", "topic_label")
    op.drop_column("semantic_segments", "token_count")

    op.drop_column("transcript_segments", "confidence")
    op.drop_column("transcript_segments", "source")

    op.alter_column("lectures", "youtube_id", new_column_name="youtube_video_id")
