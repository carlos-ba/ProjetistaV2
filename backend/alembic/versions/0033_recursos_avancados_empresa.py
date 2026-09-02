"""Adiciona empresa.recursos_avancados_habilitados

Trava opcional pro superadmin liberar "Classificação de Itens" e "Catálogo
de Preços" por exceção — nascem desligados pra toda empresa (não há
usuário empresa em produção ainda, então não precisa de grandfathering pra
nenhum cliente existente). Sem gate no backend de propósito, só esconde o
menu no frontend — decisão consciente do usuário pra não arriscar nada nas
rotas de leitura já em produção (GET /classificacoes e
GET /produto-empresa/mapa-precos são usadas pelo Card 6 de qualquer
usuário, travar ali quebraria o orçamento).

Revision ID: 0033
Revises: 0032
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresa",
        sa.Column("recursos_avancados_habilitados", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("empresa", "recursos_avancados_habilitados")
