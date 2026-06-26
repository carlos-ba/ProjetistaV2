"""Adiciona flags incluir_filtro, incluir_visor, incluir_gbc_entrada, incluir_gbc_saida

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('configuracao_montagem', sa.Column('incluir_filtro',      sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('configuracao_montagem', sa.Column('incluir_visor',       sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('configuracao_montagem', sa.Column('incluir_gbc_entrada', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('configuracao_montagem', sa.Column('incluir_gbc_saida',   sa.Boolean(), nullable=False, server_default='true'))


def downgrade():
    op.drop_column('configuracao_montagem', 'incluir_filtro')
    op.drop_column('configuracao_montagem', 'incluir_visor')
    op.drop_column('configuracao_montagem', 'incluir_gbc_entrada')
    op.drop_column('configuracao_montagem', 'incluir_gbc_saida')
