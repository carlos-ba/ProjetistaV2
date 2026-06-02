"""
Importa tabela de isolamento para tubulação (espuma elastomérica Armacel).

Formato esperado (colunas fixas):
  A(0)  Ø Externo Cu mm
  B(1)  Ø Nominal Cu pol
  C(2)  Ø Nominal Fe pol
  D(3)  Ø Externo Fe mm
  E(4)  Diâmetro interno min-max (mm)
  F(5)  Ref. D  | G(6)  Esp. D mm
  H(7)  Ref. F  | I(8)  Esp. F mm
  J(9)  Ref. H  | K(10) Esp. H mm
  L(11) Ref. M  | M(12) Esp. M mm
  N(13) Ref. R  | O(14) Esp. R mm
  P(15) Ref. T  | Q(16) Esp. T mm

Padrões: D(6-7,5mm) | F(9-12mm) | H(13-16mm) | M(19-26mm) | R(25-32,5mm) | T(32-45mm)

Uso:
  python scripts/importar_isolamento.py <arquivo.xlsx> [--dry-run]
"""
import sys
import asyncio
import argparse
import openpyxl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.isolamento import IsolamentoTubulacao
from app.models.catalogo import Fabricante

FABRICANTE_NOME = "Armacel"

# Padrões e suas colunas (ref_col, esp_col)
PADROES = {
    "D": (5,  6),
    "F": (7,  8),
    "H": (9,  10),
    "M": (11, 12),
    "R": (13, 14),
    "T": (15, 16),
}

# Faixas de espessura por padrão (para documentação/validação)
FAIXAS = {
    "D": (6.0,  7.5),
    "F": (9.0,  12.0),
    "H": (13.0, 16.0),
    "M": (19.0, 26.0),
    "R": (25.0, 32.5),
    "T": (32.0, 45.0),
}


def parse_diametro_interno(texto: str):
    """Extrai min e max de string como '19.0 - 20,5' → (19.0, 20.5)"""
    if not texto:
        return None, None
    txt = str(texto).replace(",", ".").replace(" ", "")
    partes = txt.split("-")
    try:
        return float(partes[0]), float(partes[1])
    except Exception:
        return None, None


def ler_excel(caminho: str) -> list[dict]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    dados = []

    for row in ws.iter_rows(min_row=3, values_only=True):
        cu_mm = row[0]
        if cu_mm is None:
            continue
        try:
            cu_mm = float(cu_mm)
        except (ValueError, TypeError):
            continue

        fe_raw = row[3]
        fe_mm  = None
        if fe_raw not in (None, "-", "–"):
            try:
                fe_mm = float(str(fe_raw).replace(",", "."))
            except (ValueError, TypeError):
                pass

        d_int_min, d_int_max = parse_diametro_interno(row[4])

        for padrao, (col_ref, col_esp) in PADROES.items():
            ref = row[col_ref]
            esp = row[col_esp]
            if ref is None or esp is None:
                continue
            try:
                esp_val = float(str(esp).replace(",", "."))
            except (ValueError, TypeError):
                continue

            dados.append({
                "cu_mm":      cu_mm,
                "fe_mm":      fe_mm,
                "d_int_min":  d_int_min,
                "d_int_max":  d_int_max,
                "padrao":     padrao,
                "referencia": str(ref).strip(),
                "espessura":  esp_val,
            })
    return dados


async def importar(caminho: str, dry_run: bool):
    dados = ler_excel(caminho)

    padroes_cnt = {p: sum(1 for d in dados if d["padrao"] == p) for p in PADROES}
    diametros   = sorted(set(d["cu_mm"] for d in dados))

    print(f"\n[ARQ]  {Path(caminho).name}")
    print(f"[INFO] {len(dados)} registros | Fabricante: {FABRICANTE_NOME}")
    print(f"[INFO] Diâmetros Cu: {diametros}")
    print(f"[INFO] Por padrão: {padroes_cnt}")
    print(f"[INFO] Faixas: D(6-7.5) F(9-12) H(13-16) M(19-26) R(25-32.5) T(32-45) mm")
    print(f"{'[DRY RUN]' if dry_run else '[IMPORTACAO REAL]'}\n")

    async with SessionLocal() as db:
        # Garantir fabricante
        res = await db.execute(select(Fabricante).where(Fabricante.nome == FABRICANTE_NOME))
        fab = res.scalar_one_or_none()
        if not fab:
            if not dry_run:
                fab = Fabricante(nome=FABRICANTE_NOME)
                db.add(fab)
                await db.flush()
                print(f"  [NEW] Fabricante: {FABRICANTE_NOME} (id={fab.id})")
            else:
                print(f"  [DRY] Fabricante seria criado: {FABRICANTE_NOME}")

        if dry_run:
            # Mostrar amostra por padrão
            for padrao in PADROES:
                amostras = [d for d in dados if d["padrao"] == padrao][:3]
                for d in amostras:
                    print(f"  [DRY] Cu={d['cu_mm']}mm | Padrão={d['padrao']} | "
                          f"Ref={d['referencia']} | Esp={d['espessura']}mm")
            print(f"\n[DRY] {len(dados)} registros seriam importados.")
            return

        inseridos   = 0
        atualizados = 0
        fab_id      = fab.id

        for d in dados:
            res = await db.execute(
                select(IsolamentoTubulacao).where(
                    IsolamentoTubulacao.fabricante_id == fab_id,
                    IsolamentoTubulacao.padrao        == d["padrao"],
                    IsolamentoTubulacao.referencia    == d["referencia"],
                )
            )
            existente = res.scalar_one_or_none()
            if existente:
                existente.diametro_cu_mm       = d["cu_mm"]
                existente.diametro_fe_mm       = d["fe_mm"]
                existente.diametro_interno_min = d["d_int_min"]
                existente.diametro_interno_max = d["d_int_max"]
                existente.espessura_mm         = d["espessura"]
                atualizados += 1
            else:
                db.add(IsolamentoTubulacao(
                    fabricante_id        = fab_id,
                    diametro_cu_mm       = d["cu_mm"],
                    diametro_fe_mm       = d["fe_mm"],
                    diametro_interno_min = d["d_int_min"],
                    diametro_interno_max = d["d_int_max"],
                    padrao               = d["padrao"],
                    referencia           = d["referencia"],
                    espessura_mm         = d["espessura"],
                    custo                = 0,
                ))
                inseridos += 1

        await db.commit()
        print(f"[OK] Importacao concluida!")
        print(f"  Registros inseridos:   {inseridos}")
        print(f"  Registros atualizados: {atualizados}")

        # Resumo por padrão
        print(f"\n  Padrão | Registros | Faixa espessura")
        for padrao, (e_min, e_max) in FAIXAS.items():
            cnt = sum(1 for d in dados if d["padrao"] == padrao)
            if cnt:
                esps = [d["espessura"] for d in dados if d["padrao"] == padrao]
                print(f"    {padrao}    | {cnt:9} | {min(esps)} – {max(esps)} mm  (nominal {e_min}-{e_max})")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description="Importa isolamento de tubulacao")
    parser.add_argument("arquivo",   help="Caminho do arquivo .xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar")
    args = parser.parse_args()
    asyncio.run(importar(args.arquivo, args.dry_run))
