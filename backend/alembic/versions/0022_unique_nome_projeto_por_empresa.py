"""Nome de projeto único por empresa

Corrige bug: nada impedia salvar dois projetos com o mesmo nome (nem no
frontend, nem no backend, nem no banco). Antes de criar a constraint,
desambigua duplicatas que já existam (mantém a mais antiga com o nome
original, renomeia as demais) — assim o deploy não quebra se já houver
duplicatas em produção.

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-13
"""
import sqlalchemy as sa
from alembic import op

revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    duplicados = conn.execute(sa.text(
        "SELECT empresa_id, nome, array_agg(id ORDER BY created_at) AS ids "
        "FROM projeto GROUP BY empresa_id, nome HAVING count(*) > 1"
    )).all()

    total_renomeados = 0
    for empresa_id, nome, ids in duplicados:
        # ids[0] fica com o nome original (mais antigo); os demais são desambiguados
        for projeto_id in ids[1:]:
            sufixo = str(projeto_id)[:8]
            conn.execute(sa.text(
                "UPDATE projeto SET nome = :novo_nome WHERE id = :id"
            ), {"novo_nome": f"{nome} (duplicado {sufixo})"[:200], "id": projeto_id})
            total_renomeados += 1
    if duplicados:
        print(f"[0022] {len(duplicados)} nome(s) duplicado(s) encontrados, "
              f"{total_renomeados} projeto(s) renomeado(s) para desambiguar")

    op.create_unique_constraint('uq_projeto_empresa_nome', 'projeto', ['empresa_id', 'nome'])


def downgrade():
    op.drop_constraint('uq_projeto_empresa_nome', 'projeto', type_='unique')
