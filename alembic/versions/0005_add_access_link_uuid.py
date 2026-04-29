"""add access_link_uuid to users

Revision ID: 0005_add_access_link_uuid
Revises: 0004_add_access_key_hash
Create Date: 2026-04-29 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_add_access_link_uuid"
down_revision: Union[str, Sequence[str], None] = "0004_add_access_key_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("access_link_uuid", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_users_access_link_uuid", "users", ["access_link_uuid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_access_link_uuid", table_name="users")
    op.drop_column("users", "access_link_uuid")
