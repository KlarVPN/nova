"""add access_key_hash to users

Revision ID: 0004_add_access_key_hash
Revises: 0003_promo_curr_act_not_null
Create Date: 2026-04-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_add_access_key_hash"
down_revision: Union[str, Sequence[str], None] = "0003_promo_curr_act_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("access_key_hash", sa.String(256), nullable=True),
    )
    op.create_index("ix_users_access_key_hash", "users", ["access_key_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_access_key_hash", table_name="users")
    op.drop_column("users", "access_key_hash")
