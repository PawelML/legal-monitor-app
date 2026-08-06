"""Add immutable extracted-text and analysis versions.

Revision ID: 20260716_02
Revises: 20260716_01
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_02"
down_revision: str | None = "20260716_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create versioned source-text and LLM-analysis storage."""
    op.create_table(
        "act_texts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("act_eli", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("pages", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["act_eli"], ["acts.eli"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("act_eli", "content_hash"),
    )
    op.create_index("ix_act_texts_act_eli", "act_texts", ["act_eli"])
    op.create_index("ix_act_texts_content_hash", "act_texts", ["content_hash"])
    op.create_table(
        "act_analyses",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("act_eli", sa.String(length=64), nullable=False),
        sa.Column("act_text_id", sa.String(length=32), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["act_eli"], ["acts.eli"]),
        sa.ForeignKeyConstraint(["act_text_id"], ["act_texts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_act_analyses_act_eli", "act_analyses", ["act_eli"])
    op.create_index("ix_act_analyses_act_text_id", "act_analyses", ["act_text_id"])


def downgrade() -> None:
    """Remove Phase 1 version tables."""
    op.drop_index("ix_act_analyses_act_text_id", table_name="act_analyses")
    op.drop_index("ix_act_analyses_act_eli", table_name="act_analyses")
    op.drop_table("act_analyses")
    op.drop_index("ix_act_texts_content_hash", table_name="act_texts")
    op.drop_index("ix_act_texts_act_eli", table_name="act_texts")
    op.drop_table("act_texts")
