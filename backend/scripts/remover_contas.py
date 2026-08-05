"""Remove contas de usuário e a empresa delas — com inventário prévio do que será perdido.

DESTRUTIVO E IRREVERSÍVEL. Apagar a empresa leva junto, por CASCADE, todos os
projetos, clientes, fornecedores, cotações, propostas e perfis de montagem dela.

Uso:
    cd backend
    # 1) inventário: mostra o que cada conta tem, sem apagar nada
    ..\\.venv\\Scripts\\python.exe scripts\\remover_contas.py teste10 teste_local

    # 2) apaga de verdade
    ..\\.venv\\Scripts\\python.exe scripts\\remover_contas.py teste10 teste_local --aplicar

Proteções:
  - Sem --aplicar apenas inventaria.
  - Contas com dados são destacadas; use --forcar para apagar mesmo assim.
  - Recusa apagar superadmin (evita perder o acesso administrativo).
  - A empresa só é removida se não sobrar nenhum outro usuário nela.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

TABELAS = ["projeto", "cliente", "fornecedor", "cotacao", "proposta_comercial", "configuracao_montagem"]


async def main(usernames, aplicar, forcar):
    async with SessionLocal() as db:
        print(f"=== {'REMOVENDO' if aplicar else 'INVENTÁRIO (nada será apagado)'} ===\n")
        alvos, com_dados = [], []

        for username in usernames:
            r = (await db.execute(text(
                "SELECT u.id, u.papel, u.email, e.id, e.nome FROM usuario u "
                "LEFT JOIN empresa e ON e.id = u.empresa_id WHERE u.username = :u"
            ), {"u": username})).first()
            if not r:
                print(f"⚠ '{username}' não encontrado — ignorando.\n")
                continue
            uid, papel, email, eid, enome = r

            if papel == "superadmin_icenexus":
                print(f"⛔ '{username}' é superadmin — recusado para não perder o acesso administrativo.\n")
                continue

            # quantos outros usuários dividem a mesma empresa
            outros = (await db.execute(text(
                "SELECT count(*) FROM usuario WHERE empresa_id = :e AND id <> :u"
            ), {"e": eid, "u": uid})).scalar() if eid else 0

            contagens = {}
            total = 0
            if eid:
                for t in TABELAS:
                    n = (await db.execute(text(
                        f"SELECT count(*) FROM {t} WHERE empresa_id = :e"), {"e": eid})).scalar()
                    if n:
                        contagens[t] = n
                        total += n

            print(f"· {username}  ({email})")
            print(f"    empresa: {enome or '—'}" + (f"  · outros usuários nela: {outros}" if outros else ""))
            if contagens:
                print(f"    DADOS QUE SERÃO PERDIDOS: " + " · ".join(f"{t}={n}" for t, n in contagens.items()))
                com_dados.append(username)
            else:
                print("    sem dados")
            print()
            alvos.append((username, uid, eid, enome, outros, total))

        if not alvos:
            print("Nada a fazer.")
            return

        if com_dados and not forcar:
            print("⛔ ABORTADO: as contas acima têm dados. Revise e, se for mesmo para apagar,")
            print("   repita o comando acrescentando --forcar.")
            return

        if not aplicar:
            print(f"(inventário) {len(alvos)} conta(s) seriam removidas. Use --aplicar para executar.")
            return

        for username, uid, eid, enome, outros, _ in alvos:
            await db.execute(text("DELETE FROM usuario WHERE id = :u"), {"u": uid})
            if eid and outros == 0:
                await db.execute(text("DELETE FROM empresa WHERE id = :e"), {"e": eid})
                print(f"  ✅ {username} e a empresa '{enome}' removidos")
            else:
                print(f"  ✅ {username} removido (empresa '{enome}' mantida — há outros usuários)")
        await db.commit()

        print("\nSituação final:")
        for u, e in (await db.execute(text(
            "SELECT u.username, em.nome FROM usuario u JOIN empresa em ON em.id = u.empresa_id "
            "ORDER BY u.username"))).all():
            print(f"  {u:24} {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Remove contas e suas empresas (destrutivo).")
    ap.add_argument("usernames", nargs="+", help="usernames a remover")
    ap.add_argument("--aplicar", action="store_true", help="executa (sem isso, só inventaria)")
    ap.add_argument("--forcar", action="store_true", help="permite apagar contas que têm dados")
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    a = ap.parse_args()
    asyncio.run(main(a.usernames, a.aplicar, a.forcar))
