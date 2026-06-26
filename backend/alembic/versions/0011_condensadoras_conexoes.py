"""Preenche conexao_liquido e conexao_succao nas condensadoras Elgin ES+

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-26
"""
from alembic import op

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    # Pequenas (até 350): 3/8" líquido, 5/8" sucção
    pequenas = [
        'ES+M2150%', 'ES+M2200%', 'ES+M2300%', 'ES+M2350%',
        'ES+M4150%', 'ES+M4200%', 'ES+M4250%', 'ES+M4300%', 'ES+M4350%',
        'ES+B4130%', 'ES+B4150%', 'ES+B4200%', 'ES+B4250%', 'ES+B4300%', 'ES+B4350%',
        'ES+E4130%', 'ES+E4150%', 'ES+E4200%', 'ES+E4300%', 'ES+E4350%',
    ]
    # Médias/grandes (375+): 1/2" líquido, 3/4" sucção
    grandes = [
        'ES+M2400%', 'ES+M2500%', 'ES+M2600%',
        'ES+M4375%', 'ES+M4400%', 'ES+M4500%', 'ES+M4550%', 'ES+M4600%',
        'ES+B4400%', 'ES+B4500%',
        'ES+E4400%', 'ES+E4450%', 'ES+E4500%', 'ES+E4600%',
        'ES+L4450%', 'ES+L4500%', 'ES+L4600%',
    ]

    for padrao in pequenas:
        op.execute(f"""
            UPDATE equipamento
            SET conexao_liquido = '3/8"', conexao_succao = '5/8"'
            WHERE modelo LIKE '{padrao}' AND conexao_liquido IS NULL
        """)

    for padrao in grandes:
        op.execute(f"""
            UPDATE equipamento
            SET conexao_liquido = '1/2"', conexao_succao = '3/4"'
            WHERE modelo LIKE '{padrao}' AND conexao_liquido IS NULL
        """)


def downgrade():
    op.execute("""
        UPDATE equipamento
        SET conexao_liquido = NULL, conexao_succao = NULL
        WHERE modelo LIKE 'ES+%'
    """)
