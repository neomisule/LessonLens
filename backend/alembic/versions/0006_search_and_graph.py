"""0006 – Search enhancements, subject graph, mindmap columns

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

_SAFE = "DO $$ BEGIN {sql}; EXCEPTION WHEN duplicate_column THEN NULL; END $$;"


def _add_col(table: str, col_sql: str) -> None:
    op.execute(_SAFE.format(sql=f"ALTER TABLE {table} ADD COLUMN {col_sql}"))


def _add_idx(name: str, table: str, col: str) -> None:
    op.execute(f"DO $$ BEGIN CREATE INDEX {name} ON {table}({col}); EXCEPTION WHEN duplicate_table THEN NULL; END $$;")


def upgrade() -> None:
    # ── mind_map_nodes ────────────────────────────────────────────────────────
    _add_col("mind_map_nodes", "subject_id VARCHAR(36) REFERENCES subjects(id) ON DELETE CASCADE")
    _add_col("mind_map_nodes", "importance VARCHAR(20) NOT NULL DEFAULT 'supporting'")
    _add_col("mind_map_nodes", "exam_likelihood FLOAT NOT NULL DEFAULT 0.5")
    _add_col("mind_map_nodes", "timestamp_start FLOAT")
    _add_idx("ix_mind_map_nodes_subject_id", "mind_map_nodes", "subject_id")

    # ── mind_map_edges ────────────────────────────────────────────────────────
    _add_col("mind_map_edges", "subject_id VARCHAR(36) REFERENCES subjects(id) ON DELETE CASCADE")
    _add_idx("ix_mind_map_edges_subject_id", "mind_map_edges", "subject_id")

    conn = op.get_bind()
    insp = sa.inspect(conn)

    # ── subject_concepts table ────────────────────────────────────────────────
    if not insp.has_table("subject_concepts"):
        op.create_table(
            "subject_concepts",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("subject_id", sa.String(36), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("cluster_label", sa.String(300), nullable=False),
            sa.Column("frequency", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_prerequisite", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("importance", sa.String(20), nullable=False, server_default="supporting"),
            sa.Column("avg_exam_likelihood", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("avg_mastery", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_subject_concepts_subject_id", "subject_concepts", ["subject_id"])
        op.create_index("ix_subject_concepts_cluster", "subject_concepts", ["subject_id", "cluster_label"], unique=True)

    # ── subject_concept_links table ───────────────────────────────────────────
    if not insp.has_table("subject_concept_links"):
        op.create_table(
            "subject_concept_links",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("subject_concept_id", sa.String(36), sa.ForeignKey("subject_concepts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("concept_id", sa.String(36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("lecture_id", sa.String(36), sa.ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False),
        )
        op.create_index("ix_scl_subject_concept_id", "subject_concept_links", ["subject_concept_id"])
        op.create_index("ix_scl_concept_id",         "subject_concept_links", ["concept_id"])
        op.create_index("ix_scl_lecture_id",          "subject_concept_links", ["lecture_id"])
        op.create_index("ix_scl_unique",              "subject_concept_links", ["subject_concept_id", "concept_id"], unique=True)

    # ── IVFFlat index on concepts.embedding ──────────────────────────────────
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_concepts_embedding_ivfflat') THEN
            CREATE INDEX ix_concepts_embedding_ivfflat
            ON concepts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
          END IF;
        END $$;
    """)

    # ── stage_errors column on processing_jobs (added in session) ────────────
    _add_col("processing_jobs", "stage_errors JSON")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_concepts_embedding_ivfflat")
    op.execute("DROP TABLE IF EXISTS subject_concept_links CASCADE")
    op.execute("DROP TABLE IF EXISTS subject_concepts CASCADE")
    op.execute("ALTER TABLE mind_map_edges DROP COLUMN IF EXISTS subject_id")
    op.execute("ALTER TABLE mind_map_nodes DROP COLUMN IF EXISTS subject_id")
    op.execute("ALTER TABLE mind_map_nodes DROP COLUMN IF EXISTS timestamp_start")
    op.execute("ALTER TABLE mind_map_nodes DROP COLUMN IF EXISTS exam_likelihood")
    op.execute("ALTER TABLE mind_map_nodes DROP COLUMN IF EXISTS importance")
    op.execute("ALTER TABLE processing_jobs DROP COLUMN IF EXISTS stage_errors")
