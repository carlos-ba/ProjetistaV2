"""Adiciona cotacao_item.qtde_cotada (quantidade que o fornecedor cotou)

Importação de PDF por IA: o painel de conferência passa a mostrar e permitir
ajustar a quantidade lida no PDF do fornecedor (que pode diferir da pedida por
embalagem/unidade). Coluna nullable, aditiva — nenhum dado existente é tocado.

Revision ID: 0043
Revises: 0042
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cotacao_item", sa.Column("qtde_cotada", sa.Numeric(12, 3), nullable=True))


def downgrade() -> None:
    op.drop_column("cotacao_item", "qtde_cotada")
