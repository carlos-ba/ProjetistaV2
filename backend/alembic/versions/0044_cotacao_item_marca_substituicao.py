"""cotacao_item: marca, código do fabricante e sinal de possível substituição

Achado na jornada do usuário (docs/analises/jornada-cotacao-card6-2026-10-08.md,
Achado 6): a coluna `marca_modelo_cotado` misturava três coisas — marca, código do
fabricante e produto diferente do pedido — e o Card 6 tratava toda marca como
"item substituto". Passa a guardar separado:
  - marca_cotada: só a marca (informação comum, editável, pode ir pra proposta)
  - codigo_fabricante_cotado: código do produto no fornecedor (uso interno/compra)
  - possivel_substituicao: sinal da IA de que o item cotado é realmente diferente
Todas nullable e aditivas — nenhum dado existente é tocado (cotações antigas ficam
com NULL e o frontend cai no `marca_modelo_cotado` como antes).

Revision ID: 0044
Revises: 0043
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cotacao_item", sa.Column("marca_cotada", sa.String(100), nullable=True))
    op.add_column("cotacao_item", sa.Column("codigo_fabricante_cotado", sa.String(100), nullable=True))
    op.add_column("cotacao_item", sa.Column("possivel_substituicao", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("cotacao_item", "possivel_substituicao")
    op.drop_column("cotacao_item", "codigo_fabricante_cotado")
    op.drop_column("cotacao_item", "marca_cotada")
