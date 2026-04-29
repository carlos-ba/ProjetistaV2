"""schema_completo_v2

Revision ID: 0001
Revises:
Create Date: 2026-04-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- lookup tables (no FK dependencies) ---
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "fabricante",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "unidade_medida",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(50), nullable=False),
        sa.Column("sigla", sa.String(10), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tipo_produto_termico",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    # --- thermal profiles ---
    op.create_table(
        "perfil_produto_termico",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.Column("ponto_congelamento", sa.Numeric(5, 2), nullable=False),
        sa.Column("calor_especifico_acima_congelamento", sa.Numeric(6, 4), nullable=False),
        sa.Column("calor_latente_congelamento", sa.Numeric(6, 2), nullable=False),
        sa.Column("calor_especifico_abaixo_congelamento", sa.Numeric(6, 4), nullable=False),
        sa.Column("taxa_respiracao", sa.Numeric(10, 4), nullable=True),
        sa.Column("temperatura_conservacao", sa.Numeric(5, 2), nullable=True),
        sa.Column("umidade_relativa", sa.Numeric(5, 2), nullable=True),
        sa.Column("teor_agua", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo_produto_termico.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    # --- equipment ---
    op.create_table(
        "equipamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("fabricante_id", sa.Integer(), nullable=False),
        sa.Column("custo", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("unidade_medida_id", sa.Integer(), nullable=False),
        sa.Column("qtde_ventiladores", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("diametro_ventilador_mm", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vazao_ar_m3h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flecha_ar_m", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.ForeignKeyConstraint(["unidade_medida_id"], ["unidade_medida.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "performance_equipamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("equipamento_id", sa.Integer(), nullable=False),
        sa.Column("fluido", sa.String(20), nullable=False),
        sa.Column("temp_condensacao", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("temp_evaporacao", sa.Integer(), nullable=False),
        sa.Column("delta_t", sa.Numeric(4, 1), nullable=False, server_default="0"),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("consumo_w", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["equipamento_id"], ["equipamento.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipamento_id", "fluido", "temp_condensacao", "temp_evaporacao", "delta_t",
            name="uq_performance_equipamento",
        ),
    )

    # --- flow components ---
    op.create_table(
        "componente_tecnico",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("codigo_fabricante", sa.String(50), nullable=True),
        sa.Column("fabricante_id", sa.Integer(), nullable=False),
        sa.Column("conexao_entrada", sa.String(20), nullable=False),
        sa.Column("conexao_saida", sa.String(20), nullable=False),
        sa.Column("capacidade_nominal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("dados_especificos", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("custo", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "performance_componente",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("componente_id", sa.Integer(), nullable=False),
        sa.Column("fluido", sa.String(20), nullable=False),
        sa.Column("temp_evaporacao", sa.Integer(), nullable=False),
        sa.Column("temp_condensacao", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("capacidade_kcalh", sa.Float(), nullable=False),
        sa.Column("capacidade_min_kcalh", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["componente_id"], ["componente_tecnico.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "componente_id", "fluido", "temp_evaporacao", "temp_condensacao",
            name="uq_performance_componente",
        ),
    )

    # --- materials ---
    op.create_table(
        "material",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("fabricante_id", sa.Integer(), nullable=True),
        sa.Column("custo", sa.Numeric(10, 2), nullable=False),
        sa.Column("unidade_medida_id", sa.Integer(), nullable=False),
        sa.Column("diametro_conexao", sa.String(50), nullable=True),
        sa.Column("capacidade_nominal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("detalhes_tecnicos", sa.JSON(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
        sa.ForeignKeyConstraint(["unidade_medida_id"], ["unidade_medida.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- users ---
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # --- projects and calculations ---
    op.create_table(
        "projeto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("cliente", sa.String(200), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="rascunho"),
        sa.Column("dados_completos", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_projeto_created_at", "projeto", ["created_at"])
    op.create_index("idx_projeto_owner_id", "projeto", ["owner_id"])

    op.create_table(
        "calculo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("payload_entrada", sa.JSON(), nullable=False),
        sa.Column("resultado", sa.JSON(), nullable=False),
        sa.Column("versao_regra", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["projeto_id"], ["projeto.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_calculo_projeto_id", "calculo", ["projeto_id"])


def downgrade() -> None:
    op.drop_index("idx_calculo_projeto_id", table_name="calculo")
    op.drop_table("calculo")
    op.drop_index("idx_projeto_owner_id", table_name="projeto")
    op.drop_index("idx_projeto_created_at", table_name="projeto")
    op.drop_table("projeto")
    op.drop_table("usuario")
    op.drop_table("material")
    op.drop_table("performance_componente")
    op.drop_table("componente_tecnico")
    op.drop_table("performance_equipamento")
    op.drop_table("equipamento")
    op.drop_table("perfil_produto_termico")
    op.drop_table("tipo_produto_termico")
    op.drop_table("unidade_medida")
    op.drop_table("fabricante")
    op.drop_table("categoria")
