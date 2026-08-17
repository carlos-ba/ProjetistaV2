"""Cria tabela embalagem_fluido e semeia dados de teste (R404A)

Catálogo de tamanhos de embalagem descartável de fluido refrigerante, usado
no Card 6 pra converter a carga estimada em kg numa peça comprável (N
cilindros de X kg). Só R404A tem dados reais de teste por enquanto — os
demais fluidos ficam sem sugestão até o cadastro real ser levantado (ver
DESIGN_EMBALAGEM_FLUIDO_2026-08-17.md).

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-17
"""
import sqlalchemy as sa
from alembic import op

revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'embalagem_fluido',
        sa.Column('id',      sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('fluido',  sa.String(20), nullable=False),
        sa.Column('peso_kg', sa.Float(),    nullable=False),
    )

    tabela = sa.table(
        'embalagem_fluido',
        sa.column('fluido',  sa.String),
        sa.column('peso_kg', sa.Float),
    )
    op.bulk_insert(tabela, [
        {'fluido': 'R404A', 'peso_kg': 10.9},
        {'fluido': 'R404A', 'peso_kg': 0.7},
    ])


def downgrade():
    op.drop_table('embalagem_fluido')
