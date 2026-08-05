"""Fase A — passo 2 de 2: backfill automático + empresa_id NOT NULL

Faz o backfill DENTRO da migration e só então aplica o NOT NULL. Assim
`alembic upgrade head` funciona sozinho em qualquer ambiente — do zero ou já
povoado — sem passo manual entre dois deploys.

Regra do backfill: cada usuário existente vira dono de uma empresa própria (1:1).
Registros escopados herdam a empresa pelo dono (owner_id / usuario_id).

Órfãos (registros sem dono, herdados de FKs com SET NULL) não têm empresa a herdar.
Em vez de apagá-los ou travar o deploy, são estacionados numa empresa de quarentena
— ficam invisíveis para todos os tenants reais, mas preservados e identificáveis.

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-05
"""
import uuid

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None

# (tabela, coluna que aponta para usuario.id)
ESCOPADAS = [
    ('projeto', 'owner_id'),
    ('cliente', 'owner_id'),
    ('fornecedor', 'owner_id'),
    ('cotacao', 'owner_id'),
    ('proposta_comercial', 'owner_id'),
    ('configuracao_montagem', 'usuario_id'),
]

EMPRESA_QUARENTENA = 'Registros órfãos (migração multi-tenancy)'


def upgrade():
    conn = op.get_bind()

    # ── 1. Uma empresa por usuário sem empresa ──────────────────────────────
    usuarios = conn.execute(sa.text(
        "SELECT id, username, email FROM usuario WHERE empresa_id IS NULL"
    )).all()
    for uid, username, email in usuarios:
        eid = uuid.uuid4()
        conn.execute(sa.text(
            "INSERT INTO empresa (id, nome, plano, status_assinatura, created_at, updated_at) "
            "VALUES (:id, :nome, 'trial', 'ativa', now(), now())"
        ), {"id": eid, "nome": (username or email or "Empresa")[:200]})
        conn.execute(sa.text(
            "UPDATE usuario SET empresa_id = :e WHERE id = :u"
        ), {"e": eid, "u": uid})
    print(f"[0021] empresas criadas para {len(usuarios)} usuário(s)")

    # ── 2. Registros escopados herdam a empresa do dono ─────────────────────
    for tabela, col in ESCOPADAS:
        r = conn.execute(sa.text(
            f"UPDATE {tabela} t SET empresa_id = u.empresa_id FROM usuario u "
            f"WHERE t.{col} = u.id AND t.empresa_id IS NULL"
        ))
        print(f"[0021] {tabela}: {r.rowcount} registro(s) vinculado(s)")

    # ── 3. Órfãos (sem dono) vão para a quarentena ──────────────────────────
    orfaos = {}
    for tabela, _ in ESCOPADAS:
        n = conn.execute(sa.text(
            f"SELECT count(*) FROM {tabela} WHERE empresa_id IS NULL"
        )).scalar()
        if n:
            orfaos[tabela] = n

    if orfaos:
        qid = uuid.uuid4()
        conn.execute(sa.text(
            "INSERT INTO empresa (id, nome, plano, status_assinatura, created_at, updated_at) "
            "VALUES (:id, :nome, 'inativo', 'cancelada', now(), now())"
        ), {"id": qid, "nome": EMPRESA_QUARENTENA})
        for tabela, n in orfaos.items():
            conn.execute(sa.text(
                f"UPDATE {tabela} SET empresa_id = :e WHERE empresa_id IS NULL"
            ), {"e": qid})
            print(f"[0021] {tabela}: {n} órfão(s) movido(s) para quarentena")

    # ── 4. Agora sim, NOT NULL ──────────────────────────────────────────────
    op.alter_column('usuario', 'empresa_id', existing_type=pg.UUID(as_uuid=True), nullable=False)
    for tabela, _ in ESCOPADAS:
        op.alter_column(tabela, 'empresa_id', existing_type=pg.UUID(as_uuid=True), nullable=False)

    # A FK do usuário nasceu com SET NULL (coluna era nullable). Agora que é NOT NULL,
    # SET NULL seria contraditório — RESTRICT impede apagar empresa com usuário, com
    # erro claro em vez de violação de constraint.
    op.drop_constraint('fk_usuario_empresa', 'usuario', type_='foreignkey')
    op.create_foreign_key('fk_usuario_empresa', 'usuario', 'empresa', ['empresa_id'], ['id'],
                          ondelete='RESTRICT')


def downgrade():
    """Volta as colunas para nullable. Os dados do backfill permanecem — são
    idempotentes e um novo upgrade os reaproveita."""
    op.drop_constraint('fk_usuario_empresa', 'usuario', type_='foreignkey')
    op.create_foreign_key('fk_usuario_empresa', 'usuario', 'empresa', ['empresa_id'], ['id'],
                          ondelete='SET NULL')
    for tabela, _ in ESCOPADAS:
        op.alter_column(tabela, 'empresa_id', existing_type=pg.UUID(as_uuid=True), nullable=True)
    op.alter_column('usuario', 'empresa_id', existing_type=pg.UUID(as_uuid=True), nullable=True)
