"""
Importa evaporadoras de arquivo Excel para o banco do Projetista V2.

Formato esperado (colunas fixas):
  A(0) Modelo | B(1) Fabricante | C(2) Fluido |
  D(3)  Q +10C | E(4)  Q +5C | F(5)  Q  0C | G(6)  Q -5C  |
  H(7)  Q -10C | I(8)  Q -15C | J(9)  Q -20C | K(10) Q -25C |
  L(11) Q -30C | M(12) Q -35C | N(13) Q -40C |   <- kcal/h
  O(14) Qt Ventiladores | P(15) Vazao m3/h | Q(16) Diametro mm | R(17) Flecha m

Regras:
  - Categoria gravada: Evaporadora
  - temp_ambiente: 32C fixo (condicao padrao de catalogo)
  - consumo_kw: nao aplicavel (evaporadora nao tem compressor)
  - Fluido "R404" normalizado para "R404A"
  - Mesmo modelo com fluidos diferentes = 1 equipamento + N performances

Uso:
  python scripts/importar_evaporadoras.py <arquivo.xlsx> [--delta-t 8] [--dry-run]
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

# Temperaturas de evaporacao (colunas D a N)
TEMPS_EVAP = [10, 5, 0, -5, -10, -15, -20, -25, -30, -35, -40]

# Indices das colunas (0-based)
COL_MODELO     = 0
COL_FABRICANTE = 1
COL_FLUIDO     = 2
COL_CAP_INICIO = 3   # D → Q +10C  ate  N → Q -40C  (11 colunas)
COL_QT_VENT    = 14  # O
COL_VAZAO_AR   = 15  # P
COL_DIAM_VENT  = 16  # Q
COL_FLECHA_AR  = 17  # R

# Temperatura de condensacao padrao de catalogo para evaporadoras
T_COND_PADRAO = 32

# Normalizacao de fluidos
FLUIDO_MAP = {
    "R404":  "R404A",
    "R404a": "R404A",
    "r404a": "R404A",
    "r404":  "R404A",
    "R22":   "R22",
    "r22":   "R22",
    "R290":  "R290",
    "R134a": "R134a",
    "R448A": "R448A",
}


def normalizar_fluido(fluido: str) -> str:
    return FLUIDO_MAP.get(fluido.strip(), fluido.strip())


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_MODELO]:
            continue
        item = {
            "modelo":     str(row[COL_MODELO]).strip(),
            "fabricante": str(row[COL_FABRICANTE]).strip() if row[COL_FABRICANTE] else "Generico",
            "fluido":     normalizar_fluido(str(row[COL_FLUIDO])) if row[COL_FLUIDO] else "R404A",
            "qt_vent":    int(row[COL_QT_VENT])  if row[COL_QT_VENT]  else 0,
            "vazao_ar":   int(row[COL_VAZAO_AR]) if row[COL_VAZAO_AR] else 0,
            "diam_vent":  int(row[COL_DIAM_VENT]) if row[COL_DIAM_VENT] else 0,
            "flecha_ar":  int(row[COL_FLECHA_AR]) if row[COL_FLECHA_AR] else 0,
        }
        for i, t in enumerate(TEMPS_EVAP):
            item[f"cap_{t}"] = row[COL_CAP_INICIO + i]
        dados.append(item)
    return dados


async def importar(caminho: str, delta_t: float, dry_run: bool):
    dados = ler_excel(caminho)
    modelos_unicos = sorted(set(d["modelo"] for d in dados))
    fluidos_unicos = sorted(set(d["fluido"] for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} linhas | {len(modelos_unicos)} modelos | fluidos: {fluidos_unicos}")
    print(f"[INFO] Temperaturas de evaporacao: {TEMPS_EVAP}")
    print(f"[INFO] T.Cond padrao (catalogo): {T_COND_PADRAO}C | Delta T: {delta_t}C")
    print(f"[INFO] Categoria: Evaporadora")
    print(f"{'[DRY RUN - nada sera salvo]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:
        res = await db.execute(select(UnidadeMedida).where(UnidadeMedida.id == 1))
        unidade = res.scalar_one_or_none()

        res = await db.execute(select(Categoria).where(Categoria.nome == "Evaporadora"))
        categoria = res.scalar_one_or_none()

        if not unidade or not categoria:
            print("[ERRO] Unidade id=1 ou categoria 'Evaporadora' nao encontrada.")
            return

        equip_novos      = 0
        equip_existentes = 0
        perf_inseridas   = 0
        perf_atualizadas = 0
        cache_fab        = {}   # nome → id
        cache_equip      = {}   # modelo → id

        for row in dados:
            modelo    = row["modelo"]
            fab_nome  = row["fabricante"]
            fluido    = row["fluido"]

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

            # --- Equipamento (1 por modelo, independente do fluido) ---
            if modelo not in cache_equip:
                res = await db.execute(select(Equipamento).where(Equipamento.modelo == modelo))
                equip = res.scalar_one_or_none()
                if not equip:
                    if not dry_run:
                        equip = Equipamento(
                            modelo               = modelo,
                            categoria_id         = categoria.id,
                            fabricante_id        = fab_id,
                            unidade_medida_id    = unidade.id,
                            custo                = 0,
                            qtde_ventiladores    = row["qt_vent"],
                            diametro_ventilador_mm = row["diam_vent"],
                            vazao_ar_m3h         = row["vazao_ar"],
                            flecha_ar_m          = row["flecha_ar"],
                        )
                        db.add(equip)
                        await db.flush()
                        equip_novos += 1
                        print(f"  [OK] Equipamento: {modelo} | {row['qt_vent']} vent | "
                              f"{row['vazao_ar']} m3/h | {row['diam_vent']}mm | {row['flecha_ar']}m flecha (id={equip.id})")
                    else:
                        print(f"  [DRY] Equipamento seria criado: {modelo} | "
                              f"qt_vent={row['qt_vent']} | vazao={row['vazao_ar']} m3/h")
                        cache_equip[modelo] = -1
                        continue
                else:
                    equip_existentes += 1
                cache_equip[modelo] = equip.id

            equip_id = cache_equip.get(modelo, -1)
            if equip_id == -1:
                continue

            # --- Performances (1 por temperatura de evaporacao) ---
            for t_evap in TEMPS_EVAP:
                cap_val = row.get(f"cap_{t_evap}")
                if cap_val is None:
                    continue
                try:
                    cap = int(float(cap_val))
                except (ValueError, TypeError):
                    continue

                if dry_run:
                    print(f"    [DRY] {modelo} | {fluido} | T.Cond={T_COND_PADRAO}C"
                          f" | T.Evap={t_evap}C | {cap} kcal/h")
                    continue

                res = await db.execute(
                    select(PerformanceEquipamento).where(
                        PerformanceEquipamento.equipamento_id   == equip_id,
                        PerformanceEquipamento.fluido            == fluido,
                        PerformanceEquipamento.temp_ambiente  == T_COND_PADRAO,
                        PerformanceEquipamento.temp_evaporacao   == t_evap,
                        PerformanceEquipamento.delta_t           == delta_t,
                    )
                )
                existente = res.scalar_one_or_none()
                if existente:
                    existente.capacidade = cap
                    perf_atualizadas += 1
                else:
                    db.add(PerformanceEquipamento(
                        equipamento_id   = equip_id,
                        fluido           = fluido,
                        temp_ambiente = T_COND_PADRAO,
                        temp_evaporacao  = t_evap,
                        delta_t          = delta_t,
                        capacidade       = cap,
                        consumo_kw       = None,   # evaporadora nao tem compressor
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

    parser = argparse.ArgumentParser(description="Importa evaporadoras Excel para o banco")
    parser.add_argument("arquivo",    help="Caminho do arquivo .xlsx")
    parser.add_argument("--delta-t", type=float, default=8.0,
                        help="Delta T do evaporador em graus C (padrao: 8)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula a importacao sem salvar nada")
    args = parser.parse_args()

    asyncio.run(importar(args.arquivo, args.delta_t, args.dry_run))


