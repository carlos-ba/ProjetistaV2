"""Evolução do modelo de equipamento pra suportar catálogos mais ricos
(achado importando o catálogo Mipal Hd/Hdl400 Pro) — sem quebrar nenhum
cadastro existente (Elgin/Danfoss), todas as colunas/tabelas novas são
opcionais.

- `equipamento` ganha: tipo_motor (AC/EC — capacidade/vazão diferem entre
  os dois pro mesmo modelo físico), cotas mínimas pra check de encaixe
  futuro (comprimento/altura/profundidade), peso líquido, ruído (dBA),
  carga de refrigerante já publicada pelo fabricante, e referência opcional
  a um documento técnico externo.
- `performance_equipamento` ganha `usa_fator_correcao`: quando true, a
  capacidade gravada é só a do fluido de referência do fabricante (ex: R22)
  — o valor real por fluido é calculado na leitura via `fator_correcao_fluido`,
  em vez de gravar 1 linha por fluido (catálogo Mipal só mede em R-22).
- `fator_correcao_fluido`, `equipamento_variante_eletrica`,
  `equipamento_resistencia_degelo`, `biblioteca_tecnica`: tabelas novas,
  detalhe completo em `project_evolucao_dados_evaporador` na memória.

Revision ID: 0037
Revises: 0036
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biblioteca_tecnica",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fabricante_id", sa.Integer(), sa.ForeignKey("fabricante.id"), nullable=False),
        sa.Column("titulo", sa.String(150), nullable=False),
        sa.Column("link_url", sa.String(500), nullable=True),
        sa.Column("observacao", sa.String(300), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.add_column("equipamento", sa.Column("tipo_motor", sa.String(5), nullable=True))
    op.add_column("equipamento", sa.Column("comprimento_mm", sa.Integer(), nullable=True))
    op.add_column("equipamento", sa.Column("altura_mm", sa.Integer(), nullable=True))
    op.add_column("equipamento", sa.Column("profundidade_mm", sa.Integer(), nullable=True))
    op.add_column("equipamento", sa.Column("peso_liquido_kg", sa.Numeric(6, 2), nullable=True))
    op.add_column("equipamento", sa.Column("ruido_dba", sa.Integer(), nullable=True))
    op.add_column("equipamento", sa.Column("carga_refrigerante_kg", sa.Numeric(6, 3), nullable=True))
    op.add_column(
        "equipamento",
        sa.Column("biblioteca_tecnica_id", sa.Integer(), sa.ForeignKey("biblioteca_tecnica.id"), nullable=True),
    )
    # Sem constraint real no banco até aqui (só checagem do importador) —
    # dado já entra deduplicado por (modelo, fabricante_id, categoria_id)
    # via upsert, então tipo_motor=NULL em todo mundo não cria colisão nova.
    op.create_unique_constraint(
        "uq_equipamento_modelo_fabricante_categoria_motor",
        "equipamento",
        ["modelo", "fabricante_id", "categoria_id", "tipo_motor"],
    )

    op.add_column(
        "performance_equipamento",
        sa.Column("usa_fator_correcao", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "fator_correcao_fluido",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fabricante_id", sa.Integer(), sa.ForeignKey("fabricante.id"), nullable=False),
        sa.Column("fluido_base", sa.String(20), nullable=False),
        sa.Column("fluido", sa.String(20), nullable=False),
        sa.Column("fator", sa.Numeric(5, 4), nullable=False),
        sa.UniqueConstraint("fabricante_id", "fluido_base", "fluido", name="uq_fator_correcao_fluido"),
    )

    op.create_table(
        "equipamento_variante_eletrica",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("equipamento_id", sa.Integer(), sa.ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tensao", sa.String(20), nullable=False),
        sa.Column("fase", sa.Integer(), nullable=False),
        sa.Column("frequencia_hz", sa.Integer(), nullable=True),
        sa.Column("vazao_ar_m3h", sa.Integer(), nullable=True),
        sa.Column("potencia_w", sa.Numeric(8, 2), nullable=True),
        sa.Column("corrente_a", sa.Numeric(6, 2), nullable=True),
        sa.UniqueConstraint(
            "equipamento_id", "tensao", "fase", "frequencia_hz",
            name="uq_equipamento_variante_eletrica"
        ),
    )

    op.create_table(
        "equipamento_resistencia_degelo",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("equipamento_id", sa.Integer(), sa.ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tensao", sa.String(20), nullable=False),
        sa.Column("potencia_individual_w", sa.Numeric(8, 2), nullable=False),
        sa.Column("corrente_a", sa.Numeric(6, 2), nullable=False),
        sa.Column("consumo_nao_equilibrado", sa.Boolean(), nullable=False, server_default="false"),
        sa.UniqueConstraint("equipamento_id", "tensao", name="uq_equipamento_resistencia_degelo"),
    )


def downgrade() -> None:
    op.drop_table("equipamento_resistencia_degelo")
    op.drop_table("equipamento_variante_eletrica")
    op.drop_table("fator_correcao_fluido")

    op.drop_column("performance_equipamento", "usa_fator_correcao")

    op.drop_constraint(
        "uq_equipamento_modelo_fabricante_categoria_motor", "equipamento", type_="unique"
    )
    op.drop_column("equipamento", "biblioteca_tecnica_id")
    op.drop_column("equipamento", "carga_refrigerante_kg")
    op.drop_column("equipamento", "ruido_dba")
    op.drop_column("equipamento", "peso_liquido_kg")
    op.drop_column("equipamento", "profundidade_mm")
    op.drop_column("equipamento", "altura_mm")
    op.drop_column("equipamento", "comprimento_mm")
    op.drop_column("equipamento", "tipo_motor")

    op.drop_table("biblioteca_tecnica")
