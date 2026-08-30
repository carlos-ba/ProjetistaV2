"""Backfill 2026-08-30: plano='trial' -> plano='tecnico'.

Decisão: "trial" deixou de ser um valor válido de `plano` (produto
contratado) — passou a existir só em `status_assinatura` (fase temporária
de avaliação). Toda empresa com plano='trial' hoje é, por construção, um
cadastro self-serve feito por `registrar_usuario` (o único caminho que
grava plano='trial' — empresas criadas pelo admin sempre setam um plano
real explícito) — ou seja, é seguro e determinístico virar 'tecnico'.
Ver docs/decisoes/2026-08-30-plano-x-status.md.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\backfill_plano_tecnico.py            # simula
    ..\\.venv\\Scripts\\python.exe scripts\\backfill_plano_tecnico.py --aplicar  # grava

IDEMPOTENTE: só toca em plano='trial'. Rodar de novo depois de aplicado não
encontra mais nada pra mudar.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402


async def main(aplicar: bool):
    modo = "APLICANDO" if aplicar else "SIMULACAO (dry-run) - nada sera gravado"
    print(f"=== Backfill plano='trial' -> 'tecnico' - {modo} ===\n")

    async with SessionLocal() as db:
        afetadas = (await db.execute(text(
            "SELECT id, nome, status_assinatura FROM empresa WHERE plano = 'trial' ORDER BY nome"
        ))).all()

        print(f"Empresas com plano='trial': {len(afetadas)}")
        for eid, nome, status in afetadas:
            print(f"    - {nome:30} status={status}")

        if aplicar:
            res = await db.execute(text("UPDATE empresa SET plano = 'tecnico' WHERE plano = 'trial'"))
            await db.commit()
            print(f"\nGravado. {res.rowcount} empresa(s) atualizada(s) para plano='tecnico'.")
        else:
            print(f"\n(dry-run) Seriam atualizadas {len(afetadas)} empresa(s).")
            print("Rode novamente com --aplicar para gravar.")

        restantes = (await db.execute(text(
            "SELECT count(*) FROM empresa WHERE plano = 'trial'"
        ))).scalar()
        print(f"\nEmpresas com plano='trial' apos esta execucao (se --aplicar): "
              f"{0 if aplicar else restantes}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(aplicar="--aplicar" in sys.argv))
