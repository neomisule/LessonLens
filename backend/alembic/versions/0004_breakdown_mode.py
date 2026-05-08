"""breakdown mode

Creates the explanation_cache table for Break It Down Mode.

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-04 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "explanation_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "concept_id",
            sa.String(36),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "lecture_id",
            sa.String(36),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Explanation parameters
        sa.Column("style", sa.String(30), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        # Generated content
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("timestamp_start", sa.Float(), nullable=True),
        # Audio cache
        sa.Column("audio_cache_key", sa.String(64), nullable=True),
        sa.Column("audio_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Unique index: one row per (concept, style, language) combination
    op.create_index(
        "ix_explanation_cache_concept_style_lang",
        "explanation_cache",
        ["concept_id", "style", "language"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_explanation_cache_concept_style_lang", "explanation_cache")
    op.drop_table("explanation_cache")
