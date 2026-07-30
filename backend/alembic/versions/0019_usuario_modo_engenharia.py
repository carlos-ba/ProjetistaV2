"""Adiciona modo_engenharia no usuário (app só como seleção/lista, sem orçamento)

Preferência por usuário: quando ativa, o app funciona como gestor de engenharia —
Cards 1–5 (dimensionamento) + exportação da lista em Excel, sem a jornada comercial
(cotação, proposta, cliente, margens). Coluna booleana com default False (nenhum
usuário existente muda de comportamento).

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-29
"""
import sqlalchemy as sa
from alembic import op

revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'usuario',
        sa.Column('modo_engenharia', sa.Boolean(), nullable=False,
                  server_default=sa.false(),
                  comment='Se True, app opera só como seleção/lista de engenharia (sem orçamento)'),
    )


def downgrade():
    op.drop_column('usuario', 'modo_engenharia')
