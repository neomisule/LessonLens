"""0006 – Search enhancements, subject graph, mindmap columns

Adds:
  - mind_map_nodes: subject_id, importance, exam_likelihood, timestamp_start
  - mind_map_edges: subject_id
  - subject_concepts table
  - subject_concept_links table
  - IVFFlat index on concept embeddings

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


def upgrade() -> None:
    # ── mind_map_nodes: new columns ───────────────────────────────────────────
    with op.batch_alter_table("mind_map_nodes") as batch_op:
        batch_op.add_column(sa.Column(
            "subject_id", sa.String(36),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=True,
        ))
        batch_op.add_column(sa.Column("importance", sa.String(20), nullable=False, server_default="supporting"))
        batch_op.add_column(sa.Column("exam_likelihood", sa.Float(), nullable=False, server_default="0.5"))
        batch_op.add_column(sa.Column("timestamp_start", sa.Float(), nullable=True))
        batch_op.create_index("ix_mind_map_nodes_subject_id", ["subject_id"])

    # ── mind_map_edges: subject_id ────────────────────────────────────────────
    with op.batch_alter_table("mind_map_edges") as batch_op:
        batch_op.add_column(sa.Column(
            "subject_id", sa.String(36),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=True,
        ))
        batch_op.create_index("ix_mind_map_edges_subject_id", ["subject_id"])

    # ── subject_concepts table ────────────────────────────────────────────────
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
    op.create_index(
        "ix_subject_concepts_cluster",
        "subject_concepts",
        ["subject_id", "cluster_label"],
        unique=True,
    )

    # ── subject_concept_links table ───────────────────────────────────────────
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
    op.create_index(
        "ix_scl_unique",
        "subject_concept_links",
        ["subject_concept_id", "concept_id"],
        unique=True,
    )

    # ── IVFFlat index on concepts.embedding (if pgvector available) ───────────
    op.execute("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'ix_concepts_embedding_ivfflat'
          ) THEN
            CREATE INDEX ix_concepts_embedding_ivfflat
            ON concepts USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);
          END IF;
        END$$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_concepts_embedding_ivfflat")

    op.drop_index("ix_scl_unique",             table_name="subject_concept_links")
    op.drop_index("ix_scl_lecture_id",         table_name="subject_concept_links")
    op.drop_index("ix_scl_concept_id",         table_name="subject_concept_links")
    op.drop_index("ix_scl_subject_concept_id", table_name="subject_concept_links")
    op.drop_table("subject_concept_links")

    op.drop_index("ix_subject_concepts_cluster",    table_name="subject_concepts")
    op.drop_index("ix_subject_concepts_subject_id", table_name="subject_concepts")
    op.drop_table("subject_concepts")

    with op.batch_alter_table("mind_map_edges") as batch_op:
        batch_op.drop_index("ix_mind_map_edges_subject_id")
        batch_op.drop_column("subject_id")

    with op.batch_alter_table("mind_map_nodes") as batch_op:
        batch_op.drop_index("ix_mind_map_nodes_subject_id")
        batch_op.drop_column("timestamp_start")
        batch_op.drop_column("exam_likelihood")
        batch_op.drop_column("importance")
        batch_op.drop_column("subject_id")
