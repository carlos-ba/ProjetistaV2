"""Cria tabela painel_frigorifico

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "painel_frigorifico",
        sa.Column("id",                sa.Integer(),     nullable=False, autoincrement=True),
        sa.Column("produto",           sa.String(100),   nullable=False),
        sa.Column("fabricante_id",     sa.Integer(),     nullable=False),
        sa.Column("nucleo",            sa.String(10),    nullable=False),
        sa.Column("espessura_mm",      sa.Integer(),     nullable=False),
        sa.Column("largura_mm",        sa.Integer(),     nullable=False),
        sa.Column("comprimento_max_m", sa.Numeric(5,2),  nullable=True),
        sa.Column("auto_portancia_mm", sa.Integer(),     nullable=True),
        sa.Column("peso_kg_m2",        sa.Numeric(6,3),  nullable=True),
        sa.Column("u_global",          sa.Numeric(6,4),  nullable=False),
        sa.Column("custo",             sa.Numeric(10,2), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.UniqueConstraint(
            "fabricante_id", "nucleo", "espessura_mm", "largura_mm",
            name="uq_painel_frigorifico"
        ),
    )


def downgrade() -> None:
    op.drop_table("painel_frigorifico")
