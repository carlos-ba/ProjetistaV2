"""Cria tabelas fornecedor, cotacao e cotacao_item

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fornecedor",
        sa.Column("id",         sa.Integer(),    nullable=False, autoincrement=True),
        sa.Column("owner_id",   UUID(as_uuid=True), nullable=False),
        sa.Column("nome",       sa.String(150),  nullable=False),
        sa.Column("cnpj",       sa.String(18),   nullable=True),
        sa.Column("telefone",   sa.String(20),   nullable=True),
        sa.Column("email",      sa.String(150),  nullable=True),
        sa.Column("contato",    sa.String(100),  nullable=True),
        sa.Column("ativo",      sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["usuario.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_fornecedor_owner", "fornecedor", ["owner_id"])

    op.create_table(
        "cotacao",
        sa.Column("id",               UUID(as_uuid=True), nullable=False),
        sa.Column("codigo",           sa.String(30),   nullable=False),
        sa.Column("owner_id",         UUID(as_uuid=True), nullable=False),
        sa.Column("fornecedor_id",    sa.Integer(),    nullable=False),
        sa.Column("projeto_id",       UUID(as_uuid=True), nullable=True),
        sa.Column("nome_projeto",     sa.String(200),  nullable=True),
        sa.Column("status",           sa.String(20),   nullable=False, server_default="rascunho"),
        sa.Column("validade_dias",    sa.Integer(),    nullable=False, server_default="30"),
        sa.Column("data_recebimento", sa.String(30),   nullable=True),
        sa.Column("observacoes",      sa.Text(),       nullable=True),
        sa.Column("created_at",       sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
        sa.ForeignKeyConstraint(["owner_id"],      ["usuario.id"],   ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedor.id"]),
        sa.ForeignKeyConstraint(["projeto_id"],    ["projeto.id"],   ondelete="SET NULL"),
    )
    op.create_index("ix_cotacao_owner", "cotacao", ["owner_id"])

    op.create_table(
        "cotacao_item",
        sa.Column("id",                  sa.Integer(),      nullable=False, autoincrement=True),
        sa.Column("cotacao_id",          UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_item",           sa.String(30),     nullable=False),
        sa.Column("ref_id",              sa.Integer(),      nullable=True),
        sa.Column("descricao",           sa.String(250),    nullable=False),
        sa.Column("detalhe",             sa.String(250),    nullable=True),
        sa.Column("qtde",                sa.Numeric(12, 3), nullable=False, server_default="1"),
        sa.Column("unidade",             sa.String(10),     nullable=False, server_default="un"),
        sa.Column("preco_unitario",      sa.Numeric(12, 2), nullable=True),
        sa.Column("marca_modelo_cotado", sa.String(150),    nullable=True),
        sa.Column("prazo_entrega_dias",  sa.Integer(),      nullable=True),
        sa.Column("obs_fornecedor",      sa.String(250),    nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cotacao_id"], ["cotacao.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cotacao_item_cotacao", "cotacao_item", ["cotacao_id"])


def downgrade() -> None:
    op.drop_table("cotacao_item")
    op.drop_table("cotacao")
    op.drop_table("fornecedor")
