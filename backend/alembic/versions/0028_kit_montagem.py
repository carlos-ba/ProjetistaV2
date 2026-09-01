"""Cria tabelas selante_montagem, rebite, parafuso_bucha + 2 campos em configuracao_montagem

Segunda parte do desmembramento do kit de montagem (a primeira, tabela
perfil_metalico, foi a migration 0027). Selante/rebite/parafuso+bucha são
cadastros simples (sempre o mesmo produto, só varia fabricante/embalagem —
sem seleção por especificação, ver DESIGN_KIT_MONTAGEM_2026-09-01.md).

Os 2 campos novos em configuracao_montagem alimentam a seleção automática de
perfil (largura_aba_padrao_mm) e o cálculo de selante (rendimento por
embalagem) — mesmo mecanismo de preferência configurável por perfil de
montagem que já existe pros outros campos desta tabela.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

# tipo_item novos → mesma classificação "Acessórios de Montagem" (id=5, seed da
# migration 0017) que a linha única "Acessórios de Montagem (Kit)" já usava —
# são a decomposição dela, não uma categoria nova.
NOVOS_TIPO_ITEM = [
    "perfil_angulo_externo",
    "perfil_angulo_interno",
    "perfil_u",
    "perfil_manual",
    "selante_montagem",
    "rebite",
    "parafuso_bucha",
]


def upgrade() -> None:
    op.create_table(
        "selante_montagem",
        sa.Column("id",                sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fabricante_id",     sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante", sa.String(50),  nullable=False),
        sa.Column("descricao",         sa.String(200), nullable=False),
        sa.Column("tipo_embalagem",    sa.String(20),  nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )
    op.create_table(
        "rebite",
        sa.Column("id",                sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fabricante_id",     sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante", sa.String(50),  nullable=False),
        sa.Column("descricao",         sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )
    op.create_table(
        "parafuso_bucha",
        sa.Column("id",                sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fabricante_id",     sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante", sa.String(50),  nullable=False),
        sa.Column("descricao",         sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )
    op.add_column(
        "configuracao_montagem",
        sa.Column("largura_aba_padrao_mm", sa.Integer(), nullable=False, server_default="40"),
    )
    op.add_column(
        "configuracao_montagem",
        sa.Column("rendimento_selante_m_por_embalagem", sa.Numeric(6, 2), nullable=False, server_default="12.00"),
    )

    t_item = sa.table(
        "item_classificacao",
        sa.column("tipo_item", sa.String),
        sa.column("classificacao_id", sa.Integer),
    )
    op.bulk_insert(t_item, [{"tipo_item": t, "classificacao_id": 5} for t in NOVOS_TIPO_ITEM])


def downgrade() -> None:
    op.execute(
        "DELETE FROM item_classificacao WHERE tipo_item IN ("
        + ",".join(f"'{t}'" for t in NOVOS_TIPO_ITEM)
        + ")"
    )
    op.drop_column("configuracao_montagem", "rendimento_selante_m_por_embalagem")
    op.drop_column("configuracao_montagem", "largura_aba_padrao_mm")
    op.drop_table("parafuso_bucha")
    op.drop_table("rebite")
    op.drop_table("selante_montagem")
