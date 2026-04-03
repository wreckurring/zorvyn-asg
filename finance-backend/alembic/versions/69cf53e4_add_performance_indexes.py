revision = "69cf53e4"
down_revision = "69cedc89"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.create_index("ix_transactions_date", "transactions", ["date"])
    op.create_index("ix_transactions_type", "transactions", ["type"])
    op.create_index("ix_transactions_category", "transactions", ["category"])
    op.create_index("ix_transactions_created_by", "transactions", ["created_by"])
    op.create_index(
        "ix_transactions_active_date",
        "transactions",
        ["is_deleted", "date"],
    )
    op.create_index(
        "ix_transactions_active_type",
        "transactions",
        ["is_deleted", "type"],
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_active_type", table_name="transactions")
    op.drop_index("ix_transactions_active_date", table_name="transactions")
    op.drop_index("ix_transactions_created_by", table_name="transactions")
    op.drop_index("ix_transactions_category", table_name="transactions")
    op.drop_index("ix_transactions_type", table_name="transactions")
    op.drop_index("ix_transactions_date", table_name="transactions")
