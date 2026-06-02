"""usuario: email_verified e tokens de verificacao/reset

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("usuario", sa.Column("email_verification_token", sa.String(255), nullable=True))
    op.add_column("usuario", sa.Column("password_reset_token", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "password_reset_token")
    op.drop_column("usuario", "email_verification_token")
    op.drop_column("usuario", "email_verified")
