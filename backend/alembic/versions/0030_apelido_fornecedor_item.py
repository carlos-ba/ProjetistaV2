"""Cria tabela apelido_fornecedor_item — apelidos aprendidos por fornecedor

Primeira parte da importação de cotação em PDF (ver
DESIGN_IMPORTACAO_PDF_COTACAO_2026-09-01.md). A tabela guarda o "regime
permanente" do casamento híbrido: IA só resolve o cold start (termo nunca
visto daquele fornecedor); uma vez o humano confirmando na tela de
conferência, o par (fornecedor_id, termo_fornecedor) vira lookup direto —
sem IA — nas próximas cotações do mesmo fornecedor.

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apelido_fornecedor_item",
        sa.Column("id",               sa.Integer(),   nullable=False, autoincrement=True),
        sa.Column("fornecedor_id",    sa.Integer(),   nullable=False),
        sa.Column("empresa_id",       sa.Uuid(),      nullable=False),
        sa.Column("termo_fornecedor", sa.String(200), nullable=False),
        sa.Column("nosso_ref_id",     sa.Integer(),   nullable=True),
        sa.Column("nosso_tipo_item",  sa.String(30),  nullable=False),
        sa.Column("nosso_descricao",  sa.String(250), nullable=False),
        sa.Column("created_at",       sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("fornecedor_id", "termo_fornecedor", name="uq_apelido_fornecedor_termo"),
    )
    op.create_index(
        "ix_apelido_fornecedor_item_fornecedor",
        "apelido_fornecedor_item",
        ["fornecedor_id"],
    )


def downgrade() -> None:
    op.drop_table("apelido_fornecedor_item")
