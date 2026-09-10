"""Perfil T (sustentação do teto dividido pela auto-portância) + Barra Roscada 3/8

Acessórios novos pro fix de 2026-09-10 (painéis de teto divididos quando a
largura da câmara excede a auto-portância do painel): o Perfil T sustenta
as juntas internas entre os pedaços de teto; a Barra Roscada 3/8 sustenta
o próprio Perfil T. Pedido do usuário, cadastro simples (mesmo padrão de
SelanteMontagem/Rebite/ParafusoBucha, migration 0028).

Perfil T entra na tabela `perfil_metalico` já existente (tipo="T", genérica
o suficiente: medida_1=espessura da alma, medida_2=base, medida_3=alma/
altura, comprimento). Barra Roscada é uma tabela nova, `barra_roscada_
perfil_t`, mesmo molde de Rebite/ParafusoBucha.

Fabricante MBP Isoblock (mesma linha Easyfrigo já cadastrada em 0029) —
descrição do fornecedor confirmada pelo usuário: "PERFIL T ALUMINIO BRANCO
3X80X40X6000MM". Nenhum código de fabricante foi fornecido pra nenhum dos
2 itens — usados códigos internos placeholder (formato claramente distinto
dos códigos reais MBP, tipo "PIxxxxxxxxxxxx", pra não confundir com peça
catalogada de verdade) até o usuário confirmar o código real.

Revision ID: 0040
Revises: 0039
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None

FABRICANTE_MBP = "MBP Isoblock"

# codigo_fabricante placeholder — sem código real informado ainda (ver nota acima)
PERFIL_T_CODIGO = "PLACEHOLDER-PERFIL-T-3X80X40-6000"
PERFIL_T_DESCRICAO_ORIGINAL = "PERFIL T ALUMINIO BRANCO 3X80X40X6000MM"
BARRA_ROSCADA_CODIGO = "PLACEHOLDER-BARRA-ROSCADA-38-PERFIL-T"
BARRA_ROSCADA_DESCRICAO = "Cj Barra Roscada 3/8 + Suporte Trava Perfil T 1000mm"

NOVOS_TIPO_ITEM = ["perfil_t", "barra_roscada_perfil_t"]


def _get_or_create_fabricante_id(conn, nome: str) -> int:
    conn.execute(
        sa.text("INSERT INTO fabricante (nome) VALUES (:nome) ON CONFLICT (nome) DO NOTHING"),
        {"nome": nome},
    )
    return conn.execute(
        sa.text("SELECT id FROM fabricante WHERE nome = :nome"), {"nome": nome}
    ).scalar_one()


def upgrade() -> None:
    op.create_table(
        "barra_roscada_perfil_t",
        sa.Column("id",                sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fabricante_id",     sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante", sa.String(50),  nullable=False),
        sa.Column("descricao",         sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )

    conn = op.get_bind()
    fabricante_id = _get_or_create_fabricante_id(conn, FABRICANTE_MBP)

    t_perfil = sa.table(
        "perfil_metalico",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("tipo", sa.String),
        sa.column("medida_1_mm", sa.Integer),
        sa.column("medida_2_mm", sa.Integer),
        sa.column("medida_3_mm", sa.Integer),
        sa.column("comprimento_mm", sa.Integer),
        sa.column("descricao_original", sa.String),
    )
    op.bulk_insert(t_perfil, [{
        "fabricante_id": fabricante_id,
        "codigo_fabricante": PERFIL_T_CODIGO,
        "tipo": "T",
        "medida_1_mm": 3,      # espessura da alma
        "medida_2_mm": 80,     # base do T
        "medida_3_mm": 40,     # alma (altura) do T
        "comprimento_mm": 6000,
        "descricao_original": PERFIL_T_DESCRICAO_ORIGINAL,
    }])

    t_barra = sa.table(
        "barra_roscada_perfil_t",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("descricao", sa.String),
    )
    op.bulk_insert(t_barra, [{
        "fabricante_id": fabricante_id,
        "codigo_fabricante": BARRA_ROSCADA_CODIGO,
        "descricao": BARRA_ROSCADA_DESCRICAO,
    }])

    t_item = sa.table(
        "item_classificacao",
        sa.column("tipo_item", sa.String),
        sa.column("classificacao_id", sa.Integer),
    )
    op.bulk_insert(t_item, [{"tipo_item": t, "classificacao_id": 5} for t in NOVOS_TIPO_ITEM])


def downgrade() -> None:
    conn = op.get_bind()
    op.execute(
        "DELETE FROM item_classificacao WHERE tipo_item IN ("
        + ",".join(f"'{t}'" for t in NOVOS_TIPO_ITEM)
        + ")"
    )
    conn.execute(sa.text("DELETE FROM perfil_metalico WHERE codigo_fabricante = :cod"), {"cod": PERFIL_T_CODIGO})
    op.drop_table("barra_roscada_perfil_t")
