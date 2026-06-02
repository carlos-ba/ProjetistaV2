"""
Importa dados de equipamentos de arquivos Excel para o banco do Projetista V2.

Formato esperado (colunas fixas):
  A(0) Modelo | B(1) Fabricante | C(2) Fluido | D(3) HP | E(4) T.Amb(C) |
  F(5)  Q +5C  | G(6)  Q  0C | H(7)  Q -5C | I(8)  Q -10C |
  J(9)  Q -15C | K(10) Q -20C | L(11) Q -25C | M(12) Q -30C |  <- kcal/h
  N(13) P +5C  | O(14) P  0C | P(15) P -5C | Q(16) P -10C |
  R(17) P -15C | S(18) P -20C | T(19) P -25C | U(20) P -30C |  <- kW

Uso:
  python scripts/importar_excel.py <arquivo.xlsx> [--delta-t 8] [--dry-run]
"""
import sys
import asyncio
import argparse
import openpyxl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.equipamento import Equipamento, PerformanceEquipamento
from app.models.catalogo import Categoria, Fabricante, UnidadeMedida

# Temperaturas de evaporacao nas colunas F-M (capacidade) e N-U (potencia)
TEMPS_EVAP = [5, 0, -5, -10, -15, -20, -25, -30]

# Indices das colunas (0-based)
COL_MODELO      = 0
COL_FABRICANTE  = 1
COL_FLUIDO      = 2
COL_HP          = 3
COL_T_AMB       = 4
COL_CAP_INICIO  = 5   # F → Q +5C  ate M → Q -30C
COL_POT_INICIO  = 13  # N → P +5C  ate U → P -30C


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_MODELO]:
            continue
        item = {
            "modelo":      str(row[COL_MODELO]).strip(),
            "fabricante":  str(row[COL_FABRICANTE]).strip() if row[COL_FABRICANTE] else "Generico",
            "fluido":      str(row[COL_FLUIDO]).strip()     if row[COL_FLUIDO]      else "R404A",
            "t_amb":       row[COL_T_AMB],
        }
        for i, t in enumerate(TEMPS_EVAP):
            item[f"cap_{t}"] = row[COL_CAP_INICIO + i]
            item[f"pot_{t}"] = row[COL_POT_INICIO + i]
        dados.append(item)
    return dados


async def importar(caminho: str, delta_t: float, dry_run: bool):
    dados = ler_excel(caminho)

    print(f"\n[ARQ] {Path(caminho).name}")
    print(f"[INFO] {len(dados)} linhas | {len(set(d['modelo'] for d in dados))} modelos unicos")
    print(f"[INFO] Temperaturas de evaporacao: {TEMPS_EVAP}")
    print(f"[INFO] Delta T: {delta_t}C | Potencia: kW | Capacidade: kcal/h")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:
        res = await db.execute(select(UnidadeMedida).where(UnidadeMedida.id == 1))
        unidade = res.scalar_one_or_none()

        res = await db.execute(select(Categoria).where(Categoria.nome == "Unidade Condensadora"))
        categoria = res.scalar_one_or_none()

        if not unidade or not categoria:
            print("[ERRO] Unidade id=1 ou categoria 'Condensadora' nao encontrada.")
            return

        equip_novos = 0
        equip_existentes = 0
        perf_inseridas = 0
        perf_atualizadas = 0
        modelos_cache = {}

        for row in dados:
            modelo      = row["modelo"]
            fab_nome    = row["fabricante"]
            fluido      = row["fluido"]
            t_amb       = row["t_amb"]

            if t_amb is None:
                continue

            t_cond = int(t_amb)  # T.Amb gravado direto (padrao de mercado)

            # --- Fabricante ---
            if fab_nome not in modelos_cache:
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
                        continue
                modelos_cache[f"fab_{fab_nome}"] = fab.id

            fab_id = modelos_cache.get(f"fab_{fab_nome}")

            # --- Equipamento ---
            if modelo not in modelos_cache:
                res = await db.execute(select(Equipamento).where(Equipamento.modelo == modelo))
                equip = res.scalar_one_or_none()
                if not equip:
                    if not dry_run:
                        equip = Equipamento(
                            modelo=modelo,
                            categoria_id=categoria.id,
                            fabricante_id=fab_id,
                            unidade_medida_id=unidade.id,
                            custo=0,
                            qtde_ventiladores=1,
                            diametro_ventilador_mm=0,
                            vazao_ar_m3h=0,
                            flecha_ar_m=0,
                        )
                        db.add(equip)
                        await db.flush()
                        equip_novos += 1
                        print(f"  [OK] Equipamento criado: {modelo} (id={equip.id})")
                    else:
                        print(f"  [DRY] Equipamento seria criado: {modelo}")
                        modelos_cache[modelo] = -1
                        continue
                else:
                    equip_existentes += 1
                modelos_cache[modelo] = equip.id

            equip_id = modelos_cache.get(modelo, -1)
            if equip_id == -1:
                continue

            # --- Performances (uma por temperatura de evaporacao) ---
            for t_evap in TEMPS_EVAP:
                cap_val = row.get(f"cap_{t_evap}")
                pot_val = row.get(f"pot_{t_evap}")

                if cap_val is None:
                    continue

                try:
                    cap    = int(float(cap_val))
                    pot_kw = round(float(pot_val), 3) if pot_val is not None else None
                except (ValueError, TypeError):
                    continue

                if dry_run:
                    print(f"    [DRY] {modelo} | {fluido} | T.Amb={t_cond}C | Tevap={t_evap}C"
                          f" | {cap} kcal/h | {pot_kw} kW")
                    continue

                res = await db.execute(
                    select(PerformanceEquipamento).where(
                        PerformanceEquipamento.equipamento_id == equip_id,
                        PerformanceEquipamento.fluido         == fluido,
                        PerformanceEquipamento.temp_ambiente == t_cond,
                        PerformanceEquipamento.temp_evaporacao  == t_evap,
                        PerformanceEquipamento.delta_t          == delta_t,
                    )
                )
                existente = res.scalar_one_or_none()
                if existente:
                    existente.capacidade  = cap
                    existente.consumo_kw  = pot_kw
                    perf_atualizadas += 1
                else:
                    db.add(PerformanceEquipamento(
                        equipamento_id  = equip_id,
                        fluido          = fluido,
                        temp_ambiente = t_cond,
                        temp_evaporacao  = t_evap,
                        delta_t         = delta_t,
                        capacidade      = cap,
                        consumo_kw      = pot_kw,
                    ))
                    perf_inseridas += 1

        if not dry_run:
            await db.commit()
            print(f"\n[OK] Importacao concluida!")
            print(f"  Equipamentos novos:       {equip_novos}")
            print(f"  Equipamentos ja existiam: {equip_existentes}")
            print(f"  Performances inseridas:   {perf_inseridas}")
            print(f"  Performances atualizadas: {perf_atualizadas}")
        else:
            print(f"\n[DRY] Simulacao concluida — nada foi salvo.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(description="Importa Excel de equipamentos para o banco")
    parser.add_argument("arquivo",     help="Caminho do arquivo .xlsx")
    parser.add_argument("--delta-t",  type=float, default=8.0,
                        help="Delta T do evaporador em graus C (padrao: 8)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Simula a importacao sem salvar nada")
    args = parser.parse_args()

    asyncio.run(importar(args.arquivo, args.delta_t, args.dry_run))


