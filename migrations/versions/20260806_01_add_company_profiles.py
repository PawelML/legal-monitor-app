"""Add minimal KRS-backed company profiles.

Revision ID: 20260806_01
Revises: 20260716_02
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260806_01"
down_revision: str | None = "20260716_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create public-source company-profile storage without personal fields."""
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("krs_number", sa.String(length=10), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("legal_form", sa.Text(), nullable=False),
        sa.Column("pkd_codes", sa.JSON(), nullable=False),
        sa.Column("monitoring_tags", sa.JSON(), nullable=False),
        sa.Column("registry_updated_on", sa.Date(), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("krs_number"),
    )
    op.create_index(
        "ix_company_profiles_krs_number",
        "company_profiles",
        ["krs_number"],
        unique=False,
    )


def downgrade() -> None:
    """Remove Phase 2 company-profile storage."""
    op.drop_index("ix_company_profiles_krs_number", table_name="company_profiles")
    op.drop_table("company_profiles")
