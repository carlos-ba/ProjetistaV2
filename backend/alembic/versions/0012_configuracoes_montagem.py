"""Tabela configuracao_montagem — perfis de montagem por usuário

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'configuracao_montagem',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('usuario_id', sa.UUID(), sa.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tipo_filtro', sa.String(10), nullable=False, server_default='solda'),
        sa.Column('tipo_visor', sa.String(10), nullable=False, server_default='solda'),
        sa.Column('trecho_vet_evap', sa.Numeric(5, 2), nullable=False, server_default='0.50'),
        sa.Column('trecho_evap_sifao', sa.Numeric(5, 2), nullable=False, server_default='0.50'),
        sa.Column('trecho_subida', sa.Numeric(5, 2), nullable=False, server_default='1.00'),
        sa.Column('trecho_sifao_gbc', sa.Numeric(5, 2), nullable=False, server_default='0.50'),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_configuracao_montagem_usuario', 'configuracao_montagem', ['usuario_id'])


def downgrade():
    op.drop_table('configuracao_montagem')
