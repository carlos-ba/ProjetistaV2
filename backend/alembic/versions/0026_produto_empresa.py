"""Cria tabela produto_empresa — lista de preços/catálogo privado por empresa (Fase B)

Base da Fase B (DESIGN_MULTITENANCY_ASSINATURA_2026-07-28.md): cada empresa pode ter
sua própria lista de preços, usada no orçamento em vez do preço global do catálogo
técnico (que passa a ser só especificação, sem preço). `ref_global`/`tipo_catalogo`
são metadado opcional (útil pra uma futura UI de busca no catálogo global) — o
casamento de preço em si é por descrição normalizada (ver `app/core/matching.py`),
já que nem todo item do orçamento carrega um id estável (painéis, portas, materiais
extras do gabinete não têm `ref_id` no payload hoje).

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-20
"""
import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'produto_empresa',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('empresa_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('descricao', sa.String(250), nullable=False),
        sa.Column('codigo_interno', sa.String(50), nullable=True),
        sa.Column('unidade', sa.String(10), nullable=False, server_default='un'),
        sa.Column('preco', sa.Numeric(10, 2), nullable=False),
        sa.Column('tipo_catalogo', sa.String(20), nullable=True,
                   comment="'material' | 'equipamento' — qual tabela ref_global referencia"),
        sa.Column('ref_global', sa.Integer(), nullable=True,
                   comment='id em Material/Equipamento — metadado pra UI, não é chave de casamento'),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_foreign_key('fk_produto_empresa_empresa', 'produto_empresa', 'empresa',
                           ['empresa_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_produto_empresa_empresa_id', 'produto_empresa', ['empresa_id'])


def downgrade():
    op.drop_index('ix_produto_empresa_empresa_id', table_name='produto_empresa')
    op.drop_constraint('fk_produto_empresa_empresa', 'produto_empresa', type_='foreignkey')
    op.drop_table('produto_empresa')
