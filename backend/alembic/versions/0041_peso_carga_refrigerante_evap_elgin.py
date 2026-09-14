"""Peso líquido + carga de refrigerante publicada — Evaporadores Elgin FL

Achado do usuário: `equipamento.peso_liquido_kg` e `.carga_refrigerante_kg`
estavam vazios nos 12 modelos de Evaporadora Elgin (linha FL*), mesmo o
`volume_interno_kg` já estando preenchido pra todos (usado hoje na
Estimativa de Carga de Fluido, Card 5). Usuário enviou o catálogo técnico
oficial Elgin ("Evaporador FL", julho/2021, pág. 4 — "Dados Físicos") pra
validar e corrigir.

Achado ao comparar: os valores da coluna "Carga de refrigerante (kg)" do
catálogo batem exatamente com o que já estava gravado em
`volume_interno_kg` — confirma que esse campo já vinha sendo alimentado
com o dado certo desde antes de `carga_refrigerante_kg` existir como
campo próprio (migration 0037). Esta migration replica o mesmo valor pra
`carga_refrigerante_kg` (fonte de verdade correta daqui pra frente — o
serviço de carga de fluido já prioriza esse campo sobre `volume_interno_kg`
quando presente, `evaporador?.carga_refrigerante_kg || volume_interno_kg`)
e preenche `peso_liquido_kg` com a coluna "Peso Líquido/Neto (kg)", dado
que nunca tinha sido cadastrado.

Revision ID: 0041
Revises: 0040
Create Date: 2026-09-14
"""
from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None

# modelo: (peso_liquido_kg, carga_refrigerante_kg) — catálogo Elgin
# "Evaporador FL", julho/2021, pág. 4 ("Dados Físicos").
DADOS = {
    "FL*017": (12.3, 1.1),
    "FL*018": (18.1, 1.3),
    "FL*028": (18.9, 1.7),
    "FL*031": (19.8, 1.9),
    "FL*039": (24.6, 2.2),
    "FL*048": (25.2, 2.7),
    "FL*053": (35.7, 3.2),
    "FL*065": (36.3, 3.5),
    "FL*086": (42.9, 4.5),
    "FL*096": (51.0, 5.0),
    "FL*114": (57.8, 5.9),
    "FL*129": (66.7, 6.6),
}


def upgrade():
    for modelo, (peso, carga) in DADOS.items():
        op.execute(
            f"""
            UPDATE equipamento e
            SET peso_liquido_kg = {peso:.2f},
                carga_refrigerante_kg = {carga:.3f}
            FROM fabricante f, categoria c
            WHERE e.fabricante_id = f.id
              AND e.categoria_id = c.id
              AND f.nome ILIKE '%elgin%'
              AND c.nome = 'Evaporadora'
              AND e.modelo = '{modelo}'
            """
        )


def downgrade():
    for modelo in DADOS:
        op.execute(
            f"""
            UPDATE equipamento e
            SET peso_liquido_kg = NULL,
                carga_refrigerante_kg = NULL
            FROM fabricante f, categoria c
            WHERE e.fabricante_id = f.id
              AND e.categoria_id = c.id
              AND f.nome ILIKE '%elgin%'
              AND c.nome = 'Evaporadora'
              AND e.modelo = '{modelo}'
            """
        )
