"""Amplia cotacao_item.obs_fornecedor de 250 para 500 caracteres

Achado testando a importação de PDF por IA (0030): explicações de possível
substituição geradas pela IA passam fácil dos 250 caracteres pensados
originalmente pra uma anotação manual curta digitada pelo fornecedor na
planilha. Amplia sem quebrar nada — só aumenta o limite, dado existente
continua válido.

Revision ID: 0031
Revises: 0030
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("cotacao_item", "obs_fornecedor", type_=sa.String(500))


def downgrade() -> None:
    op.alter_column("cotacao_item", "obs_fornecedor", type_=sa.String(250))
