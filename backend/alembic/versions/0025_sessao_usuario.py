"""Cria tabela sessao_usuario — limite de sessões simultâneas + logout real

Base de infraestrutura para as três decisões do DESIGN_LIMITE_SESSOES_2026-08-16.md:
limite de 2 sessões simultâneas por usuário, logout que revoga de verdade no servidor
(hoje só limpa o localStorage do navegador) e métrica de IPs distintos/dia no admin.

Uma linha por sessão ativa. Login cria; logout, expiração do refresh ou estouro do
limite revoga (revogada_em preenchido). O id da linha vai embutido como claim `sid`
no access e no refresh token — é o elo entre o token que o navegador carrega e a
linha que o banco controla.

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-19
"""
import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sessao_usuario',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('usuario_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('ultimo_uso_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('revogada_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_foreign_key('fk_sessao_usuario_usuario', 'sessao_usuario', 'usuario',
                           ['usuario_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_sessao_usuario_usuario_id', 'sessao_usuario', ['usuario_id'])


def downgrade():
    op.drop_index('ix_sessao_usuario_usuario_id', table_name='sessao_usuario')
    op.drop_constraint('fk_sessao_usuario_usuario', 'sessao_usuario', type_='foreignkey')
    op.drop_table('sessao_usuario')
