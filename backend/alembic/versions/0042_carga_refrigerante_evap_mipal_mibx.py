"""Carga de refrigerante publicada — Evaporadores Mipal Mi BX (linha antiga)

Achado revisando o catálogo de Evaporadora completo (2026-09-14, depois do
fix da Elgin FL* na migration 0041): dos 61 modelos Mipal, 48 (linha
Hd/Hdl400 Pro, catálogo mais novo) já tinham `carga_refrigerante_kg`
preenchido; os outros 13 (linha antiga "Mi BX") só tinham
`volume_interno_kg` — mesmo padrão da Elgin antes da 0041.

Usuário confirmou diretamente (curador da informação, catálogo Mi BX em
mãos): o valor gravado em `volume_interno_kg` pra essa linha **é** a carga
de refrigerante publicada, não um volume calculado — nomenclatura antiga,
de antes de `carga_refrigerante_kg` existir como campo próprio (migration
0037, motivada pelo catálogo Hd/Hdl400 Pro). Diferente da 0041 (valores
extraídos de um PDF externo), aqui o dado já está no banco — só precisa
migrar de coluna, por isso o `UPDATE` copia direto de `volume_interno_kg`
em vez de valores hardcoded.

Revision ID: 0042
Revises: 0041
Create Date: 2026-09-14
"""
from alembic import op

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE equipamento e
        SET carga_refrigerante_kg = e.volume_interno_kg
        FROM fabricante f, categoria c
        WHERE e.fabricante_id = f.id
          AND e.categoria_id = c.id
          AND f.nome ILIKE '%mipal%'
          AND c.nome = 'Evaporadora'
          AND e.modelo ILIKE 'Mi BX%'
          AND e.volume_interno_kg IS NOT NULL
          AND e.carga_refrigerante_kg IS NULL
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE equipamento e
        SET carga_refrigerante_kg = NULL
        FROM fabricante f, categoria c
        WHERE e.fabricante_id = f.id
          AND e.categoria_id = c.id
          AND f.nome ILIKE '%mipal%'
          AND c.nome = 'Evaporadora'
          AND e.modelo ILIKE 'Mi BX%'
        """
    )
