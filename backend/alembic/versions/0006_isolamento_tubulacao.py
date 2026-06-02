"""Cria tabela isolamento_tubulacao

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "isolamento_tubulacao",
        sa.Column("id",                    sa.Integer(),     nullable=False, autoincrement=True),
        sa.Column("fabricante_id",         sa.Integer(),     nullable=False),
        sa.Column("diametro_cu_mm",        sa.Numeric(6, 1), nullable=True),   # tubo cobre
        sa.Column("diametro_fe_mm",        sa.Numeric(6, 1), nullable=True),   # tubo aço (futuro)
        sa.Column("diametro_interno_min",  sa.Numeric(6, 1), nullable=True),   # furo mín do isolamento
        sa.Column("diametro_interno_max",  sa.Numeric(6, 1), nullable=True),   # furo máx do isolamento
        sa.Column("padrao",                sa.String(2),     nullable=False),   # D F H M R T
        sa.Column("referencia",            sa.String(20),    nullable=False),   # ex: F-22
        sa.Column("espessura_mm",          sa.Numeric(5, 1), nullable=False),   # espessura real
        sa.Column("custo",                 sa.Numeric(10,2), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.UniqueConstraint("fabricante_id", "padrao", "referencia",
                            name="uq_isolamento_tubulacao"),
    )


def downgrade() -> None:
    op.drop_table("isolamento_tubulacao")
