"""Classificação de itens do orçamento (blocos + classificações + de-para tipo_item)

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-09
"""
import sqlalchemy as sa
from alembic import op

revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


# ── Seed ──────────────────────────────────────────────────────────────────
# Blocos (nível 1): id, nome, ordem
BLOCOS = [
    (1, 'Materiais Termo Isolantes', 1),
    (2, 'Equipamentos',              2),
    (3, 'Tubulação e Conexões',      3),
    (4, 'Componentes de Fluxo',      4),
    (99, 'Outros',                   99),
]

# Classificações (nível 2): id, nome, bloco_id, ordem
CLASSIFICACOES = [
    (1,  'Painéis PIR/PUR',                    1, 1),
    (2,  'Placas de Isolamento',               1, 2),
    (3,  'Acessórios de Vedação',              1, 3),
    (4,  'Estrutura / Piso',                   1, 4),
    (5,  'Acessórios de Montagem',             1, 5),
    (6,  'Portas Frigoríficas',                1, 6),
    (7,  'Unidade Condensadora',               2, 1),
    (8,  'Evaporadora / Forçador',             2, 2),
    (9,  'Tubo de Cobre',                      3, 1),
    (10, 'Isolamento de Tubulações e Vasos',   3, 2),
    (11, 'Conexões (luvas/porcas)',            3, 3),
    (12, 'Sifões',                             3, 4),
    (13, 'Válvula de Expansão (VET)',          4, 1),
    (14, 'Válvula Solenoide',                  4, 2),
    (15, 'Filtro Secador',                     4, 3),
    (16, 'Visor de Líquido',                   4, 4),
    (17, 'Separadores',                        4, 5),
    (18, 'Tanque de Líquido',                  4, 6),
    (19, 'Carga de Fluido',                    4, 7),
    (99, 'A classificar',                      99, 1),
]

# De-para tipo_item → classificacao_id
ITENS = [
    ('painel_parede',           1),
    ('painel_teto',             1),
    ('painel_piso',             1),
    ('placa_isolamento',        2),
    ('barreira_vapor',          3),
    ('concreto_armado',         4),
    ('acessorio_montagem',      5),
    ('porta_frigorifica',       6),
    ('unidade_condensadora',    7),
    ('evaporadora',             8),
    ('tubo_cobre_liquido',      9),
    ('tubo_cobre_succao',       9),
    ('isolamento_tubo_succao',  10),
    ('isolamento_tubo_liquido', 10),
    ('luva_passagem',           11),
    ('luva_reducao',            11),
    ('porca',                   11),
    ('sifao',                   12),
    ('contra_sifao',            12),
    ('valvula_expansao',        13),
    ('valvula_solenoide',       14),
    ('filtro_secador',          15),
    ('visor_liquido',           16),
    ('separador_liquido',       17),
    ('separador_oleo',          17),
    ('tanque_liquido',          18),
    ('carga_fluido',            19),
]


def upgrade():
    op.create_table(
        'bloco_orcamento',
        sa.Column('id',    sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nome',  sa.String(100), nullable=False, unique=True),
        sa.Column('ordem', sa.Integer(),   nullable=False, server_default='0'),
    )
    op.create_table(
        'classificacao_item',
        sa.Column('id',       sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nome',     sa.String(100), nullable=False),
        sa.Column('bloco_id', sa.Integer(), sa.ForeignKey('bloco_orcamento.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ordem',    sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_table(
        'item_classificacao',
        sa.Column('id',               sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tipo_item',        sa.String(50), nullable=False, unique=True),
        sa.Column('classificacao_id', sa.Integer(), sa.ForeignKey('classificacao_item.id', ondelete='CASCADE'), nullable=False),
    )

    t_bloco = sa.table('bloco_orcamento',
                       sa.column('id', sa.Integer), sa.column('nome', sa.String), sa.column('ordem', sa.Integer))
    t_class = sa.table('classificacao_item',
                       sa.column('id', sa.Integer), sa.column('nome', sa.String),
                       sa.column('bloco_id', sa.Integer), sa.column('ordem', sa.Integer))
    t_item = sa.table('item_classificacao',
                      sa.column('tipo_item', sa.String), sa.column('classificacao_id', sa.Integer))

    op.bulk_insert(t_bloco, [{'id': i, 'nome': n, 'ordem': o} for i, n, o in BLOCOS])
    op.bulk_insert(t_class, [{'id': i, 'nome': n, 'bloco_id': b, 'ordem': o} for i, n, b, o in CLASSIFICACOES])
    op.bulk_insert(t_item,  [{'tipo_item': t, 'classificacao_id': c} for t, c in ITENS])

    # Ajusta sequências (Postgres) para não colidir com IDs inseridos manualmente
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("SELECT setval('bloco_orcamento_id_seq', (SELECT MAX(id) FROM bloco_orcamento))")
        op.execute("SELECT setval('classificacao_item_id_seq', (SELECT MAX(id) FROM classificacao_item))")


def downgrade():
    op.drop_table('item_classificacao')
    op.drop_table('classificacao_item')
    op.drop_table('bloco_orcamento')
