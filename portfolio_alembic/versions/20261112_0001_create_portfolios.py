"""Create the Portfolio Service persistence schema.

Revision ID: 20261112_0001
Revises: None
Create Date: 2026-11-12
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261112_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "char_length(portfolio_id) BETWEEN 1 AND 64",
            name="ck_portfolios_portfolio_id_length",
        ),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 200",
            name="ck_portfolios_name_length",
        ),
        sa.CheckConstraint(
            "char_length(owner) BETWEEN 1 AND 100",
            name="ck_portfolios_owner_length",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_portfolios_status",
        ),
        sa.PrimaryKeyConstraint("portfolio_id"),
    )
    op.create_index("ix_portfolios_owner", "portfolios", ["owner"], unique=False)
    op.create_index("ix_portfolios_status", "portfolios", ["status"], unique=False)
    op.create_index(
        "ix_portfolios_created_id",
        "portfolios",
        ["created_at", "portfolio_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_portfolios_created_id", table_name="portfolios")
    op.drop_index("ix_portfolios_status", table_name="portfolios")
    op.drop_index("ix_portfolios_owner", table_name="portfolios")
    op.drop_table("portfolios")
