"""
Importa painéis frigoríficos para o banco do Projetista V2.

Formato esperado (colunas fixas):
  A(0) Produto | B(1) Fabricante | C(2) Núcleo |
  D(3) Largura mm | E(4) Espessura mm | F(5) Comp. Máx. m |
  G(6) Auto-portância mm | H(7) Peso kg/m² | I(8) U Global W/(m²·K)

Uso:
  python scripts/importar_paineis.py <arquivo.xlsx> [--dry-run]
"""
import sys
import asyncio
import argparse
import openpyxl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.painel import PainelFrigorifico
from app.models.catalogo import Fabricante

COL_PRODUTO    = 0
COL_FABRICANTE = 1
COL_NUCLEO     = 2
COL_LARGURA    = 3
COL_ESPESSURA  = 4
COL_COMP_MAX   = 5
COL_AUTO_PORT  = 6
COL_PESO       = 7
COL_U_GLOBAL   = 8


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_PRODUTO]:
            continue
        dados.append({
            "produto":    str(row[COL_PRODUTO]).strip(),
            "fabricante": str(row[COL_FABRICANTE]).strip() if row[COL_FABRICANTE] else "Generico",
            "nucleo":     str(row[COL_NUCLEO]).strip().upper() if row[COL_NUCLEO] else "PIR",
            "largura_mm": int(row[COL_LARGURA])              if row[COL_LARGURA]   is not None else 0,
            "espessura_mm": int(row[COL_ESPESSURA])          if row[COL_ESPESSURA] is not None else 0,
            "comprimento_max_m": float(row[COL_COMP_MAX])    if row[COL_COMP_MAX]  is not None else None,
            "auto_portancia_mm": int(row[COL_AUTO_PORT])     if row[COL_AUTO_PORT] is not None else None,
            "peso_kg_m2": float(row[COL_PESO])               if row[COL_PESO]      is not None else None,
            "u_global":   float(row[COL_U_GLOBAL])           if row[COL_U_GLOBAL]  is not None else None,
        })
    return dados


async def importar(caminho: str, dry_run: bool):
    dados = ler_excel(caminho)
    nucleos    = sorted(set(d["nucleo"]    for d in dados))
    espessuras = sorted(set(d["espessura_mm"] for d in dados))
    fabricantes= sorted(set(d["fabricante"] for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} paineis | Fabricantes: {fabricantes}")
    print(f"[INFO] Nucleos: {nucleos} | Espessuras: {espessuras} mm")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:
        cache_fab = {}
        inseridos = 0
        atualizados = 0

        for row in dados:
            fab_nome = row["fabricante"]

            # --- Fabricante ---
            if fab_nome not in cache_fab:
                res = await db.execute(select(Fabricante).where(Fabricante.nome == fab_nome))
                fab = res.scalar_one_or_none()
                if not fab:
                    if not dry_run:
                        fab = Fabricante(nome=fab_nome)
                        db.add(fab)
                        await db.flush()
                        print(f"  [NEW] Fabricante: {fab_nome} (id={fab.id})")
                    else:
                        print(f"  [DRY] Fabricante seria criado: {fab_nome}")
                        cache_fab[fab_nome] = -1
                        continue
                cache_fab[fab_nome] = fab.id

            fab_id = cache_fab[fab_nome]
            if fab_id == -1:
                continue

            if row["u_global"] is None:
                print(f"  [SKIP] {row['produto']} esp={row['espessura_mm']}mm — U_global ausente")
                continue

            if dry_run:
                print(f"  [DRY] {row['produto']} | {row['nucleo']} | "
                      f"esp={row['espessura_mm']}mm | larg={row['largura_mm']}mm | "
                      f"U={row['u_global']} W/m2K | comp_max={row['comprimento_max_m']}m")
                continue

            # Verificar se já existe
            res = await db.execute(
                select(PainelFrigorifico).where(
                    PainelFrigorifico.fabricante_id == fab_id,
                    PainelFrigorifico.nucleo        == row["nucleo"],
                    PainelFrigorifico.espessura_mm  == row["espessura_mm"],
                    PainelFrigorifico.largura_mm    == row["largura_mm"],
                )
            )
            existente = res.scalar_one_or_none()

            if existente:
                existente.u_global          = row["u_global"]
                existente.comprimento_max_m = row["comprimento_max_m"]
                existente.auto_portancia_mm = row["auto_portancia_mm"]
                existente.peso_kg_m2        = row["peso_kg_m2"]
                atualizados += 1
            else:
                db.add(PainelFrigorifico(
                    produto           = row["produto"],
                    fabricante_id     = fab_id,
                    nucleo            = row["nucleo"],
                    espessura_mm      = row["espessura_mm"],
                    largura_mm        = row["largura_mm"],
                    comprimento_max_m = row["comprimento_max_m"],
                    auto_portancia_mm = row["auto_portancia_mm"],
                    peso_kg_m2        = row["peso_kg_m2"],
                    u_global          = row["u_global"],
                    custo             = 0,
                ))
                inseridos += 1

        if not dry_run:
            await db.commit()
            print(f"[OK] Importacao concluida!")
            print(f"  Paineis inseridos:   {inseridos}")
            print(f"  Paineis atualizados: {atualizados}")
        else:
            print(f"\n[DRY] Simulacao concluida — nada foi salvo.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description="Importa paineis frigorificos para o banco")
    parser.add_argument("arquivo",   help="Caminho do arquivo .xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar")
    args = parser.parse_args()
    asyncio.run(importar(args.arquivo, args.dry_run))
