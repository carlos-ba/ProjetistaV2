"""Cria tabela catalogo_generico + seed dos 3 itens da barreira de vapor

Cadastro genérico pra itens simples (sem seleção por especificação, só varia
fabricante/embalagem) — mesmo conceito de selante_montagem/rebite/
parafuso_bucha (migration 0028), mas numa tabela só, compartilhada por
`tipo_item`, pra não abrir uma tabela nova a cada item descoberto (essa é a
2ª leva desse tipo de cadastro; a 1ª foi o kit de montagem). As 3 tabelas
antigas continuam como estão — só os itens novos entram aqui.

Seed: os 3 itens da barreira de vapor (Card 1, piso convencional), fórmulas
e códigos confirmados pelo usuário com quem elaborou a planilha de
referência (VALFIM) — fabricante "Genérico" (id 14), sem fornecedor
específico definido, mesmo padrão já usado pro kit de montagem.

Revision ID: 0032
Revises: 0031
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None

NOVOS_TIPO_ITEM = ["lona_val_film", "fita_branca", "lona"]
FABRICANTE_GENERICO_ID = 14


def upgrade() -> None:
    op.create_table(
        "catalogo_generico",
        sa.Column("id",                sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("tipo_item",         sa.String(50),  nullable=False),
        sa.Column("fabricante_id",     sa.Integer(),   nullable=False),
        sa.Column("codigo_fabricante", sa.String(50),  nullable=False),
        sa.Column("descricao",         sa.String(200), nullable=False),
        sa.Column("tipo_embalagem",    sa.String(20),  nullable=True),
        sa.Column("observacao",        sa.String(500), nullable=True),
        sa.Column("ativo",             sa.Boolean(),   nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fabricante_id"], ["fabricante.id"]),
    )
    op.create_index("ix_catalogo_generico_tipo_item", "catalogo_generico", ["tipo_item"])

    t_item = sa.table(
        "item_classificacao",
        sa.column("tipo_item", sa.String),
        sa.column("classificacao_id", sa.Integer),
    )
    op.bulk_insert(t_item, [{"tipo_item": t, "classificacao_id": 3} for t in NOVOS_TIPO_ITEM])

    t_catalogo = sa.table(
        "catalogo_generico",
        sa.column("tipo_item", sa.String),
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("descricao", sa.String),
        sa.column("tipo_embalagem", sa.String),
        sa.column("observacao", sa.String),
    )
    op.bulk_insert(t_catalogo, [
        {
            "tipo_item": "lona_val_film", "fabricante_id": FABRICANTE_GENERICO_ID,
            "codigo_fabricante": "200000111", "descricao": "Lona Val Film",
            "tipo_embalagem": "rolo",
            "observacao": "Rolo com 3m de largura, peso por metro linear de 0,242kg",
        },
        {
            "tipo_item": "fita_branca", "fabricante_id": FABRICANTE_GENERICO_ID,
            "codigo_fabricante": "200000484", "descricao": "Fita Branca",
            "tipo_embalagem": "rolo", "observacao": None,
        },
        {
            "tipo_item": "lona", "fabricante_id": FABRICANTE_GENERICO_ID,
            "codigo_fabricante": "200000525", "descricao": "Lona",
            "tipo_embalagem": None, "observacao": None,
        },
    ])


def downgrade() -> None:
    op.execute(
        "DELETE FROM item_classificacao WHERE tipo_item IN ("
        + ",".join(f"'{t}'" for t in NOVOS_TIPO_ITEM)
        + ")"
    )
    op.drop_index("ix_catalogo_generico_tipo_item", table_name="catalogo_generico")
    op.drop_table("catalogo_generico")
