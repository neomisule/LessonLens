"""0005 – Revise Mode: flashcard/quiz/mastery columns + revision_plans table

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── flashcards: add Revise Mode columns ──────────────────────────────────
    with op.batch_alter_table("flashcards") as batch_op:
        batch_op.add_column(sa.Column("question_type", sa.String(20), nullable=False, server_default="surface"))
        batch_op.add_column(sa.Column("timestamp_start", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("timestamp_end", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("time_spent_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("exam_likelihood", sa.Float(), nullable=False, server_default="0.5"))
        batch_op.add_column(sa.Column("evidence_quote", sa.Text(), nullable=True))

    # ── user_mastery: add SM-2 columns ────────────────────────────────────────
    with op.batch_alter_table("user_mastery") as batch_op:
        batch_op.add_column(sa.Column("confidence", sa.String(20), nullable=False, server_default="not_started"))
        batch_op.add_column(sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"))
        batch_op.add_column(sa.Column("next_review_interval_days", sa.Integer(), nullable=False, server_default="1"))

    # ── quiz_questions: add concept_id, grounding columns ────────────────────
    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.add_column(sa.Column(
            "concept_id", sa.String(36),
            sa.ForeignKey("concepts.id", ondelete="SET NULL"),
            nullable=True,
        ))
        batch_op.add_column(sa.Column("timestamp_start", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("evidence_quote", sa.Text(), nullable=True))
        batch_op.create_index("ix_quiz_questions_concept_id", ["concept_id"])

    # ── revision_plans table ──────────────────────────────────────────────────
    op.create_table(
        "revision_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lecture_id", sa.String(36), sa.ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("concept_name", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("due_in_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timestamp_start", sa.Float(), nullable=True),
        sa.Column("exam_likelihood", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_revision_plans_lecture_id", "revision_plans", ["lecture_id"])
    op.create_index("ix_revision_plans_concept_id", "revision_plans", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_revision_plans_concept_id", table_name="revision_plans")
    op.drop_index("ix_revision_plans_lecture_id", table_name="revision_plans")
    op.drop_table("revision_plans")

    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.drop_index("ix_quiz_questions_concept_id")
        batch_op.drop_column("evidence_quote")
        batch_op.drop_column("timestamp_start")
        batch_op.drop_column("concept_id")

    with op.batch_alter_table("user_mastery") as batch_op:
        batch_op.drop_column("next_review_interval_days")
        batch_op.drop_column("ease_factor")
        batch_op.drop_column("confidence")

    with op.batch_alter_table("flashcards") as batch_op:
        batch_op.drop_column("evidence_quote")
        batch_op.drop_column("exam_likelihood")
        batch_op.drop_column("time_spent_seconds")
        batch_op.drop_column("timestamp_end")
        batch_op.drop_column("timestamp_start")
        batch_op.drop_column("question_type")
