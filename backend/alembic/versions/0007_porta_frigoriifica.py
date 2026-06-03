"""Cria tabela porta_frigoriifica

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "porta_frigoriifica",
        sa.Column("id",            sa.Integer(),     nullable=False, autoincrement=True),
        sa.Column("fabricante_id", sa.Integer(),     nullable=True),   # opcional
        sa.Column("descricao",     sa.String(150),   nullable=False),
        sa.Column("tipo",          sa.String(30),    nullable=False),   # giratoria | deslizante | rapida
        sa.Column("largura_mm",    sa.Integer(),     nullable=False),
        sa.Column("altura_mm",     sa.Integer(),     nullable=False),
        sa.Column("espessura_mm",  sa.Integer(),     nullable=False),
        sa.Column("classificacao", sa.String(30),    nullable=False),   # resfriados | congelada | ultra-congelada
        sa.Column("abertura",      sa.String(20),    nullable=True),    # direita | esquerda | ambas | automatica
        sa.Column("batente",       sa.String(10),    nullable=True),    # 3B | 4B | etc
        sa.Column("soleira",       sa.Boolean(),     nullable=False, server_default="false"),
        sa.Column("custo",         sa.Numeric(10,2), nullable=False, server_default="0"),
        sa.Column("observacao",    sa.String(255),   nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )


def downgrade() -> None:
    op.drop_table("porta_frigoriifica")
