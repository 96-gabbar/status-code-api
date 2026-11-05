"""Create the trade exceptions persistence schema.

Revision ID: 20261106_0001
Revises: None
Create Date: 2026-11-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261106_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence("exception_id_seq", start=10001)))
    op.create_table(
        "trade_exceptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exception_id", sa.String(length=32), nullable=False),
        sa.Column("portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution_code", sa.String(length=100), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "exception_id ~ '^EXC-[0-9]+$'",
            name="ck_trade_exceptions_exception_id_format",
        ),
        sa.CheckConstraint(
            "type IN ('SETTLEMENT_MISMATCH', 'MISSING_REFERENCE_DATA', "
            "'POSITION_MISMATCH', 'PRICE_VARIANCE', 'CASH_BREAK', 'OTHER')",
            name="ck_trade_exceptions_type",
        ),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_trade_exceptions_severity",
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')",
            name="ck_trade_exceptions_status",
        ),
        sa.CheckConstraint(
            "char_length(portfolio_id) BETWEEN 1 AND 64",
            name="ck_trade_exceptions_portfolio_id_length",
        ),
        sa.CheckConstraint(
            "char_length(transaction_id) BETWEEN 1 AND 64",
            name="ck_trade_exceptions_transaction_id_length",
        ),
        sa.CheckConstraint(
            "char_length(description) BETWEEN 1 AND 2000",
            name="ck_trade_exceptions_description_length",
        ),
        sa.CheckConstraint(
            "assigned_to IS NULL OR char_length(assigned_to) BETWEEN 1 AND 100",
            name="ck_trade_exceptions_assigned_to_length",
        ),
        sa.CheckConstraint(
            "resolution_code IS NULL OR char_length(resolution_code) BETWEEN 1 AND 100",
            name="ck_trade_exceptions_resolution_code_length",
        ),
        sa.CheckConstraint(
            "resolution_notes IS NULL OR char_length(resolution_notes) BETWEEN 1 AND 2000",
            name="ck_trade_exceptions_resolution_notes_length",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exception_id"),
    )
    op.create_index(
        "ix_trade_exceptions_created_id",
        "trade_exceptions",
        ["created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_trade_exceptions_portfolio_id",
        "trade_exceptions",
        ["portfolio_id"],
        unique=False,
    )
    op.create_index(
        "ix_trade_exceptions_severity",
        "trade_exceptions",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_trade_exceptions_status",
        "trade_exceptions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trade_exceptions_status", table_name="trade_exceptions")
    op.drop_index("ix_trade_exceptions_severity", table_name="trade_exceptions")
    op.drop_index("ix_trade_exceptions_portfolio_id", table_name="trade_exceptions")
    op.drop_index("ix_trade_exceptions_created_id", table_name="trade_exceptions")
    op.drop_table("trade_exceptions")
    op.execute(sa.schema.DropSequence(sa.Sequence("exception_id_seq")))
