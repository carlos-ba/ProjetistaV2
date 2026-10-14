"""empresa.ia_descritivo_habilitado — libera a redação por IA do descritivo técnico

Trava por empresa, ligada pelo superadmin no painel Administração. Nasce desligada
pra todo mundo (beta fechado); se a funcionalidade se provar útil, passa a ser
habilitada para o plano premium. Diferente de `recursos_avancados_habilitados`,
esta trava será aplicada TAMBÉM no backend (cada geração custa uma chamada de IA).
Coluna booleana aditiva com default false — nenhum dado existente é tocado.

Revision ID: 0046
Revises: 0045
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresa",
        sa.Column("ia_descritivo_habilitado", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("empresa", "ia_descritivo_habilitado")
