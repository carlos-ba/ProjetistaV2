"""Corrige capacidades R404A da VET Danfoss T2

As linhas R404A eram cópia da tabela R22 (superestimadas ~55%), fazendo a VET
sair subdimensionada em projetos R404A. Valores corrigidos extraídos do
CoolSelector®2 em 2026-07-10, condição: T.Cond 45°C, sub-resfriamento 2K,
superaquecimento útil 5K. Capacidade mínima = 25% da nominal (padrão Danfoss).

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-10
"""
from alembic import op

revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None

# T.Evap: +5, 0, -5, -10, -15, -20, -25, -30  (kcal/h, nominal)
TEMPS = [5, 0, -5, -10, -15, -20, -25, -30]
R404A = {
    'T2 - X': [546.6, 545.2, 538.0, 526.1, 510.4, 491.4, 469.5, 444.8],
    'T2 - 0': [1093, 1060, 1009, 945.4, 873.3, 796.4, 717.6, 639.2],
    'T2 - 1': [2155, 2001, 1820, 1627, 1437, 1256, 1089, 939.0],
    'T2 - 2': [2944, 2639, 2321, 2017, 1740, 1492, 1276, 1087],
    'T2 - 3': [5044, 4501, 3947, 3425, 2951, 2532, 2164, 1843],
    'T2 - 4': [7577, 6770, 5931, 5128, 4396, 3752, 3196, 2721],
    'T2 - 5': [10550, 9295, 8017, 6838, 5805, 4923, 4179, 3553],
    'T2 - 6': [12430, 10880, 9351, 7962, 6757, 5734, 4872, 4146],
}


def _aplicar(valores_por_modelo):
    for modelo, caps in valores_por_modelo.items():
        for te, cap in zip(TEMPS, caps):
            op.execute(
                f"""
                UPDATE performance_componente pc
                SET capacidade_kcalh = {cap:.2f},
                    capacidade_min_kcalh = {cap * 0.25:.2f}
                FROM componente_tecnico ct, categoria c
                WHERE pc.componente_id = ct.id
                  AND ct.categoria_id = c.id
                  AND c.nome LIKE 'V%lvula de Expans%'
                  AND ct.modelo = '{modelo}'
                  AND pc.fluido = 'R404A'
                  AND pc.temp_evaporacao = {te}
                """
            )


def upgrade():
    _aplicar(R404A)


def downgrade():
    # Estado anterior: R404A era cópia dos valores R22 (comportamento legado)
    op.execute(
        """
        UPDATE performance_componente pc
        SET capacidade_kcalh = r22.capacidade_kcalh,
            capacidade_min_kcalh = r22.capacidade_min_kcalh
        FROM performance_componente r22, componente_tecnico ct, categoria c
        WHERE pc.componente_id = ct.id
          AND ct.categoria_id = c.id
          AND c.nome LIKE 'V%lvula de Expans%'
          AND pc.fluido = 'R404A'
          AND r22.componente_id = pc.componente_id
          AND r22.fluido = 'R22'
          AND r22.temp_evaporacao = pc.temp_evaporacao
        """
    )
