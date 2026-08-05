"""Backfill da Fase A — cria 1 empresa por usuário e preenche empresa_id nas tabelas escopadas.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\backfill_empresa.py            # simula (dry-run)
    ..\\.venv\\Scripts\\python.exe scripts\\backfill_empresa.py --aplicar  # grava

IDEMPOTENTE: só toca em registros com empresa_id NULL. Rodar duas vezes não duplica
nada nem reatribui empresa de quem já tem.

Regra: cada usuário existente vira uma empresa própria (1:1). Depois da Fase A, novos
usuários de uma mesma empresa são criados pelo endpoint de admin, apontando para a
empresa já existente.
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

# (tabela, coluna que aponta para usuario.id)
ESCOPADAS = [
    ("projeto", "owner_id"),
    ("cliente", "owner_id"),
    ("fornecedor", "owner_id"),
    ("cotacao", "owner_id"),
    ("proposta_comercial", "owner_id"),
    ("configuracao_montagem", "usuario_id"),
]


async def main(aplicar: bool):
    modo = "APLICANDO" if aplicar else "SIMULAÇÃO (dry-run) — nada será gravado"
    print(f"=== Backfill multi-tenancy — {modo} ===\n")

    async with SessionLocal() as db:
        # ── 1. Uma empresa por usuário sem empresa ──────────────────────────
        sem_empresa = (await db.execute(text(
            "SELECT id, username, email FROM usuario WHERE empresa_id IS NULL ORDER BY created_at"
        ))).all()

        print(f"[1] Usuários sem empresa: {len(sem_empresa)}")
        for uid, username, email in sem_empresa:
            nome = (username or email or "Empresa").strip()
            print(f"    · {username:20} -> empresa '{nome}'")
            if aplicar:
                eid = uuid4()
                await db.execute(text(
                    "INSERT INTO empresa (id, nome, plano, status_assinatura, created_at, updated_at) "
                    "VALUES (:id, :nome, 'trial', 'ativa', now(), now())"
                ), {"id": eid, "nome": nome})
                await db.execute(text(
                    "UPDATE usuario SET empresa_id = :eid WHERE id = :uid"
                ), {"eid": eid, "uid": uid})

        if aplicar:
            await db.flush()

        # ── 2. empresa_id nas tabelas escopadas, a partir do dono ───────────
        print("\n[2] Propagando empresa_id (via dono do registro):")
        total = 0
        for tabela, col in ESCOPADAS:
            # No dry-run as empresas ainda não existem; conta o que SERIA vinculado
            # assumindo que todo usuário terá empresa após a etapa 1.
            sql_conta = (
                f"SELECT count(*) FROM {tabela} t JOIN usuario u ON u.id = t.{col} "
                f"WHERE t.empresa_id IS NULL"
            )
            sql_update = (
                f"UPDATE {tabela} t SET empresa_id = u.empresa_id FROM usuario u "
                f"WHERE t.{col} = u.id AND t.empresa_id IS NULL AND u.empresa_id IS NOT NULL"
            )
            if aplicar:
                res = await db.execute(text(sql_update))
                n = res.rowcount
            else:
                n = (await db.execute(text(sql_conta))).scalar() or 0
            total += n
            print(f"    · {tabela:24} {n:4} registro(s)")

        # ── 3. Órfãos (sem dono) — ficam sem empresa, exigem decisão manual ──
        print("\n[3] Registros órfãos (sem dono — permanecem sem empresa):")
        orfaos = 0
        for tabela, col in ESCOPADAS:
            n = (await db.execute(text(
                f"SELECT count(*) FROM {tabela} WHERE {col} IS NULL AND empresa_id IS NULL"
            ))).scalar() or 0
            if n:
                print(f"    ⚠ {tabela:24} {n} registro(s)")
                orfaos += n
        if not orfaos:
            print("    nenhum")

        if aplicar:
            await db.commit()
            print(f"\n✅ Gravado. {len(sem_empresa)} empresa(s) criada(s), {total} registro(s) vinculado(s).")
        else:
            print(f"\n(dry-run) Seriam criadas {len(sem_empresa)} empresa(s) e vinculados {total} registro(s).")
            print("Rode novamente com --aplicar para gravar.")

        # ── 4. Verificação final ────────────────────────────────────────────
        print("\n[4] Situação atual (pendentes de empresa_id):")
        n = (await db.execute(text("SELECT count(*) FROM usuario WHERE empresa_id IS NULL"))).scalar()
        print(f"    usuario                  {n}")
        for tabela, _ in ESCOPADAS:
            n = (await db.execute(text(f"SELECT count(*) FROM {tabela} WHERE empresa_id IS NULL"))).scalar()
            print(f"    {tabela:24} {n}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(aplicar="--aplicar" in sys.argv))
