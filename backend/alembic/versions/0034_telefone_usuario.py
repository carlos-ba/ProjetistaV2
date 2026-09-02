"""Adiciona usuario.telefone

Captura o telefone/WhatsApp no cadastro público (trial self-serve) — vira
lead pro time de vendas contatar. Coluna nullable (contas existentes não
têm esse dado, e usuário adicional criado pelo admin não precisa dele —
obrigatoriedade é regra de validação do schema de cadastro público, não do
banco).

Revision ID: 0034
Revises: 0033
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("telefone", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "telefone")
