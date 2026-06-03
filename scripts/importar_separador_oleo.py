"""
Importa Separadores de Óleo RAC Brasil para o banco do Projetista V2.

Fonte: catálogo RAC Brasil — "Separador de óleo flange superior"
Temperatura de condensação base: 35°C
Fluidos: R22/R407C/R404A/R507 (coluna única) e R134a

Dados extraídos do PDF — não requer arquivo externo.

Uso:
  python scripts/importar_separador_oleo.py [--dry-run]
"""
import sys
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.componente import ComponenteTecnico, PerformanceComponente
from app.models.catalogo import Categoria, Fabricante

CATEGORIA_NOME = "Separador de Óleo"
FABRICANTE_NOME = "RAC"
T_COND = 35  # temperatura de condensação base do catálogo

# ── Dados extraídos do catálogo RAC Brasil ────────────────────────────────
# Estrutura: (modelo, codigo, conexao_solda, conexao_rosca, perf_R404A, perf_R134a)
# perf = {t_evap: cap_kcalh}

CATALOGO = [
    {
        "modelo":  "SOF 1/2\"S",
        "codigo":  "050-101",
        "conexao": '1/2"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 7140, -30: 7397, -20: 7653, -10: 7910,  5: 8420},
        "perf_R134a": {           -30: 4550, -20: 4765, -10: 4980,  5: 5500},
    },
    {
        "modelo":  "SOF 1/2\"R",
        "codigo":  "050-102",
        "conexao": '1/2" SAE',
        "tipo":    "Rosca",
        "perf_R404A": {-40: 7140, -30: 7397, -20: 7653, -10: 7910,  5: 8420},
        "perf_R134a": {           -30: 4550, -20: 4765, -10: 4980,  5: 5500},
    },
    {
        "modelo":  "SOF 5/8\"S",
        "codigo":  "050-103",
        "conexao": '5/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 14440, -30: 14843, -20: 15247, -10: 15650, 5: 16850},
        "perf_R134a": {            -30:  9110, -20:  9370, -10:  9630, 5: 11000},
    },
    {
        "modelo":  "SOF 5/8\"R",
        "codigo":  "050-104",
        "conexao": '5/8" SAE',
        "tipo":    "Rosca",
        "perf_R404A": {-40: 14440, -30: 14843, -20: 15247, -10: 15650, 5: 16850},
        "perf_R134a": {            -30:  9110, -20:  9370, -10:  9630, 5: 11000},
    },
    {
        "modelo":  "SOF 3/4\"R",
        "codigo":  "050-125",
        "conexao": '3/4" SAE',
        "tipo":    "Rosca",
        "perf_R404A": {-40: 16860, -30: 18120, -20: 19380, -10: 20640, 5: 22450},
        "perf_R134a": {            -30: 12040, -20: 12640, -10: 13240, 5: 14790},
    },
    {
        "modelo":  "SOF 7/8\"S",
        "codigo":  "050-105",
        "conexao": '7/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 21590, -30: 22247, -20: 22903, -10: 23560, 5: 25370},
        "perf_R134a": {            -30: 13500, -20: 14060, -10: 14620, 5: 16590},
    },
    {
        "modelo":  "SOF 1.1/8\"S",
        "codigo":  "050-106",
        "conexao": '1.1/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 28720, -30: 29580, -20: 30440, -10: 31300, 5: 33880},
        "perf_R134a": {            -30: 18230, -20: 19435, -10: 20640, 5: 22100},
    },
    {
        "modelo":  "SOF 1.3/8\"S",
        "codigo":  "050-107",
        "conexao": '1.3/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 32670, -30: 33760, -20: 34850, -10: 35940, 5: 38950},
        "perf_R134a": {            -30: 20980, -20: 22355, -10: 23730, 5: 25370},
    },
    {
        "modelo":  "SOF 1.5/8\"S",
        "codigo":  "050-114",
        "conexao": '1.5/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 48420, -30: 50053, -20: 51687, -10: 53320, 5: 56160},
        "perf_R134a": {            -30: 32340, -20: 33930, -10: 35520, 5: 39300},
    },
    {
        "modelo":  "SOF 2.1/8\"S",
        "codigo":  "050-109",
        "conexao": '2.1/8"',
        "tipo":    "Solda",
        "perf_R404A": {-40: 75770, -30: 78380, -20: 80990, -10: 83600, 5: 94600},
        "perf_R134a": {            -30: 57450, -20: 60330, -10: 63210, 5: 69580},
    },
]


async def importar(dry_run: bool):
    print(f"\n[INFO] Separadores de Óleo RAC Brasil — {len(CATALOGO)} modelos")
    print(f"[INFO] Categoria: {CATEGORIA_NOME}")
    print(f"[INFO] T.Cond base: {T_COND}°C")
    print(f"[INFO] Fluidos: R404A (R22/R407C/R404A/R507) + R134a")
    print(f"{'[DRY RUN]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:

        # ── Categoria ─────────────────────────────────────────────────────
        res = await db.execute(select(Categoria).where(Categoria.nome == CATEGORIA_NOME))
        categoria = res.scalar_one_or_none()
        if not categoria:
            if dry_run:
                print(f"  [DRY] Categoria '{CATEGORIA_NOME}' seria criada")
                categoria_id = -1
            else:
                categoria = Categoria(nome=CATEGORIA_NOME)
                db.add(categoria)
                await db.flush()
                print(f"  [NEW] Categoria: {CATEGORIA_NOME} (id={categoria.id})")
                categoria_id = categoria.id
        else:
            categoria_id = categoria.id
            print(f"  [OK]  Categoria: {CATEGORIA_NOME} (id={categoria_id})")

        # ── Fabricante ────────────────────────────────────────────────────
        res = await db.execute(select(Fabricante).where(Fabricante.nome == FABRICANTE_NOME))
        fabricante = res.scalar_one_or_none()
        if not fabricante:
            if dry_run:
                print(f"  [DRY] Fabricante '{FABRICANTE_NOME}' seria criado")
                fab_id = -1
            else:
                fabricante = Fabricante(nome=FABRICANTE_NOME)
                db.add(fabricante)
                await db.flush()
                print(f"  [NEW] Fabricante: {FABRICANTE_NOME} (id={fabricante.id})")
                fab_id = fabricante.id
        else:
            fab_id = fabricante.id
            print(f"  [OK]  Fabricante: {FABRICANTE_NOME} (id={fab_id})\n")

        comp_novos = 0; comp_exist = 0
        perf_ins   = 0; perf_upd  = 0

        for item in CATALOGO:
            modelo  = item["modelo"]
            codigo  = item["codigo"]
            conexao = item["conexao"]
            tipo    = item["tipo"]
            cap_max = max(item["perf_R404A"].values())  # capacidade nominal = maior cap R404A

            # ── Componente ────────────────────────────────────────────────
            if not dry_run and categoria_id != -1:
                res = await db.execute(
                    select(ComponenteTecnico).where(
                        ComponenteTecnico.modelo       == modelo,
                        ComponenteTecnico.categoria_id == categoria_id,
                    )
                )
                comp = res.scalar_one_or_none()
                if not comp:
                    comp = ComponenteTecnico(
                        modelo             = modelo,
                        codigo_fabricante  = codigo,
                        categoria_id       = categoria_id,
                        fabricante_id      = fab_id,
                        conexao_entrada    = conexao,
                        conexao_saida      = conexao,
                        capacidade_nominal = float(cap_max),
                        dados_especificos  = {"tipo_conexao": tipo, "t_cond_base": T_COND},
                        custo              = 0,
                    )
                    db.add(comp)
                    await db.flush()
                    comp_novos += 1
                    print(f"  [OK] {modelo} | {tipo} {conexao} | cap_max={cap_max:,} kcal/h (id={comp.id})")
                else:
                    comp_exist += 1
                    print(f"  [--] {modelo} já existe (id={comp.id})")
                comp_id = comp.id
            else:
                print(f"  [DRY] {modelo} | {tipo} {conexao} | cap_max={cap_max:,} kcal/h")
                comp_id = -1

            # ── Performances ──────────────────────────────────────────────
            todos_fluidos = [
                ("R404A", item["perf_R404A"]),
                ("R22",   item["perf_R404A"]),   # R22 usa mesma coluna do catálogo
                ("R134a", item["perf_R134a"]),
            ]

            for fluido, perfs in todos_fluidos:
                for t_evap, cap_kcalh in perfs.items():
                    if dry_run:
                        print(f"    [DRY] {modelo} | {fluido} | T.Evap={t_evap}°C | {cap_kcalh:,} kcal/h")
                        continue

                    res = await db.execute(
                        select(PerformanceComponente).where(
                            PerformanceComponente.componente_id   == comp_id,
                            PerformanceComponente.fluido           == fluido,
                            PerformanceComponente.temp_evaporacao  == t_evap,
                            PerformanceComponente.temp_condensacao == T_COND,
                        )
                    )
                    existente = res.scalar_one_or_none()
                    if existente:
                        existente.capacidade_kcalh     = float(cap_kcalh)
                        existente.capacidade_min_kcalh = 0.0
                        perf_upd += 1
                    else:
                        db.add(PerformanceComponente(
                            componente_id        = comp_id,
                            fluido               = fluido,
                            temp_evaporacao      = t_evap,
                            temp_condensacao     = T_COND,
                            capacidade_kcalh     = float(cap_kcalh),
                            capacidade_min_kcalh = 0.0,
                        ))
                        perf_ins += 1

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Importação concluída!")
            print(f"  Componentes inseridos:    {comp_novos}")
            print(f"  Componentes já existiam:  {comp_exist}")
            print(f"  Performances inseridas:   {perf_ins}")
            print(f"  Performances atualizadas: {perf_upd}")
            total_perf = comp_novos * (5 + 5 + 4 + 4)  # R404A+R22 (5 pts) + R134a (4 pts) por modelo
            print(f"  Total esperado: {len(CATALOGO)} modelos × ~18 performances = ~{len(CATALOGO)*18}")
        else:
            print(f"\n[DRY] Simulação concluída — nada foi salvo.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description="Importa Separadores de Óleo RAC Brasil")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar")
    args = parser.parse_args()
    asyncio.run(importar(args.dry_run))
