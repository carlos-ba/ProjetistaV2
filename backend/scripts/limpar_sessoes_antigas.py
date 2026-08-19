"""Apaga sessões antigas de sessao_usuario (retenção LGPD — DESIGN_LIMITE_SESSOES_2026-08-16.md).

ip e user_agent são dado pessoal; a decisão foi não acumular indefinidamente. Apaga
sessões REVOGADAS (revogada_em preenchido) com mais de N dias. Sessões vivas
(revogada_em IS NULL) nunca são tocadas, mesmo que antigas — ainda podem estar em uso.

Sem cron configurado no projeto ainda — roda manual por enquanto.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\limpar_sessoes_antigas.py            # simula, 90 dias
    ..\\.venv\\Scripts\\python.exe scripts\\limpar_sessoes_antigas.py --dias 60  # simula, 60 dias
    ..\\.venv\\Scripts\\python.exe scripts\\limpar_sessoes_antigas.py --aplicar  # grava
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

DIAS_PADRAO = 90


def _dias() -> int:
    if "--dias" in sys.argv:
        i = sys.argv.index("--dias")
        if i + 1 < len(sys.argv):
            return int(sys.argv[i + 1])
    return DIAS_PADRAO


async def main(dias: int, aplicar: bool):
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    print(f"=== Limpeza de sessões revogadas há mais de {dias} dias "
          f"({'APLICANDO' if aplicar else 'simulação'}) ===\n")

    async with SessionLocal() as db:
        candidatas = (await db.execute(text(
            "SELECT count(*) FROM sessao_usuario WHERE revogada_em IS NOT NULL AND revogada_em < :limite"
        ), {"limite": limite})).scalar_one()
        vivas_antigas = (await db.execute(text(
            "SELECT count(*) FROM sessao_usuario WHERE revogada_em IS NULL AND created_at < :limite"
        ), {"limite": limite})).scalar_one()

        print(f"  sessões revogadas há mais de {dias} dias : {candidatas}  (serão apagadas)")
        print(f"  sessões ainda vivas mas antigas          : {vivas_antigas}  (NÃO tocadas — podem estar em uso)")

        if aplicar:
            await db.execute(text(
                "DELETE FROM sessao_usuario WHERE revogada_em IS NOT NULL AND revogada_em < :limite"
            ), {"limite": limite})
            await db.commit()
            print(f"\n✅ {candidatas} sessão(ões) apagada(s).")
        else:
            print("\n(simulação) Rode novamente com --aplicar para apagar de verdade.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(_dias(), "--aplicar" in sys.argv))
