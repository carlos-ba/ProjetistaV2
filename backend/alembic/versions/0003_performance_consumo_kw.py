"""performance_equipamento: renomeia consumo_w para consumo_kw

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "performance_equipamento",
        "consumo_w",
        new_column_name="consumo_kw",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )
    # Converter valores existentes de W para kW (divide por 1000)
    op.execute("""
        ALTER TABLE performance_equipamento
        ALTER COLUMN consumo_kw TYPE NUMERIC(8,3)
        USING consumo_kw::NUMERIC / 1000
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE performance_equipamento
        ALTER COLUMN consumo_kw TYPE INTEGER
        USING ROUND(consumo_kw * 1000)::INTEGER
    """)
    op.alter_column(
        "performance_equipamento",
        "consumo_kw",
        new_column_name="consumo_w",
        existing_type=sa.Numeric(8, 3),
        existing_nullable=True,
    )
