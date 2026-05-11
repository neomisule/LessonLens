"""ingestion fields

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

# Helper: run SQL, silently ignore "duplicate_column" errors
_SAFE = "DO $$ BEGIN {sql}; EXCEPTION WHEN duplicate_column THEN NULL; END $$;"


def _add_col(table: str, col_sql: str) -> None:
    op.execute(_SAFE.format(sql=f"ALTER TABLE {table} ADD COLUMN {col_sql}"))


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # ── Rename youtube_video_id → youtube_id ─────────────────────────────────
    lecture_cols = {c["name"] for c in insp.get_columns("lectures")}
    if "youtube_video_id" in lecture_cols and "youtube_id" not in lecture_cols:
        op.alter_column("lectures", "youtube_video_id", new_column_name="youtube_id")

    # ── transcript_segments ───────────────────────────────────────────────────
    _add_col("transcript_segments", "source VARCHAR(30) NOT NULL DEFAULT 'youtube_captions'")
    _add_col("transcript_segments", "confidence FLOAT")

    # ── semantic_segments (token_count already created in 0001) ───────────────
    _add_col("semantic_segments", "topic_label VARCHAR(200)")
    _add_col("semantic_segments", "topic_boundary_score FLOAT")

    # ── Fix embedding columns to pgvector type (no-op if already vector) ──────
    for tbl in ("semantic_segments", "concepts"):
        op.execute(f"""
            DO $$ BEGIN
                ALTER TABLE {tbl} ALTER COLUMN embedding
                    TYPE vector(1536) USING embedding::vector(1536);
            EXCEPTION WHEN others THEN NULL;
            END $$;
        """)

    # ── processing_jobs ───────────────────────────────────────────────────────
    _add_col("processing_jobs", "progress_metadata JSON")

    # ── lectures ──────────────────────────────────────────────────────────────
    _add_col("lectures", "description TEXT")
    _add_col("lectures", "channel_name VARCHAR(200)")
    _add_col("lectures", "processing_error TEXT")
    _add_col("lectures", "processed_at TIMESTAMPTZ")
    _add_col("lectures", "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")

    # ── transcript_quality table ──────────────────────────────────────────────
    if not insp.has_table("transcript_quality"):
        op.create_table(
            "transcript_quality",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("lecture_id", sa.String(36),
                      sa.ForeignKey("lectures.id", ondelete="CASCADE"),
                      nullable=False, unique=True),
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
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
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
    op.drop_column("transcript_segments", "confidence")
    op.drop_column("transcript_segments", "source")
    op.alter_column("lectures", "youtube_id", new_column_name="youtube_video_id")
