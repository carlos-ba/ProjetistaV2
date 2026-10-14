"""empresa.proposta_crea — CREA do engenheiro responsável pela proposta

Campo opcional da Identidade da Proposta (Configurações): aparece abaixo do nome do
responsável no bloco "Aprovação e Aceite" da proposta; em branco, não aparece nada.
Coluna nullable e aditiva — nenhum dado existente é tocado.

Revision ID: 0045
Revises: 0044
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("empresa", sa.Column("proposta_crea", sa.String(60), nullable=True))


def downgrade() -> None:
    op.drop_column("empresa", "proposta_crea")
