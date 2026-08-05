"""Promove um usuário a superadmin_icenexus (administração da plataforma).

Necessário UMA VEZ após o deploy da Fase A: a migration cria todos os usuários como
`admin_empresa` (dono da própria empresa) — ninguém nasce superadmin. Sem isso, as
rotas /api/v1/admin/* ficam inacessíveis e não há como fazer a implantação de clientes.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\promover_superadmin.py <username>            # simula
    ..\\.venv\\Scripts\\python.exe scripts\\promover_superadmin.py <username> --aplicar   # grava

Opcional — renomear a empresa do usuário no mesmo comando:
    ... promover_superadmin.py carlosba --empresa "WEM Refrigeração" --cnpj 41.336.429/0001-31 --aplicar
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

PAPEL = "superadmin_icenexus"


def _opt(flag: str) -> str | None:
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


async def main(username: str, aplicar: bool, nome_empresa: str | None, cnpj: str | None):
    print(f"=== Promover '{username}' a {PAPEL} "
          f"({'APLICANDO' if aplicar else 'simulação'}) ===\n")

    async with SessionLocal() as db:
        row = (await db.execute(text(
            "SELECT u.id, u.papel, e.id, e.nome FROM usuario u "
            "LEFT JOIN empresa e ON e.id = u.empresa_id WHERE u.username = :u"
        ), {"u": username})).first()

        if not row:
            print(f"ERRO: usuário '{username}' não encontrado.")
            print("Usuários disponíveis:")
            for (n,) in (await db.execute(text("SELECT username FROM usuario ORDER BY username"))).all():
                print(f"  · {n}")
            sys.exit(1)

        uid, papel_atual, eid, emp_nome = row
        print(f"  papel atual   : {papel_atual}")
        print(f"  empresa atual : {emp_nome or '(sem empresa)'}")
        if nome_empresa:
            print(f"  renomear para : {nome_empresa}" + (f" · CNPJ {cnpj}" if cnpj else ""))

        if aplicar:
            await db.execute(text("UPDATE usuario SET papel = :p WHERE id = :u"),
                             {"p": PAPEL, "u": uid})
            if nome_empresa and eid:
                await db.execute(text(
                    "UPDATE empresa SET nome = :n" + (", cnpj = :c" if cnpj else "") + " WHERE id = :e"
                ), {"n": nome_empresa, "e": eid, **({"c": cnpj} if cnpj else {})})
            await db.commit()

            r = (await db.execute(text(
                "SELECT u.papel, e.nome, e.cnpj FROM usuario u LEFT JOIN empresa e ON e.id=u.empresa_id "
                "WHERE u.id = :u"), {"u": uid})).first()
            print(f"\n✅ Aplicado. papel={r[0]} · empresa={r[1]} · cnpj={r[2] or '—'}")
        else:
            print("\n(simulação) Rode novamente com --aplicar para gravar.")

        print("\nSuperadmins atuais:")
        for (n,) in (await db.execute(text(
            "SELECT username FROM usuario WHERE papel = :p ORDER BY username"), {"p": PAPEL})).all():
            print(f"  · {n}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")
            and a not in (_opt("--empresa") or "", _opt("--cnpj") or "")]
    if not args:
        print(__doc__)
        sys.exit(1)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args[0], "--aplicar" in sys.argv, _opt("--empresa"), _opt("--cnpj")))
