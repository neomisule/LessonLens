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

_SAFE = "DO $$ BEGIN {sql}; EXCEPTION WHEN duplicate_column THEN NULL; END $$;"


def _add_col(table: str, col_sql: str) -> None:
    op.execute(_SAFE.format(sql=f"ALTER TABLE {table} ADD COLUMN {col_sql}"))


def upgrade() -> None:
    # ── flashcards ────────────────────────────────────────────────────────────
    _add_col("flashcards", "question_type VARCHAR(20) NOT NULL DEFAULT 'surface'")
    _add_col("flashcards", "timestamp_start FLOAT")
    _add_col("flashcards", "timestamp_end FLOAT")
    _add_col("flashcards", "time_spent_seconds INTEGER")
    _add_col("flashcards", "exam_likelihood FLOAT NOT NULL DEFAULT 0.5")
    _add_col("flashcards", "evidence_quote TEXT")

    # ── user_mastery ──────────────────────────────────────────────────────────
    _add_col("user_mastery", "confidence VARCHAR(20) NOT NULL DEFAULT 'not_started'")
    _add_col("user_mastery", "ease_factor FLOAT NOT NULL DEFAULT 2.5")
    _add_col("user_mastery", "next_review_interval_days INTEGER NOT NULL DEFAULT 1")

    # ── quiz_questions ────────────────────────────────────────────────────────
    _add_col("quiz_questions", "concept_id VARCHAR(36) REFERENCES concepts(id) ON DELETE SET NULL")
    _add_col("quiz_questions", "timestamp_start FLOAT")
    _add_col("quiz_questions", "evidence_quote TEXT")
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_quiz_questions_concept_id ON quiz_questions(concept_id);
        EXCEPTION WHEN duplicate_table THEN NULL;
        END $$;
    """)

    # ── revision_plans table ──────────────────────────────────────────────────
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table("revision_plans"):
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
    op.execute("DROP INDEX IF EXISTS ix_revision_plans_concept_id")
    op.execute("DROP INDEX IF EXISTS ix_revision_plans_lecture_id")
    op.execute("DROP TABLE IF EXISTS revision_plans")
    op.execute("DROP INDEX IF EXISTS ix_quiz_questions_concept_id")
    op.execute("ALTER TABLE quiz_questions DROP COLUMN IF EXISTS evidence_quote")
    op.execute("ALTER TABLE quiz_questions DROP COLUMN IF EXISTS timestamp_start")
    op.execute("ALTER TABLE quiz_questions DROP COLUMN IF EXISTS concept_id")
    op.execute("ALTER TABLE user_mastery DROP COLUMN IF EXISTS next_review_interval_days")
    op.execute("ALTER TABLE user_mastery DROP COLUMN IF EXISTS ease_factor")
    op.execute("ALTER TABLE user_mastery DROP COLUMN IF EXISTS confidence")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS evidence_quote")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS exam_likelihood")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS time_spent_seconds")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS timestamp_end")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS timestamp_start")
    op.execute("ALTER TABLE flashcards DROP COLUMN IF EXISTS question_type")
