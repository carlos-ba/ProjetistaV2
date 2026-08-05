"""Fase A — multi-tenancy: tabela empresa e empresa_id nas tabelas escopadas

Passo 1 de 2: cria a entidade `empresa`, vincula o usuário a ela e adiciona
`empresa_id` (NULLABLE) às tabelas escopadas. Nada é preenchido aqui — o backfill
roda em seguida (scripts/backfill_empresa.py) e só depois as colunas viram NOT NULL
(migration 0021). Essa divisão em dois tempos permite migrar produção sem downtime
e sem quebrar o código antigo enquanto o deploy acontece.

Escopo passa a ser a EMPRESA; `owner_id` permanece como autor do registro (auditoria).

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-05
"""
import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None

# Tabelas que passam a ser escopadas por empresa
ESCOPADAS = ['projeto', 'cliente', 'fornecedor', 'cotacao', 'proposta_comercial', 'configuracao_montagem']


def upgrade():
    op.create_table(
        'empresa',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('plano', sa.String(30), nullable=False, server_default='trial',
                  comment='trial | tecnico | empresa'),
        sa.Column('status_assinatura', sa.String(20), nullable=False, server_default='ativa',
                  comment='ativa | suspensa | cancelada'),
        sa.Column('assinatura_inicio', sa.Date(), nullable=True),
        sa.Column('assinatura_fim', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Usuário pertence a uma empresa e tem um papel
    op.add_column('usuario', sa.Column('empresa_id', pg.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_usuario_empresa', 'usuario', 'empresa', ['empresa_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_usuario_empresa_id', 'usuario', ['empresa_id'])
    op.add_column('usuario', sa.Column('papel', sa.String(30), nullable=False, server_default='admin_empresa',
                                       comment='superadmin_icenexus | admin_empresa | membro'))

    # empresa_id nas tabelas escopadas (nullable até o backfill)
    for tabela in ESCOPADAS:
        op.add_column(tabela, sa.Column('empresa_id', pg.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(f'fk_{tabela}_empresa', tabela, 'empresa', ['empresa_id'], ['id'], ondelete='CASCADE')
        op.create_index(f'ix_{tabela}_empresa_id', tabela, ['empresa_id'])


def downgrade():
    for tabela in ESCOPADAS:
        op.drop_index(f'ix_{tabela}_empresa_id', table_name=tabela)
        op.drop_constraint(f'fk_{tabela}_empresa', tabela, type_='foreignkey')
        op.drop_column(tabela, 'empresa_id')

    op.drop_column('usuario', 'papel')
    op.drop_index('ix_usuario_empresa_id', table_name='usuario')
    op.drop_constraint('fk_usuario_empresa', 'usuario', type_='foreignkey')
    op.drop_column('usuario', 'empresa_id')

    op.drop_table('empresa')
