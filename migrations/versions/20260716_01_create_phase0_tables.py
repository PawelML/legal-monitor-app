"""create phase 0 tables

Revision ID: 20260716_01
Revises:
Create Date: 2026-07-16 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "acts",
        sa.Column("eli", sa.String(length=64), nullable=False),
        sa.Column("publisher", sa.String(length=2), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=64), nullable=False),
        sa.Column("display_address", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("act_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=128), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("announcement_date", sa.Date(), nullable=True),
        sa.Column("promulgation_date", sa.Date(), nullable=True),
        sa.Column("source_change_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("has_text_html", sa.Boolean(), nullable=False),
        sa.Column("has_text_pdf", sa.Boolean(), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("eli"),
    )
    op.create_index("ix_acts_publisher", "acts", ["publisher"], unique=False)
    op.create_index("ix_acts_year", "acts", ["year"], unique=False)
    op.create_index(
        "ix_acts_source_change_date", "acts", ["source_change_date"], unique=False
    )
    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_runs_job_type", "job_runs", ["job_type"], unique=False)
    op.create_index("ix_job_runs_status", "job_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_runs_status", table_name="job_runs")
    op.drop_index("ix_job_runs_job_type", table_name="job_runs")
    op.drop_table("job_runs")
    op.drop_index("ix_acts_source_change_date", table_name="acts")
    op.drop_index("ix_acts_year", table_name="acts")
    op.drop_index("ix_acts_publisher", table_name="acts")
    op.drop_table("acts")
