"""Campos de compressor/UC (achado importando o catálogo Bitzer Combat/
Combat+/BIG CDU) — sem análogo em evaporador, tudo opcional/informativo por
ora, nenhum Card consome ainda (mesmo padrão do peso/ruído do Mipal).

- `equipamento` ganha: volume_deslocado_m3h, potencia_nominal_hp,
  motor_ventilador_corrente_a, motor_ventilador_potencia_w,
  capacitor_marcha_especificacao (texto livre), resistencia_carter_especificacao
  (texto livre — formato varia demais entre modelos pra estruturar em campos
  numéricos sem perder informação), tanque_liquido_l.
- `equipamento_variante_eletrica` ganha: codigo_fabricante (SKU por variante
  de tensão — 1ª vez que o catálogo técnico guarda código de peça pra
  qualquer fabricante) e corrente_partida_a (LRA, ao lado do corrente_a/FLA
  já existente).

Revision ID: 0038
Revises: 0037
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("equipamento", sa.Column("volume_deslocado_m3h", sa.Numeric(6, 2), nullable=True))
    op.add_column("equipamento", sa.Column("potencia_nominal_hp", sa.Numeric(5, 2), nullable=True))
    op.add_column("equipamento", sa.Column("motor_ventilador_corrente_a", sa.Numeric(6, 2), nullable=True))
    op.add_column("equipamento", sa.Column("motor_ventilador_potencia_w", sa.Numeric(8, 2), nullable=True))
    op.add_column("equipamento", sa.Column("capacitor_marcha_especificacao", sa.String(50), nullable=True))
    op.add_column("equipamento", sa.Column("resistencia_carter_especificacao", sa.String(50), nullable=True))
    op.add_column("equipamento", sa.Column("tanque_liquido_l", sa.Numeric(6, 2), nullable=True))

    op.add_column("equipamento_variante_eletrica", sa.Column("codigo_fabricante", sa.String(30), nullable=True))
    op.add_column("equipamento_variante_eletrica", sa.Column("corrente_partida_a", sa.Numeric(6, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("equipamento_variante_eletrica", "corrente_partida_a")
    op.drop_column("equipamento_variante_eletrica", "codigo_fabricante")

    op.drop_column("equipamento", "tanque_liquido_l")
    op.drop_column("equipamento", "resistencia_carter_especificacao")
    op.drop_column("equipamento", "capacitor_marcha_especificacao")
    op.drop_column("equipamento", "motor_ventilador_potencia_w")
    op.drop_column("equipamento", "motor_ventilador_corrente_a")
    op.drop_column("equipamento", "potencia_nominal_hp")
    op.drop_column("equipamento", "volume_deslocado_m3h")
