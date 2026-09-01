"""Cria tabela perfil_metalico

Catálogo global de perfis metálicos (ângulo interno/externo, liso, U, Z) usados
na montagem do gabinete — hoje representados só como uma linha genérica
"Acessórios de Montagem (Kit)" em m², sem decomposição real. codigo_fabricante
preserva o código bruto do fornecedor (rastreabilidade pro pedido de compra);
tipo + medida_1/2/3_mm + comprimento_mm são o padrão agnóstico de fabricante
que a seleção usa (mesmo molde de painel_frigorifico/componente_tecnico).

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfil_metalico",
        sa.Column("id",                  sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fabricante_id",       sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante",   sa.String(50),  nullable=False),
        sa.Column("tipo",                sa.String(30),  nullable=False),
        sa.Column("medida_1_mm",         sa.Integer(),   nullable=False),
        sa.Column("medida_2_mm",         sa.Integer(),   nullable=True),
        sa.Column("medida_3_mm",         sa.Integer(),   nullable=True),
        sa.Column("comprimento_mm",      sa.Integer(),   nullable=False),
        sa.Column("descricao_original",  sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.UniqueConstraint(
            "fabricante_id", "codigo_fabricante",
            name="uq_perfil_metalico_fabricante_codigo"
        ),
    )


def downgrade() -> None:
    op.drop_table("perfil_metalico")
