"""Cria tabela peso_tubo_cobre e popula com dados Forming Tubing

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-27
"""
import sqlalchemy as sa
from alembic import op

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


# Dados extraídos da tabela Forming Tubing — Peso Tubos de Cobre (kg/m)
# Colunas usadas: 0.79mm (1/32" — parede fina) e 1.59mm (1/16" — parede grossa)
# None = espessura não disponível para aquela bitola
DADOS = [
    # (bitola_pol,   diametro_mm, parede_fina, parede_grossa)
    ('1/8"',          3.17,  0.05274,   None),
    ('3/16"',         4.76,  0.087973,  None),
    ('1/4"',          6.35,  0.123207,  None),
    ('5/16"',         7.93,  0.158219,  None),
    ('3/8"',          9.52,  0.193452,  None),
    ('7/16"',        11.11,  0.228686,  None),
    ('1/2"',         12.70,  0.26392,   0.4955),
    ('5/8"',         15.87,  0.334165,  0.636881),
    ('3/4"',         19.05,  0.404632,  0.778707),
    ('7/8"',         22.22,  0.474878,  0.920088),
    ('1"',           25.40,  0.545345,  1.061914),
    ('1.1/8"',       28.57,  0.615591,  1.203295),
    ('1.1/4"',       31.75,  0.686058,  1.345121),
    ('1.3/8"',       34.92,  0.756304,  1.486501),
    ('1.1/2"',       38.10,  0.826771,  1.628328),
    ('1.5/8"',       41.27,  0.897017,  1.769708),
    ('1.3/4"',       44.45,  0.967484,  1.911535),
    ('2"',           50.80,  1.108197,  2.194741),
    ('2.1/8"',       53.97,  None,      2.336122),
    ('2.1/4"',       57.15,  None,      2.477948),
    ('2.1/2"',       63.50,  None,      2.761155),
    ('2.5/8"',       66.67,  None,      2.902535),
    ('3"',           76.20,  None,      3.327569),
    ('3.1/8"',       79.37,  None,      3.468949),
    ('3.5/8"',       92.07,  None,      4.035363),
    ('4.1/8"',      104.77,  None,      4.601776),
]


def upgrade():
    op.create_table(
        'peso_tubo_cobre',
        sa.Column('id',              sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('bitola_pol',      sa.String(10), nullable=False, unique=True),
        sa.Column('diametro_mm',     sa.Float(),    nullable=False),
        sa.Column('parede_fina',     sa.Float(),    nullable=True,
                  comment='Peso kg/m para parede 0.79mm (1/32")'),
        sa.Column('parede_grossa',   sa.Float(),    nullable=True,
                  comment='Peso kg/m para parede 1.59mm (1/16")'),
    )

    tabela = sa.table(
        'peso_tubo_cobre',
        sa.column('bitola_pol',    sa.String),
        sa.column('diametro_mm',   sa.Float),
        sa.column('parede_fina',   sa.Float),
        sa.column('parede_grossa', sa.Float),
    )
    op.bulk_insert(tabela, [
        {'bitola_pol': b, 'diametro_mm': d, 'parede_fina': pf, 'parede_grossa': pg}
        for b, d, pf, pg in DADOS
    ])


def downgrade():
    op.drop_table('peso_tubo_cobre')
