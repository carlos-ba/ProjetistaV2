"""
Importa Válvulas de Expansão Termostática (VET) para o banco do Projetista V2.

Formato esperado (colunas fixas):
  A(0) Modelo | B(1) Codigo | C(2) Fabricante |
  D(3) Conexao Entrada | E(4) Conexao Saida |
  F(5) Fluido | G(6) T.Evap (C) | H(7) T.Cond (C) |
  I(8) Capacidade kcal/h | J(9) Capacidade Min kcal/h

Regras:
  - Categoria: Válvula de Expansão Termostática
  - Cada linha = 1 combinação modelo × fluido × T.Evap × T.Cond
  - capacidade_nominal do componente = maior capacidade encontrada para o modelo
  - Conexões normalizadas (remove espaços extras)

Uso:
  python scripts/importar_vet.py <arquivo.xlsx> [--dry-run]
"""
import sys
import asyncio
import argparse
import openpyxl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.componente import ComponenteTecnico, PerformanceComponente
from app.models.catalogo import Categoria, Fabricante, UnidadeMedida

CATEGORIA_NOME = "Válvula de Expansão Termostática"

COL_MODELO    = 0
COL_CODIGO    = 1
COL_FABRICANTE= 2
COL_CON_ENT   = 3
COL_CON_SAI   = 4
COL_FLUIDO    = 5
COL_T_EVAP    = 6
COL_T_COND    = 7
COL_CAP       = 8
COL_CAP_MIN   = 9

FLUIDO_MAP = {
    "R404": "R404A", "R404a": "R404A", "r404a": "R404A", "r404": "R404A",
    "R22":  "R22",   "r22":   "R22",
    "R290": "R290",  "R134a": "R134a", "R448A": "R448A",
}

def normalizar_fluido(f: str) -> str:
    return FLUIDO_MAP.get(f.strip(), f.strip())

def normalizar_conexao(c: str) -> str:
    return str(c).strip() if c else ""


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_MODELO]:
            continue
        dados.append({
            "modelo":    str(row[COL_MODELO]).strip(),
            "codigo":    str(row[COL_CODIGO]).strip() if row[COL_CODIGO] else None,
            "fabricante":str(row[COL_FABRICANTE]).strip() if row[COL_FABRICANTE] else "Generico",
            "con_ent":   normalizar_conexao(row[COL_CON_ENT]),
            "con_sai":   normalizar_conexao(row[COL_CON_SAI]),
            "fluido":    normalizar_fluido(str(row[COL_FLUIDO])) if row[COL_FLUIDO] else "R22",
            "t_evap":    int(row[COL_T_EVAP])   if row[COL_T_EVAP]  is not None else None,
            "t_cond":    int(row[COL_T_COND])   if row[COL_T_COND]  is not None else 40,
            "cap":       float(row[COL_CAP])     if row[COL_CAP]     is not None else None,
            "cap_min":   float(row[COL_CAP_MIN]) if row[COL_CAP_MIN] is not None else 0.0,
        })
    return dados


async def importar(caminho: str, dry_run: bool):
    dados = ler_excel(caminho)
    modelos_unicos  = sorted(set(d["modelo"]    for d in dados))
    fluidos_unicos  = sorted(set(d["fluido"]    for d in dados))
    t_evaps_unicos  = sorted(set(d["t_evap"]    for d in dados if d["t_evap"] is not None))
    t_conds_unicos  = sorted(set(d["t_cond"]    for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} linhas | {len(modelos_unicos)} modelos")
    print(f"[INFO] Modelos:  {modelos_unicos}")
    print(f"[INFO] Fluidos:  {fluidos_unicos}")
    print(f"[INFO] T.Evap:   {t_evaps_unicos}")
    print(f"[INFO] T.Cond:   {t_conds_unicos}")
    print(f"[INFO] Categoria: {CATEGORIA_NOME}")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    # Pre-calcular capacidade_nominal por modelo (maior valor de cap)
    cap_max_por_modelo: dict[str, float] = {}
    for d in dados:
        if d["cap"] is not None:
            atual = cap_max_por_modelo.get(d["modelo"], 0.0)
            if d["cap"] > atual:
                cap_max_por_modelo[d["modelo"]] = d["cap"]

    async with SessionLocal() as db:
        res = await db.execute(select(Categoria).where(Categoria.nome == CATEGORIA_NOME))
        categoria = res.scalar_one_or_none()
        if not categoria:
            print(f"[ERRO] Categoria '{CATEGORIA_NOME}' nao encontrada.")
            return

        comp_novos      = 0
        comp_existentes = 0
        perf_inseridas  = 0
        perf_atualizadas= 0
        cache_fab       = {}
        cache_comp      = {}

        for row in dados:
            modelo   = row["modelo"]
            fab_nome = row["fabricante"]
            fluido   = row["fluido"]
            t_evap   = row["t_evap"]
            t_cond   = row["t_cond"]
            cap      = row["cap"]
            cap_min  = row["cap_min"]

            if t_evap is None or cap is None:
                continue

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

            # --- Componente (1 por modelo) ---
            if modelo not in cache_comp:
                res = await db.execute(
                    select(ComponenteTecnico).where(
                        ComponenteTecnico.modelo       == modelo,
                        ComponenteTecnico.categoria_id == categoria.id,
                    )
                )
                comp = res.scalar_one_or_none()
                if not comp:
                    if not dry_run:
                        comp = ComponenteTecnico(
                            modelo             = modelo,
                            codigo_fabricante  = row["codigo"],
                            categoria_id       = categoria.id,
                            fabricante_id      = fab_id,
                            conexao_entrada    = row["con_ent"],
                            conexao_saida      = row["con_sai"],
                            capacidade_nominal = cap_max_por_modelo.get(modelo, 0.0),
                            dados_especificos  = {},
                            custo              = 0,
                        )
                        db.add(comp)
                        await db.flush()
                        comp_novos += 1
                        print(f"  [OK] VET: {modelo} | ent={row['con_ent']} sai={row['con_sai']}"
                              f" | cap_max={cap_max_por_modelo.get(modelo,0):.0f} kcal/h (id={comp.id})")
                    else:
                        print(f"  [DRY] VET seria criada: {modelo} | {row['con_ent']} → {row['con_sai']}"
                              f" | cap_max={cap_max_por_modelo.get(modelo,0):.0f} kcal/h")
                        cache_comp[modelo] = -1
                        continue
                else:
                    comp_existentes += 1
                cache_comp[modelo] = comp.id

            comp_id = cache_comp.get(modelo, -1)
            if comp_id == -1:
                continue

            # --- Performance ---
            if dry_run:
                print(f"    [DRY] {modelo} | {fluido} | T.Evap={t_evap}C | T.Cond={t_cond}C"
                      f" | {cap:.0f} kcal/h (min={cap_min:.0f})")
                continue

            res = await db.execute(
                select(PerformanceComponente).where(
                    PerformanceComponente.componente_id   == comp_id,
                    PerformanceComponente.fluido           == fluido,
                    PerformanceComponente.temp_evaporacao  == t_evap,
                    PerformanceComponente.temp_condensacao == t_cond,
                )
            )
            existente = res.scalar_one_or_none()
            if existente:
                existente.capacidade_kcalh     = cap
                existente.capacidade_min_kcalh = cap_min
                perf_atualizadas += 1
            else:
                db.add(PerformanceComponente(
                    componente_id       = comp_id,
                    fluido              = fluido,
                    temp_evaporacao     = t_evap,
                    temp_condensacao    = t_cond,
                    capacidade_kcalh    = cap,
                    capacidade_min_kcalh= cap_min,
                ))
                perf_inseridas += 1

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Importacao concluida!")
            print(f"  VETs novas:               {comp_novos}")
            print(f"  VETs ja existiam:         {comp_existentes}")
            print(f"  Performances inseridas:   {perf_inseridas}")
            print(f"  Performances atualizadas: {perf_atualizadas}")
        else:
            print(f"\n[DRY] Simulacao concluida — nada foi salvo.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(description="Importa VET Excel para o banco")
    parser.add_argument("arquivo",    help="Caminho do arquivo .xlsx")
    parser.add_argument("--dry-run",  action="store_true", help="Simula sem salvar")
    args = parser.parse_args()

    asyncio.run(importar(args.arquivo, args.dry_run))
