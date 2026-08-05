"""Copia projetos entre empresas — por nome ou pelos mais recentes.

COPIA, não move: o original permanece intacto na empresa de origem. O projeto novo
recebe o dono e a empresa do destino, com o mesmo `dados_completos`.

Uso:
    cd backend

    # 1) ver o que existe na origem (nomes exatos e datas)
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py carlosba --listar

    # 2a) copiar projetos ESCOLHIDOS pelo nome (recomendado)
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py carlosba hbs --nomes "Câmara A" "Câmara B"
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py carlosba hbs --nomes "Câmara A" "Câmara B" --aplicar

    # 2b) ou copiar os N mais recentes
    ..\\.venv\\Scripts\\python.exe scripts\\copiar_projetos.py carlosba hbs --ultimos 4 --aplicar

Sem --aplicar o script apenas simula e mostra o que faria.

ATENÇÃO: `dados_completos` carrega junto os dados do cliente final e a composição
comercial (custos, margens, imposto). Confira o conteúdo antes de copiar para a
empresa de um cliente.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402


async def _usuario(db, username: str):
    r = (await db.execute(text(
        "SELECT u.id, u.empresa_id, e.nome FROM usuario u "
        "LEFT JOIN empresa e ON e.id = u.empresa_id WHERE u.username = :u"
    ), {"u": username})).first()
    if not r:
        print(f"ERRO: usuário '{username}' não encontrado.")
        nomes = (await db.execute(text("SELECT username FROM usuario ORDER BY username"))).all()
        print("Usuários disponíveis:", ", ".join(n for (n,) in nomes))
        sys.exit(1)
    if not r[1]:
        print(f"ERRO: usuário '{username}' não tem empresa vinculada.")
        sys.exit(1)
    return r  # (id, empresa_id, empresa_nome)


async def listar(db, empresa_id, empresa_nome):
    linhas = (await db.execute(text(
        "SELECT nome, cliente, status, updated_at, length(dados_completos::text) "
        "FROM projeto WHERE empresa_id = :e ORDER BY updated_at DESC"
    ), {"e": empresa_id})).all()
    print(f"PROJETOS DE '{empresa_nome}' ({len(linhas)}):\n")
    print(f"  {'NOME':38} {'CLIENTE':22} {'ATUALIZADO':12} {'TAMANHO':>9}")
    print("  " + "-" * 84)
    for nome, cli, st, upd, tam in linhas:
        print(f"  {(nome or '')[:38]:38} {(cli or '—')[:22]:22} {upd:%d/%m/%Y}   {tam:>7}B")
    print("\nUse os nomes acima em --nomes \"...\" \"...\" (nome exato, entre aspas).")


async def main(args):
    async with SessionLocal() as db:
        _, emp_origem, nome_origem = await _usuario(db, args.origem)

        if args.listar:
            await listar(db, emp_origem, nome_origem)
            return

        if not args.destino:
            print("ERRO: informe o usuário de destino (ou use --listar).")
            sys.exit(1)
        if not args.nomes and not args.ultimos:
            print("ERRO: escolha --nomes \"...\" ou --ultimos N.")
            sys.exit(1)

        uid_dest, emp_dest, nome_dest = await _usuario(db, args.destino)
        if emp_dest == emp_origem:
            print("ERRO: origem e destino são a mesma empresa.")
            sys.exit(1)

        # ── Seleção ────────────────────────────────────────────────────────
        if args.nomes:
            linhas = (await db.execute(text(
                "SELECT id, nome FROM projeto WHERE empresa_id = :e AND nome = ANY(:n)"
            ), {"e": emp_origem, "n": args.nomes})).all()
            achados = {n for _, n in linhas}
            faltando = [n for n in args.nomes if n not in achados]
            if faltando:
                print("⚠ Não encontrados na origem (confira o nome exato com --listar):")
                for n in faltando:
                    print(f"    · {n!r}")
                if not linhas:
                    sys.exit(1)
        else:
            linhas = (await db.execute(text(
                "SELECT id, nome FROM projeto WHERE empresa_id = :e "
                "ORDER BY updated_at DESC LIMIT :n"
            ), {"e": emp_origem, "n": args.ultimos})).all()

        print(f"\n{'APLICANDO' if args.aplicar else 'SIMULAÇÃO'} · "
              f"{nome_origem} -> {nome_dest}\n")
        for pid, nome in linhas:
            print(f"  · {nome!r} -> {nome + ' (cópia)'!r}")
            if args.aplicar:
                await db.execute(text(
                    "INSERT INTO projeto (id, nome, cliente, status, dados_completos, "
                    "                     owner_id, empresa_id, created_at, updated_at) "
                    "SELECT :novo, :nome, cliente, status, dados_completos, "
                    "       :owner, :empresa, now(), now() FROM projeto WHERE id = :orig"
                ), {"novo": uuid4(), "nome": f"{nome} (cópia)", "owner": uid_dest,
                    "empresa": emp_dest, "orig": pid})

        if args.aplicar:
            await db.commit()
            print(f"\n✅ {len(linhas)} projeto(s) copiado(s). Originais intactos.")
        else:
            print(f"\n(simulação) Seriam copiados {len(linhas)} projeto(s). Use --aplicar para gravar.")

        for quem, emp in ((nome_origem, emp_origem), (nome_dest, emp_dest)):
            n = (await db.execute(text(
                "SELECT count(*) FROM projeto WHERE empresa_id = :e"), {"e": emp})).scalar()
            print(f"    {quem:24} {n} projeto(s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Copia projetos entre empresas.")
    ap.add_argument("origem", help="username de origem")
    ap.add_argument("destino", nargs="?", help="username de destino")
    ap.add_argument("--listar", action="store_true", help="lista os projetos da origem e sai")
    ap.add_argument("--nomes", nargs="+", metavar="NOME", help="nomes exatos dos projetos a copiar")
    ap.add_argument("--ultimos", type=int, metavar="N", help="copia os N mais recentes")
    ap.add_argument("--aplicar", action="store_true", help="grava (sem isso, apenas simula)")
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(ap.parse_args()))
