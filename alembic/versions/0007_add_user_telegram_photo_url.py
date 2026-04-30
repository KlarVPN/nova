"""add user telegram photo url

Revision ID: 0007_add_user_telegram_photo_url
Revises: 0006_add_terms_accepted_at
Create Date: 2026-05-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_add_user_telegram_photo_url"
down_revision = "0006_add_terms_accepted_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_photo_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "telegram_photo_url")
