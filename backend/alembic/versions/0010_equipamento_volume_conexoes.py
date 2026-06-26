"""Adiciona volume_interno_kg, conexao_liquido e conexao_succao ao equipamento

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('equipamento', sa.Column('volume_interno_kg',  sa.Numeric(5, 2), nullable=True))
    op.add_column('equipamento', sa.Column('conexao_liquido',    sa.String(10),    nullable=True))
    op.add_column('equipamento', sa.Column('conexao_succao',     sa.String(10),    nullable=True))

    # Popula os modelos Elgin FL já cadastrados
    op.execute("""
        UPDATE equipamento SET
            volume_interno_kg = CASE modelo
                WHEN 'FL*017' THEN 1.1
                WHEN 'FL*018' THEN 1.3
                WHEN 'FL*028' THEN 1.7
                WHEN 'FL*031' THEN 1.9
                WHEN 'FL*039' THEN 2.2
                WHEN 'FL*048' THEN 2.7
                WHEN 'FL*053' THEN 3.2
                WHEN 'FL*065' THEN 3.5
                WHEN 'FL*086' THEN 4.5
                WHEN 'FL*096' THEN 5.0
                WHEN 'FL*114' THEN 5.9
                WHEN 'FL*129' THEN 6.6
            END,
            conexao_liquido = '1/2"',
            conexao_succao = CASE modelo
                WHEN 'FL*086' THEN '1.1/8"'
                WHEN 'FL*096' THEN '1.1/8"'
                WHEN 'FL*114' THEN '1.1/8"'
                WHEN 'FL*129' THEN '1.1/8"'
                ELSE '7/8"'
            END
        WHERE modelo IN (
            'FL*017','FL*018','FL*028','FL*031','FL*039','FL*048',
            'FL*053','FL*065','FL*086','FL*096','FL*114','FL*129'
        )
    """)


def downgrade() -> None:
    op.drop_column('equipamento', 'conexao_succao')
    op.drop_column('equipamento', 'conexao_liquido')
    op.drop_column('equipamento', 'volume_interno_kg')
