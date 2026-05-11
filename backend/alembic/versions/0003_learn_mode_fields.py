"""learn mode fields

Adds Learn Mode columns to existing tables and creates the chapters table.

Changes:
  - concepts: add time_spent_seconds, exam_likelihood, why_it_matters,
              prerequisites, related_concepts, evidence_timestamps
  - concepts: add evidence_quote column (used by grounding verification)
  - summaries: rename summary_type → level, add title, add created_at
  - summaries: broaden content column (already Text, no-op)
  - new table: chapters

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


_SAFE = "DO $$ BEGIN {sql}; EXCEPTION WHEN duplicate_column THEN NULL; END $$;"


def _add_col(table: str, col_sql: str) -> None:
    op.execute(_SAFE.format(sql=f"ALTER TABLE {table} ADD COLUMN {col_sql}"))


def upgrade() -> None:
    # ── concepts: add Learn Mode enrichment columns (idempotent) ─────────────
    _add_col("concepts", "time_spent_seconds FLOAT")
    _add_col("concepts", "exam_likelihood FLOAT NOT NULL DEFAULT 0.5")
    _add_col("concepts", "why_it_matters TEXT")
    _add_col("concepts", "prerequisites JSON DEFAULT '[]'")
    _add_col("concepts", "related_concepts JSON DEFAULT '[]'")
    _add_col("concepts", "evidence_timestamps JSON DEFAULT '[]'")
    _add_col("concepts", "evidence_quote TEXT")

    # ── summaries: rename summary_type → level, add title + created_at ───────
    # Check whether the rename was already done (idempotent safety)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    summary_cols = {c["name"] for c in insp.get_columns("summaries")}

    if "summary_type" in summary_cols and "level" not in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.alter_column(
                "summary_type",
                new_column_name="level",
                existing_type=sa.String(20),
                existing_nullable=False,
            )

    if "title" not in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.add_column(
                sa.Column("title", sa.String(500), nullable=False, server_default="")
            )

    if "created_at" not in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                )
            )

    # ── chapters: create table ─────────────────────────────────────────────────
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if insp.has_table("chapters"):
        return
    op.create_table(
        "chapters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("timestamp_start", sa.Float(), nullable=False),
        sa.Column("timestamp_end", sa.Float(), nullable=True),
        sa.Column("concept_names", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Drop chapters table
    op.drop_table("chapters")

    # Revert summaries changes
    conn = op.get_bind()
    insp = sa.inspect(conn)
    summary_cols = {c["name"] for c in insp.get_columns("summaries")}

    if "created_at" in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.drop_column("created_at")

    if "title" in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.drop_column("title")

    if "level" in summary_cols and "summary_type" not in summary_cols:
        with op.batch_alter_table("summaries") as batch_op:
            batch_op.alter_column(
                "level",
                new_column_name="summary_type",
                existing_type=sa.String(20),
                existing_nullable=False,
            )

    # Revert concepts columns
    with op.batch_alter_table("concepts") as batch_op:
        for col in [
            "evidence_quote",
            "evidence_timestamps",
            "related_concepts",
            "prerequisites",
            "why_it_matters",
            "exam_likelihood",
            "time_spent_seconds",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
