"""Copia projetos de um usuário/empresa para outro — útil para montar cenário de teste.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py <user_origem> <user_destino> [qtde]
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py carlosba topema_teste 3 --aplicar

COPIA (não move): o original permanece intacto na empresa de origem. O projeto novo
recebe o owner e a empresa do destino, com o mesmo `dados_completos`.
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402


async def main(origem: str, destino: str, qtde: int, aplicar: bool):
    print(f"=== Copiar {qtde} projeto(s): {origem} -> {destino} "
          f"({'APLICANDO' if aplicar else 'simulação'}) ===\n")

    async with SessionLocal() as db:
        async def usuario(username):
            r = (await db.execute(text(
                "SELECT id, empresa_id FROM usuario WHERE username = :u"
            ), {"u": username})).first()
            if not r:
                print(f"ERRO: usuário '{username}' não encontrado."); sys.exit(1)
            if not r[1]:
                print(f"ERRO: usuário '{username}' não tem empresa vinculada."); sys.exit(1)
            return r

        _, emp_origem = await usuario(origem)
        uid_dest, emp_dest = await usuario(destino)

        projetos = (await db.execute(text(
            "SELECT id, nome, cliente, status FROM projeto "
            "WHERE empresa_id = :e ORDER BY updated_at DESC LIMIT :n"
        ), {"e": emp_origem, "n": qtde})).all()

        if not projetos:
            print("Nenhum projeto na origem."); return

        for pid, nome, cliente, status in projetos:
            novo_nome = f"{nome} (cópia)"
            print(f"  · {nome!r} -> {novo_nome!r}")
            if aplicar:
                await db.execute(text(
                    "INSERT INTO projeto (id, nome, cliente, status, dados_completos, "
                    "                     owner_id, empresa_id, created_at, updated_at) "
                    "SELECT :novo_id, :nome, cliente, status, dados_completos, "
                    "       :owner, :empresa, now(), now() "
                    "FROM projeto WHERE id = :orig"
                ), {"novo_id": uuid4(), "nome": novo_nome, "owner": uid_dest,
                    "empresa": emp_dest, "orig": pid})

        if aplicar:
            await db.commit()
            print(f"\n✅ {len(projetos)} projeto(s) copiado(s). Originais intactos.")
        else:
            print(f"\n(simulação) Seriam copiados {len(projetos)} projeto(s). Use --aplicar.")

        for quem, emp in ((origem, emp_origem), (destino, emp_dest)):
            n = (await db.execute(text(
                "SELECT count(*) FROM projeto WHERE empresa_id = :e"), {"e": emp})).scalar()
            print(f"    {quem:16} agora tem {n} projeto(s)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args[0], args[1], int(args[2]) if len(args) > 2 else 3,
                     "--aplicar" in sys.argv))
