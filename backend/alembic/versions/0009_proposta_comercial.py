"""Cria tabela proposta_comercial

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proposta_comercial",
        sa.Column("id",         UUID(as_uuid=True), nullable=False),
        sa.Column("codigo",     sa.String(30),   nullable=False),
        sa.Column("owner_id",   UUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", UUID(as_uuid=True), nullable=True),
        # rascunho | enviada | aceita | recusada
        sa.Column("status",     sa.String(20),   nullable=False, server_default="rascunho"),
        # Toda a composição (fonte de preços, custos, margem, condições, valores) em JSON
        sa.Column("dados",      JSON(),          nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
        sa.ForeignKeyConstraint(["owner_id"],   ["usuario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["projeto_id"], ["projeto.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_proposta_owner", "proposta_comercial", ["owner_id"])


def downgrade() -> None:
    op.drop_table("proposta_comercial")
