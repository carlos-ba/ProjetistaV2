"""Cria tabela cliente

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-27
"""
import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cliente',
        sa.Column('id',         pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('nome',       sa.String(200), nullable=False),
        sa.Column('cnpj',      sa.String(20),  nullable=True),
        sa.Column('contato',   sa.String(100), nullable=True),
        sa.Column('celular',   sa.String(30),  nullable=True),
        sa.Column('email',     sa.String(200), nullable=True),
        sa.Column('owner_id',  pg.UUID(as_uuid=True), sa.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_cliente_owner_id', 'cliente', ['owner_id'])


def downgrade():
    op.drop_index('ix_cliente_owner_id', table_name='cliente')
    op.drop_table('cliente')
