"""
Importa portas frigoríficas para o banco do Projetista V2.

Formato esperado (colunas fixas):
  A(0) Descrição | B(1) Tipo | C(2) Largura mm | D(3) Altura mm |
  E(4) Espessura mm | F(5) Classificação | G(6) Abertura |
  H(7) Batente | I(8) Soleira (sim/não)

Tipos aceitos: giratoria | deslizante | rapida
Classificação: resfriados | congelada | ultra-congelada
Abertura: direita | esquerda | ambas | automatica
Batente: 3B | 4B | (qualquer texto)
Soleira: sim | não | s | n | 1 | 0

Uso:
  python scripts/importar_portas.py <arquivo.xlsx> [--fabricante "Nome"] [--dry-run]
"""
import sys
import asyncio
import argparse
import openpyxl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.porta import PortaFrigoriifica
from app.models.catalogo import Fabricante

COL_DESCRICAO     = 0
COL_TIPO          = 1
COL_LARGURA       = 2
COL_ALTURA        = 3
COL_ESPESSURA     = 4
COL_CLASSIFICACAO = 5
COL_ABERTURA      = 6
COL_BATENTE       = 7
COL_SOLEIRA       = 8

DESCRICAO_PADRAO = "Porta Frigorífica"


def normalizar_bool(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("sim", "s", "1", "yes", "true")


def normalizar_str(v, default="") -> str:
    return str(v).strip() if v not in (None, "-", "") else default


def ler_excel(caminho: str, fabricante_padrao: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    descricao_atual = DESCRICAO_PADRAO  # herda da linha anterior se vazia

    for row in ws.iter_rows(min_row=2, values_only=True):
        tipo = row[COL_TIPO]
        if not tipo:
            continue

        # Descrição pode ser omitida — herda da linha anterior
        desc = row[COL_DESCRICAO]
        if desc:
            descricao_atual = str(desc).strip()

        try:
            largura   = int(row[COL_LARGURA])
            altura    = int(row[COL_ALTURA])
            espessura = int(row[COL_ESPESSURA])
        except (TypeError, ValueError):
            print(f"  [SKIP] Linha ignorada — dimensões inválidas: {row}")
            continue

        dados.append({
            "descricao":     descricao_atual,
            "tipo":          normalizar_str(tipo).lower(),
            "largura_mm":    largura,
            "altura_mm":     altura,
            "espessura_mm":  espessura,
            "classificacao": normalizar_str(row[COL_CLASSIFICACAO], "resfriados").lower(),
            "abertura":      normalizar_str(row[COL_ABERTURA]) or None,
            "batente":       normalizar_str(row[COL_BATENTE]) or None,
            "soleira":       normalizar_bool(row[COL_SOLEIRA]),
            "fabricante":    fabricante_padrao,
        })
    return dados


async def importar(caminho: str, fabricante_nome: str, dry_run: bool):
    dados = ler_excel(caminho, fabricante_nome)

    tipos   = sorted(set(d["tipo"]          for d in dados))
    classif = sorted(set(d["classificacao"] for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} portas | Fabricante: {fabricante_nome or 'Genérico'}")
    print(f"[INFO] Tipos: {tipos}")
    print(f"[INFO] Classificações: {classif}")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:
        # Garantir fabricante (se informado)
        fab_id = None
        if fabricante_nome:
            res = await db.execute(select(Fabricante).where(Fabricante.nome == fabricante_nome))
            fab = res.scalar_one_or_none()
            if not fab:
                if not dry_run:
                    fab = Fabricante(nome=fabricante_nome)
                    db.add(fab)
                    await db.flush()
                    print(f"  [NEW] Fabricante: {fabricante_nome} (id={fab.id})")
                else:
                    print(f"  [DRY] Fabricante seria criado: {fabricante_nome}")
            if fab:
                fab_id = fab.id

        inseridas   = 0
        atualizadas = 0

        for d in dados:
            if dry_run:
                soleira = "com soleira" if d["soleira"] else "sem soleira"
                print(f"  [DRY] {d['descricao']} | {d['tipo']} | "
                      f"{d['largura_mm']}×{d['altura_mm']}mm | "
                      f"esp={d['espessura_mm']}mm | {d['classificacao']} | "
                      f"abertura={d['abertura']} | batente={d['batente']} | {soleira}")
                continue

            # Verificar se já existe (mesma descrição + dimensões + tipo)
            res = await db.execute(
                select(PortaFrigoriifica).where(
                    PortaFrigoriifica.descricao    == d["descricao"],
                    PortaFrigoriifica.tipo         == d["tipo"],
                    PortaFrigoriifica.largura_mm   == d["largura_mm"],
                    PortaFrigoriifica.altura_mm    == d["altura_mm"],
                    PortaFrigoriifica.espessura_mm == d["espessura_mm"],
                )
            )
            existente = res.scalar_one_or_none()

            if existente:
                existente.classificacao = d["classificacao"]
                existente.abertura      = d["abertura"]
                existente.batente       = d["batente"]
                existente.soleira       = d["soleira"]
                if fab_id:
                    existente.fabricante_id = fab_id
                atualizadas += 1
                print(f"  [UPD] {d['descricao']} {d['largura_mm']}×{d['altura_mm']}mm")
            else:
                db.add(PortaFrigoriifica(
                    fabricante_id = fab_id,
                    descricao     = d["descricao"],
                    tipo          = d["tipo"],
                    largura_mm    = d["largura_mm"],
                    altura_mm     = d["altura_mm"],
                    espessura_mm  = d["espessura_mm"],
                    classificacao = d["classificacao"],
                    abertura      = d["abertura"],
                    batente       = d["batente"],
                    soleira       = d["soleira"],
                    custo         = 0,
                ))
                inseridas += 1
                soleira = "com soleira" if d["soleira"] else "sem soleira"
                print(f"  [OK] {d['descricao']} | {d['tipo']} | "
                      f"{d['largura_mm']}×{d['altura_mm']}mm | "
                      f"esp={d['espessura_mm']}mm | {d['classificacao']} | {soleira}")

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Importacao concluida!")
            print(f"  Portas inseridas:   {inseridas}")
            print(f"  Portas atualizadas: {atualizadas}")
        else:
            print(f"\n[DRY] {len(dados)} portas seriam importadas.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description="Importa portas frigorificas")
    parser.add_argument("arquivo",      help="Caminho do arquivo .xlsx")
    parser.add_argument("--fabricante", default="", help="Nome do fabricante (opcional)")
    parser.add_argument("--dry-run",    action="store_true")
    args = parser.parse_args()
    asyncio.run(importar(args.arquivo, args.fabricante, args.dry_run))
