"""Adiciona identidade da proposta em empresa

Permite o técnico personalizar a proposta ao cliente com nome da firma,
logo e contato — 4 colunas nullable, sem retroatividade (proposta continua
igual pra quem não preencher). `proposta_nome` não reaproveita `empresa.nome`
de propósito: esse é o nome "oficial" da conta (usado no admin), enquanto
`proposta_nome` é um valor independente que qualquer membro pode editar,
sem abrir edição do nome da conta em si.

Revision ID: 0035
Revises: 0034
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("empresa", sa.Column("proposta_nome", sa.String(200), nullable=True))
    op.add_column("empresa", sa.Column("proposta_logo_base64", sa.Text(), nullable=True))
    op.add_column("empresa", sa.Column("proposta_contato_nome", sa.String(150), nullable=True))
    op.add_column("empresa", sa.Column("proposta_contato_telefone", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("empresa", "proposta_contato_telefone")
    op.drop_column("empresa", "proposta_contato_nome")
    op.drop_column("empresa", "proposta_logo_base64")
    op.drop_column("empresa", "proposta_nome")
