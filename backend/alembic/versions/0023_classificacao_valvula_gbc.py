"""Classificação para Válvula de Bloqueio (GBC)

Os toggles GBC Entrada/Saída do Card 5 nunca lançavam um item próprio na
lista de peças — só alteravam o texto de uma redução que já existia,
então ligar/desligar o toggle não mudava nada visível no Card 6. Agora o
serviço de cavalete lança uma válvula de bloqueio (esfera/globo) por lado,
na bitola da linha correspondente; esta migration cadastra a classificação
para que esses itens não caiam em "A classificar".

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-17
"""
import sqlalchemy as sa
from alembic import op

revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None


def upgrade():
    t_class = sa.table('classificacao_item',
                       sa.column('id', sa.Integer), sa.column('nome', sa.String),
                       sa.column('bloco_id', sa.Integer), sa.column('ordem', sa.Integer))
    t_item = sa.table('item_classificacao',
                      sa.column('tipo_item', sa.String), sa.column('classificacao_id', sa.Integer))

    op.bulk_insert(t_class, [{'id': 20, 'nome': 'Válvulas de Bloqueio (GBC)', 'bloco_id': 4, 'ordem': 8}])
    op.bulk_insert(t_item,  [{'tipo_item': 'valvula_bloqueio_gbc', 'classificacao_id': 20}])

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("SELECT setval('classificacao_item_id_seq', (SELECT MAX(id) FROM classificacao_item))")


def downgrade():
    op.execute("DELETE FROM item_classificacao WHERE tipo_item = 'valvula_bloqueio_gbc'")
    op.execute("DELETE FROM classificacao_item WHERE id = 20")
