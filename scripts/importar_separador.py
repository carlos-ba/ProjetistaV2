"""
Importa Separadores de Líquido para o banco do Projetista V2.

Nomenclatura: "Separador de Líquido" (também conhecido como acumulador de sucção).

Formato esperado (colunas fixas):
  A(0) Modelo | B(1) Código | C(2) Fabricante |
  D(3) Conexão Entrada | E(4) Conexão Saída |
  F(5) Fluido | G(6) T.Evap (°C) |
  H(7) Capacidade Máx kW | I(8) Capacidade Mín kW

Regras:
  - Categoria: Separador de Liquido
  - Capacidade em kW → converte para kcal/h (× 860)
  - R134 → R134a | R404 → R404A
  - Cada linha = 1 combinação modelo × fluido × T.Evap
  - capacidade_nominal = maior cap_max encontrada para o modelo

Uso:
  python scripts/importar_separador.py <arquivo.xlsx> [--dry-run]
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

CATEGORIA_NOME = "Separador de Liquido"
KW_PARA_KCALH = 860.0   # 1 kW = 860 kcal/h

COL_MODELO    = 0
COL_CODIGO    = 1
COL_FABRICANTE= 2
COL_CON_ENT   = 3
COL_CON_SAI   = 4
COL_FLUIDO    = 5
COL_T_EVAP    = 6
COL_CAP_MAX   = 7   # kW
COL_CAP_MIN   = 8   # kW

FLUIDO_MAP = {
    "R134":  "R134a",
    "r134":  "R134a",
    "R134a": "R134a",
    "R404":  "R404A",
    "r404":  "R404A",
    "R404A": "R404A",
    "R22":   "R22",
    "r22":   "R22",
    "R290":  "R290",
}

def normalizar_fluido(f: str) -> str:
    return FLUIDO_MAP.get(f.strip(), f.strip())

def normalizar_conexao(c) -> str:
    return str(c).strip() if c else ""


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_MODELO]:
            continue
        cap_max_kw = row[COL_CAP_MAX]
        cap_min_kw = row[COL_CAP_MIN]
        dados.append({
            "modelo":    str(row[COL_MODELO]).strip(),
            "codigo":    str(row[COL_CODIGO]).strip() if row[COL_CODIGO] else None,
            "fabricante":str(row[COL_FABRICANTE]).strip() if row[COL_FABRICANTE] else "Generico",
            "con_ent":   normalizar_conexao(row[COL_CON_ENT]),
            "con_sai":   normalizar_conexao(row[COL_CON_SAI]),
            "fluido":    normalizar_fluido(str(row[COL_FLUIDO])) if row[COL_FLUIDO] else "R22",
            "t_evap":    int(row[COL_T_EVAP])    if row[COL_T_EVAP]    is not None else None,
            # Converter kW → kcal/h
            "cap_max":   round(float(cap_max_kw) * KW_PARA_KCALH, 1) if cap_max_kw is not None else None,
            "cap_min":   round(float(cap_min_kw) * KW_PARA_KCALH, 1) if cap_min_kw is not None else 0.0,
            "cap_max_kw": float(cap_max_kw) if cap_max_kw is not None else None,
        })
    return dados


async def importar(caminho: str, dry_run: bool):
    dados = ler_excel(caminho)
    modelos_unicos   = sorted(set(d["modelo"]    for d in dados))
    fluidos_unicos   = sorted(set(d["fluido"]    for d in dados))
    t_evaps_unicos   = sorted(set(d["t_evap"]    for d in dados if d["t_evap"] is not None))
    fabricantes_uniq = sorted(set(d["fabricante"] for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} linhas | {len(modelos_unicos)} modelos")
    print(f"[INFO] Fabricantes: {fabricantes_uniq}")
    print(f"[INFO] Fluidos: {fluidos_unicos}")
    print(f"[INFO] T.Evap: {t_evaps_unicos} C")
    print(f"[INFO] Categoria: {CATEGORIA_NOME}")
    print(f"[INFO] Conversao: kW x {KW_PARA_KCALH} = kcal/h")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    # Pre-calcular capacidade_nominal por modelo (maior cap_max em kcal/h)
    cap_max_por_modelo: dict[str, float] = {}
    for d in dados:
        if d["cap_max"] is not None:
            cap_max_por_modelo[d["modelo"]] = max(
                cap_max_por_modelo.get(d["modelo"], 0.0), d["cap_max"]
            )

    async with SessionLocal() as db:
        res = await db.execute(select(Categoria).where(Categoria.nome == CATEGORIA_NOME))
        categoria = res.scalar_one_or_none()
        if not categoria:
            print(f"[ERRO] Categoria '{CATEGORIA_NOME}' nao encontrada.")
            return

        comp_novos       = 0
        comp_existentes  = 0
        perf_inseridas   = 0
        perf_atualizadas = 0
        cache_fab        = {}
        cache_comp       = {}

        for row in dados:
            modelo   = row["modelo"]
            fab_nome = row["fabricante"]
            fluido   = row["fluido"]
            t_evap   = row["t_evap"]
            cap_max  = row["cap_max"]
            cap_min  = row["cap_min"]

            if t_evap is None or cap_max is None:
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
                            dados_especificos  = {"unidade_capacidade": "kcal/h", "fonte_kw": True},
                            custo              = 0,
                        )
                        db.add(comp)
                        await db.flush()
                        comp_novos += 1
                        print(f"  [OK] Separador: {modelo} | {row['con_ent']} | "
                              f"cap_max={cap_max_por_modelo.get(modelo,0):.0f} kcal/h "
                              f"({cap_max_por_modelo.get(modelo,0)/KW_PARA_KCALH:.1f} kW) (id={comp.id})")
                    else:
                        cap_kw = cap_max_por_modelo.get(modelo, 0) / KW_PARA_KCALH
                        print(f"  [DRY] Separador seria criado: {modelo} | {row['con_ent']} "
                              f"| cap_max={cap_max_por_modelo.get(modelo,0):.0f} kcal/h ({cap_kw:.1f} kW)")
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
                print(f"    [DRY] {modelo} | {fluido} | T.Evap={t_evap}C"
                      f" | {cap_max:.0f} kcal/h ({row['cap_max_kw']} kW)"
                      f" | min={cap_min:.0f} kcal/h")
                continue

            res = await db.execute(
                select(PerformanceComponente).where(
                    PerformanceComponente.componente_id   == comp_id,
                    PerformanceComponente.fluido           == fluido,
                    PerformanceComponente.temp_evaporacao  == t_evap,
                )
            )
            existente = res.scalar_one_or_none()
            if existente:
                existente.capacidade_kcalh     = cap_max
                existente.capacidade_min_kcalh = cap_min
                perf_atualizadas += 1
            else:
                db.add(PerformanceComponente(
                    componente_id        = comp_id,
                    fluido               = fluido,
                    temp_evaporacao      = t_evap,
                    temp_condensacao     = 45,   # nao aplicavel ao separador, valor padrao
                    capacidade_kcalh     = cap_max,
                    capacidade_min_kcalh = cap_min,
                ))
                perf_inseridas += 1

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Importacao concluida!")
            print(f"  Separadores inseridos:    {comp_novos}")
            print(f"  Separadores ja existiam:  {comp_existentes}")
            print(f"  Performances inseridas:   {perf_inseridas}")
            print(f"  Performances atualizadas: {perf_atualizadas}")
        else:
            print(f"\n[DRY] Simulacao concluida — nada foi salvo.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description="Importa Separadores de Liquido para o banco")
    parser.add_argument("arquivo",   help="Caminho do arquivo .xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar")
    args = parser.parse_args()
    asyncio.run(importar(args.arquivo, args.dry_run))
