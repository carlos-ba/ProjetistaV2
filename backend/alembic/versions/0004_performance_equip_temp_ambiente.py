"""performance_equipamento: renomeia temp_condensacao para temp_ambiente

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Renomeia a coluna
    op.alter_column(
        "performance_equipamento",
        "temp_condensacao",
        new_column_name="temp_ambiente",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    # Recria a unique constraint com o novo nome de coluna
    op.drop_constraint("uq_performance_equipamento", "performance_equipamento")
    op.create_unique_constraint(
        "uq_performance_equipamento",
        "performance_equipamento",
        ["equipamento_id", "fluido", "temp_ambiente", "temp_evaporacao", "delta_t"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_performance_equipamento", "performance_equipamento")
    op.alter_column(
        "performance_equipamento",
        "temp_ambiente",
        new_column_name="temp_condensacao",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "uq_performance_equipamento",
        "performance_equipamento",
        ["equipamento_id", "fluido", "temp_condensacao", "temp_evaporacao", "delta_t"],
    )
