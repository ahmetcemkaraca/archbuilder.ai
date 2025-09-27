from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_rag_jobs_and_docs"
down_revision = "0002_rag_dataset_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_type", sa.String(length=50), index=True),
        sa.Column("status", sa.String(length=20), index=True),
        sa.Column("dataset_id", sa.String(length=64), index=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "rag_document_links",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("dataset_id", sa.String(length=64), index=True),
        sa.Column("document_id", sa.String(length=64), index=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rag_document_links")
    op.drop_table("rag_jobs")
