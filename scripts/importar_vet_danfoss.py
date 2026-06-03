"""
Importa VETs da planilha Danfoss (formato especifico).

Colunas da planilha:
  A(0) Modelo | B(1) Fabricante | C(2) Fluido |
  D(3) T.Evap | E(4) T.Cond |
  F(5) Capacidade kcal/h | G(6) Capacidade min kcal/h |
  H(7) Codigo | I(8) Conexao Entrada | J(9) Conexao Saida | K(10) Custo

Uso:
  python scripts/importar_vet_danfoss.py <arquivo.xlsx> [--dry-run]
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
from app.models.catalogo import Categoria, Fabricante

CATEGORIA_NOME = "Válvula de Expansão Termostática"

COL_MODELO    = 0
COL_FABRICANTE= 1
COL_FLUIDO    = 2
COL_T_EVAP    = 3
COL_T_COND    = 4
COL_CAP       = 5
COL_CAP_MIN   = 6
COL_CODIGO    = 7
COL_CON_ENT   = 8
COL_CON_SAI   = 9
COL_CUSTO     = 10

FLUIDO_MAP = {
    "R404A": "R404A", "R404": "R404A",
    "R22":   "R22",   "R290": "R290",
}


def normalizar(v) -> str:
    return str(v).strip() if v not in (None, "-", "") else ""


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_MODELO]:
            continue
        fluido_raw = normalizar(row[COL_FLUIDO])
        dados.append({
            "modelo":    normalizar(row[COL_MODELO]),
            "fabricante":normalizar(row[COL_FABRICANTE]) or "Danfoss",
            "fluido":    FLUIDO_MAP.get(fluido_raw, fluido_raw),
            "t_evap":    int(row[COL_T_EVAP])   if row[COL_T_EVAP]   is not None else None,
            "t_cond":    int(row[COL_T_COND])   if row[COL_T_COND]   is not None else 40,
            "cap":       float(row[COL_CAP])     if row[COL_CAP]      is not None else None,
            "cap_min":   float(row[COL_CAP_MIN]) if row[COL_CAP_MIN]  is not None else 0.0,
            "codigo":    normalizar(row[COL_CODIGO])  or None,
            "con_ent":   normalizar(row[COL_CON_ENT]) or "3/8\"",
            "con_sai":   normalizar(row[COL_CON_SAI]) or "1/2\"",
            "custo":     float(row[COL_CUSTO]) if row[COL_CUSTO] else 0,
        })
    return dados


async def importar(caminho: str, dry_run: bool):
    dados = ler_excel(caminho)
    modelos = sorted(set(d["modelo"] for d in dados))
    fluidos = sorted(set(d["fluido"] for d in dados))
    t_evaps = sorted(set(d["t_evap"] for d in dados if d["t_evap"] is not None))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} linhas | {len(modelos)} modelos: {modelos}")
    print(f"[INFO] Fluidos: {fluidos}")
    print(f"[INFO] T.Evap: {t_evaps}")
    print(f"[INFO] Categoria: {CATEGORIA_NOME}")
    print(f"{'[DRY RUN]' if dry_run else '[IMPORTACAO REAL]'}\n")

    # Capacidade nominal por modelo (maior valor)
    cap_max = {}
    for d in dados:
        if d["cap"] is not None:
            cap_max[d["modelo"]] = max(cap_max.get(d["modelo"], 0), d["cap"])

    async with SessionLocal() as db:
        res = await db.execute(select(Categoria).where(Categoria.nome == CATEGORIA_NOME))
        categoria = res.scalar_one_or_none()
        if not categoria:
            print(f"[ERRO] Categoria '{CATEGORIA_NOME}' nao encontrada.")
            return

        cache_fab  = {}
        cache_comp = {}
        comp_novos = 0; comp_exist = 0; perf_ins = 0; perf_upd = 0

        for d in dados:
            modelo = d["modelo"]; fab_nome = d["fabricante"]
            t_evap = d["t_evap"]; cap = d["cap"]; cap_min = d["cap_min"]

            if t_evap is None or cap is None:
                continue

            # Fabricante
            if fab_nome not in cache_fab:
                res = await db.execute(select(Fabricante).where(Fabricante.nome == fab_nome))
                fab = res.scalar_one_or_none()
                if not fab:
                    if not dry_run:
                        fab = Fabricante(nome=fab_nome)
                        db.add(fab); await db.flush()
                        print(f"  [NEW] Fabricante: {fab_nome} (id={fab.id})")
                    else:
                        print(f"  [DRY] Fabricante: {fab_nome}")
                        cache_fab[fab_nome] = -1; continue
                cache_fab[fab_nome] = fab.id

            fab_id = cache_fab[fab_nome]
            if fab_id == -1: continue

            # Componente (1 por modelo)
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
                            codigo_fabricante  = d["codigo"],
                            categoria_id       = categoria.id,
                            fabricante_id      = fab_id,
                            conexao_entrada    = d["con_ent"],
                            conexao_saida      = d["con_sai"],
                            capacidade_nominal = cap_max.get(modelo, 0),
                            dados_especificos  = {"fluido": d["fluido"]},
                            custo              = d["custo"],
                        )
                        db.add(comp); await db.flush()
                        comp_novos += 1
                        print(f"  [OK] VET: {modelo} | {d['con_ent']}→{d['con_sai']} | cap_max={cap_max.get(modelo,0):.0f} kcal/h (id={comp.id})")
                    else:
                        print(f"  [DRY] VET: {modelo} | cap_max={cap_max.get(modelo,0):.0f} kcal/h")
                        cache_comp[modelo] = -1; continue
                else:
                    comp_exist += 1
                cache_comp[modelo] = comp.id

            comp_id = cache_comp.get(modelo, -1)
            if comp_id == -1: continue

            if dry_run:
                print(f"    [DRY] {modelo} | {d['fluido']} | Tevap={t_evap} | Tcond={d['t_cond']} | {cap:.0f}/{cap_min:.0f} kcal/h")
                continue

            # Performance
            res = await db.execute(
                select(PerformanceComponente).where(
                    PerformanceComponente.componente_id   == comp_id,
                    PerformanceComponente.fluido           == d["fluido"],
                    PerformanceComponente.temp_evaporacao  == t_evap,
                    PerformanceComponente.temp_condensacao == d["t_cond"],
                )
            )
            existente = res.scalar_one_or_none()
            if existente:
                existente.capacidade_kcalh = cap; existente.capacidade_min_kcalh = cap_min
                perf_upd += 1
            else:
                db.add(PerformanceComponente(
                    componente_id        = comp_id,
                    fluido               = d["fluido"],
                    temp_evaporacao      = t_evap,
                    temp_condensacao     = d["t_cond"],
                    capacidade_kcalh     = cap,
                    capacidade_min_kcalh = cap_min,
                ))
                perf_ins += 1

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Concluido!")
            print(f"  VETs novas: {comp_novos} | existentes: {comp_exist}")
            print(f"  Performances inseridas: {perf_ins} | atualizadas: {perf_upd}")
        else:
            print(f"\n[DRY] {len(dados)} registros seriam importados.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(importar(args.arquivo, args.dry_run))
