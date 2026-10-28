"""empresa.lead_tratado_em — checkpoint comercial do trial novo (painel Administração)

Controle interno do superadmin: empresa em trial nasce com o campo vazio ("não tratada",
bolinha vermelha) e só o clique manual dele preenche (verde). Não altera assinatura nem
nada que o cliente enxergue. Ver specs/001-sinalizador-trial-novo/spec.md.

Coluna opcional, aditiva. O único UPDATE preenche a coluna nova nas empresas JÁ existentes
(valor "agora"), para que nenhuma apareça pendente por causa desta mudança — o sinalizador
vale só para cadastros daqui para frente. Nenhum dado existente é alterado ou removido.

Revision ID: 0047
Revises: 0046
Create Date: 2026-10-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("empresa", sa.Column("lead_tratado_em", sa.DateTime(), nullable=True))
    op.execute("UPDATE empresa SET lead_tratado_em = now() WHERE lead_tratado_em IS NULL")


def downgrade() -> None:
    op.drop_column("empresa", "lead_tratado_em")
