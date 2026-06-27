"""Adiciona qtde_metros em cotacao_item para tubos de cobre (m + kg)

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-27
"""
import sqlalchemy as sa
from alembic import op

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'cotacao_item',
        sa.Column('qtde_metros', sa.Numeric(12, 3), nullable=True,
                  comment='Metros de tubo (informativo) quando qtde está em kg'),
    )


def downgrade():
    op.drop_column('cotacao_item', 'qtde_metros')
