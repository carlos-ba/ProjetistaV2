"""Importa equipamentos (UC ou Evaporadoras) + performance de uma planilha Excel.

Uso:
    cd backend
    ..\.venv\Scripts\python.exe scripts\importar_equipamentos.py <planilha.xlsx> "Unidade Condensadora"
    ..\.venv\Scripts\python.exe scripts\importar_equipamentos.py <planilha.xlsx> "Evaporadora"

Planilha (formato dos templates gerados, colunas lidas pelo cabeçalho — ordem
não importa, colunas ausentes ficam None/são puladas):

    Aba "Equipamentos": modelo | fabricante | qtde_ventiladores | diametro_ventilador_mm |
        vazao_ar_m3h | flecha_ar_m | volume_interno_kg | conexao_liquido | conexao_succao |
        custo | tipo_motor | comprimento_mm | altura_mm | profundidade_mm | peso_liquido_kg |
        ruido_dba | carga_refrigerante_kg | volume_deslocado_m3h | potencia_nominal_hp |
        motor_ventilador_corrente_a | motor_ventilador_potencia_w |
        capacitor_marcha_especificacao | resistencia_carter_especificacao | tanque_liquido_l
        (tipo_motor...carga_refrigerante_kg vieram do catálogo Mipal Hd/Hdl400 Pro; as 7
        últimas vieram do catálogo Bitzer Combat/Combat+/BIG CDU — todas opcionais, ver
        `project_evolucao_dados_evaporador`/`project_evolucao_dados_uc` na memória)

    Aba "Performance": modelo | fluido | T_ambiente_C | temp_evaporacao_C | delta_t |
        capacidade_kcalh | consumo_kw | tipo_motor | usa_fator_correcao
        (tipo_motor e usa_fator_correcao são opcionais)

    Aba "Variantes Eletricas" (opcional, pulada se a planilha não tiver): modelo | tipo_motor |
        tensao | fase | frequencia_hz | vazao_ar_m3h | potencia_w | corrente_a |
        codigo_fabricante | corrente_partida_a
        (as 2 últimas são novas e opcionais — achado no catálogo Bitzer: aqui a "variante
        elétrica" é o compressor da UC por tensão, não o motor do ventilador; código de
        fabricante muda por variante de tensão, e corrente_partida_a é o LRA ao lado do
        corrente_a/FLA)

    Aba "Resistencia Degelo" (opcional): modelo | tensao | potencia_individual_w |
        corrente_a | consumo_nao_equilibrado
        (aplica a TODOS os equipamentos daquele modelo, AC e EC — a resistência de
        degelo não muda com o tipo de motor)

    Aba "Fatores Correcao" (opcional, independente de modelo — por fabricante):
        fabricante | fluido_base | fluido | fator

Comportamento:
    - PULA as linhas cinza/itálicas (referência dos templates) — só importa as linhas novas.
    - Cria fabricante automaticamente se não existir.
    - Equipamento: upsert por (modelo + fabricante + categoria + tipo_motor).
    - Se `modelo` tiver mais de uma variante de tipo_motor cadastrada e a linha de
      Performance/Variantes Eletricas não informar `tipo_motor`, a linha é pulada com
      aviso (ambíguo demais pra adivinhar).
    - Performance: upsert pela chave única (equipamento + fluido + T.Amb + T.Evap + delta_t).
    - Linhas de performance cujo modelo não está na aba Equipamentos são buscadas no banco;
      se o modelo não existir em lugar nenhum, a linha é pulada com aviso.
"""
import asyncio
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal  # noqa: E402
from app.models.catalogo import Categoria, Fabricante, UnidadeMedida  # noqa: E402
from app.models.equipamento import (  # noqa: E402
    Equipamento, PerformanceEquipamento,
    EquipamentoVarianteEletrica, EquipamentoResistenciaDegelo, FatorCorrecaoFluido,
)

REF_COLOR = "808080"  # cinza das linhas de referência dos templates


def _num(v):
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _int(v):
    n = _num(v)
    return int(n) if n is not None else None


def _bool(v):
    if v is None or v == "":
        return False
    return str(v).strip().lower() in ("1", "true", "sim", "s", "y", "yes")


def _texto(v):
    return str(v).strip() if v not in (None, "") else None


def _eh_referencia(ws, row_idx):
    """Linha de referência dos templates: fonte itálica/cinza na 1ª célula."""
    c = ws.cell(row=row_idx, column=1)
    f = c.font
    if f.italic:
        return True
    cor = getattr(f.color, "rgb", None)
    return bool(cor and str(cor).endswith(REF_COLOR))


def _mapear_cabecalho(ws):
    header = [str(c.value).strip() if c.value else "" for c in ws[1]]
    return {nome: i for i, nome in enumerate(header) if nome}


async def _resolver_equipamento(db, cat, equip_por_chave, modelo, tipo_motor_linha, contexto):
    """Acha o Equipamento certo pelo modelo — desambiguando por tipo_motor
    quando o modelo tem mais de uma variante (AC/EC) cadastrada."""
    candidatos = [
        eq for (m, tm), eq in equip_por_chave.items() if m == modelo
    ]
    if not candidatos:
        result = await db.execute(
            select(Equipamento).where(Equipamento.modelo == modelo, Equipamento.categoria_id == cat.id)
        )
        candidatos = result.scalars().all()
        for eq in candidatos:
            equip_por_chave[(eq.modelo, eq.tipo_motor)] = eq

    if not candidatos:
        print(f"PULADA ({contexto}, modelo '{modelo}' não encontrado)")
        return None
    if len(candidatos) == 1:
        return candidatos[0]
    if tipo_motor_linha:
        eq = next((e for e in candidatos if e.tipo_motor == tipo_motor_linha), None)
        if eq:
            return eq
        print(f"PULADA ({contexto}, modelo '{modelo}' não tem variante tipo_motor='{tipo_motor_linha}')")
        return None
    print(f"PULADA ({contexto}, modelo '{modelo}' é ambíguo — {len(candidatos)} variantes de tipo_motor, informe qual)")
    return None


async def importar(caminho: str, categoria_nome: str):
    wb = load_workbook(caminho)  # sem data_only para preservar formatação
    ws_eq = wb["Equipamentos"]
    ws_pf = wb["Performance"]
    ws_ve = wb["Variantes Eletricas"] if "Variantes Eletricas" in wb.sheetnames else None
    ws_rd = wb["Resistencia Degelo"] if "Resistencia Degelo" in wb.sheetnames else None
    ws_fc = wb["Fatores Correcao"] if "Fatores Correcao" in wb.sheetnames else None

    async with SessionLocal() as db:
        cat = (await db.execute(
            select(Categoria).where(Categoria.nome == categoria_nome)
        )).scalar_one_or_none()
        if not cat:
            print(f"ERRO: categoria '{categoria_nome}' não existe no banco.")
            return

        um = (await db.execute(
            select(UnidadeMedida).where(UnidadeMedida.sigla == "un")
        )).scalars().first()
        if not um:
            um = (await db.execute(select(UnidadeMedida))).scalars().first()
        if not um:
            um = UnidadeMedida(nome="Unidade", sigla="un")
            db.add(um)
            await db.flush()

        fab_por_nome = {
            f.nome.strip().lower(): f
            for f in (await db.execute(select(Fabricante))).scalars().all()
        }

        async def obter_fabricante(nome):
            chave = str(nome or "").strip().lower()
            if not chave:
                return None
            fab = fab_por_nome.get(chave)
            if not fab:
                fab = Fabricante(nome=str(nome).strip())
                db.add(fab)
                await db.flush()
                fab_por_nome[chave] = fab
            return fab

        # ── Aba Equipamentos ──────────────────────────────────────────────
        idx_eq = _mapear_cabecalho(ws_eq)

        def cel_eq(row, nome):
            return row[idx_eq[nome]] if nome in idx_eq else None

        eq_ins = eq_upd = eq_ref = 0
        equip_por_chave: dict[tuple[str, str | None], Equipamento] = {}
        for i, row in enumerate(ws_eq.iter_rows(min_row=2, values_only=True), start=2):
            modelo = cel_eq(row, "modelo")
            fab_nome = cel_eq(row, "fabricante")
            if not modelo:
                continue
            if _eh_referencia(ws_eq, i):
                eq_ref += 1
                continue
            modelo = str(modelo).strip()
            fab = await obter_fabricante(fab_nome)
            if not fab:
                print(f"PULADA (sem fabricante): {modelo}")
                continue
            tipo_motor = _texto(cel_eq(row, "tipo_motor"))

            existente = (await db.execute(
                select(Equipamento).where(
                    Equipamento.modelo == modelo,
                    Equipamento.fabricante_id == fab.id,
                    Equipamento.categoria_id == cat.id,
                    Equipamento.tipo_motor == tipo_motor,
                )
            )).scalar_one_or_none()
            campos = dict(
                qtde_ventiladores=_int(cel_eq(row, "qtde_ventiladores")) or 0,
                diametro_ventilador_mm=_int(cel_eq(row, "diametro_ventilador_mm")) or 0,
                vazao_ar_m3h=_int(cel_eq(row, "vazao_ar_m3h")) or 0,
                flecha_ar_m=_int(cel_eq(row, "flecha_ar_m")) or 0,
                volume_interno_kg=_num(cel_eq(row, "volume_interno_kg")),
                conexao_liquido=_texto(cel_eq(row, "conexao_liquido")),
                conexao_succao=_texto(cel_eq(row, "conexao_succao")),
                custo=_num(cel_eq(row, "custo")) or Decimal("0"),
                comprimento_mm=_int(cel_eq(row, "comprimento_mm")),
                altura_mm=_int(cel_eq(row, "altura_mm")),
                profundidade_mm=_int(cel_eq(row, "profundidade_mm")),
                peso_liquido_kg=_num(cel_eq(row, "peso_liquido_kg")),
                ruido_dba=_int(cel_eq(row, "ruido_dba")),
                carga_refrigerante_kg=_num(cel_eq(row, "carga_refrigerante_kg")),
                volume_deslocado_m3h=_num(cel_eq(row, "volume_deslocado_m3h")),
                potencia_nominal_hp=_num(cel_eq(row, "potencia_nominal_hp")),
                motor_ventilador_corrente_a=_num(cel_eq(row, "motor_ventilador_corrente_a")),
                motor_ventilador_potencia_w=_num(cel_eq(row, "motor_ventilador_potencia_w")),
                capacitor_marcha_especificacao=_texto(cel_eq(row, "capacitor_marcha_especificacao")),
                resistencia_carter_especificacao=_texto(cel_eq(row, "resistencia_carter_especificacao")),
                tanque_liquido_l=_num(cel_eq(row, "tanque_liquido_l")),
            )
            if existente:
                for k, v in campos.items():
                    setattr(existente, k, v)
                equip_por_chave[(modelo, tipo_motor)] = existente
                eq_upd += 1
            else:
                novo = Equipamento(
                    modelo=modelo, fabricante_id=fab.id, categoria_id=cat.id,
                    unidade_medida_id=um.id, tipo_motor=tipo_motor, **campos,
                )
                db.add(novo)
                await db.flush()
                equip_por_chave[(modelo, tipo_motor)] = novo
                eq_ins += 1

        # ── Aba Performance ───────────────────────────────────────────────
        idx_pf = _mapear_cabecalho(ws_pf)

        def cel_pf(row, nome):
            return row[idx_pf[nome]] if nome in idx_pf else None

        pf_ins = pf_upd = pf_ref = pf_pul = 0
        for i, row in enumerate(ws_pf.iter_rows(min_row=2, values_only=True), start=2):
            modelo = cel_pf(row, "modelo")
            if not modelo:
                continue
            if _eh_referencia(ws_pf, i):
                pf_ref += 1
                continue
            modelo = str(modelo).strip()
            fluido = _texto(cel_pf(row, "fluido"))
            t_amb = _int(cel_pf(row, "T_ambiente_C"))
            t_evap = _int(cel_pf(row, "temp_evaporacao_C"))
            delta_t = _num(cel_pf(row, "delta_t")) or Decimal("0")
            capacidade = _int(cel_pf(row, "capacidade_kcalh"))
            consumo = _num(cel_pf(row, "consumo_kw"))
            usa_fator = _bool(cel_pf(row, "usa_fator_correcao"))
            if not (fluido and t_amb is not None and t_evap is not None and capacidade):
                print(f"PULADA (dados incompletos) linha {i}: {row}")
                pf_pul += 1
                continue

            eq = await _resolver_equipamento(
                db, cat, equip_por_chave, modelo, _texto(cel_pf(row, "tipo_motor")), f"performance linha {i}"
            )
            if not eq:
                pf_pul += 1
                continue

            existente = (await db.execute(
                select(PerformanceEquipamento).where(
                    PerformanceEquipamento.equipamento_id == eq.id,
                    PerformanceEquipamento.fluido == fluido,
                    PerformanceEquipamento.temp_ambiente == t_amb,
                    PerformanceEquipamento.temp_evaporacao == t_evap,
                    PerformanceEquipamento.delta_t == delta_t,
                )
            )).scalar_one_or_none()
            if existente:
                existente.capacidade = capacidade
                existente.consumo_kw = consumo
                existente.usa_fator_correcao = usa_fator
                pf_upd += 1
            else:
                db.add(PerformanceEquipamento(
                    equipamento_id=eq.id, fluido=fluido, temp_ambiente=t_amb,
                    temp_evaporacao=t_evap, delta_t=delta_t,
                    capacidade=capacidade, consumo_kw=consumo, usa_fator_correcao=usa_fator,
                ))
                pf_ins += 1

        # ── Aba Variantes Eletricas (opcional) ──────────────────────────────
        ve_ins = ve_upd = ve_pul = 0
        if ws_ve is not None:
            idx_ve = _mapear_cabecalho(ws_ve)

            def cel_ve(row, nome):
                return row[idx_ve[nome]] if nome in idx_ve else None

            for i, row in enumerate(ws_ve.iter_rows(min_row=2, values_only=True), start=2):
                modelo = cel_ve(row, "modelo")
                if not modelo or _eh_referencia(ws_ve, i):
                    continue
                modelo = str(modelo).strip()
                tensao = _texto(cel_ve(row, "tensao"))
                fase = _int(cel_ve(row, "fase"))
                # frequencia_hz fica None de propósito pra motor EC — não é
                # obrigatório como tensao/fase (achado testando localmente).
                freq = _int(cel_ve(row, "frequencia_hz"))
                if not (tensao and fase):
                    print(f"PULADA (Variantes Eletricas, dados incompletos) linha {i}: {row}")
                    ve_pul += 1
                    continue
                eq = await _resolver_equipamento(
                    db, cat, equip_por_chave, modelo, _texto(cel_ve(row, "tipo_motor")), f"variante elétrica linha {i}"
                )
                if not eq:
                    ve_pul += 1
                    continue
                campos = dict(
                    vazao_ar_m3h=_int(cel_ve(row, "vazao_ar_m3h")),
                    potencia_w=_num(cel_ve(row, "potencia_w")),
                    corrente_a=_num(cel_ve(row, "corrente_a")),
                    codigo_fabricante=_texto(cel_ve(row, "codigo_fabricante")),
                    corrente_partida_a=_num(cel_ve(row, "corrente_partida_a")),
                )
                existente = (await db.execute(
                    select(EquipamentoVarianteEletrica).where(
                        EquipamentoVarianteEletrica.equipamento_id == eq.id,
                        EquipamentoVarianteEletrica.tensao == tensao,
                        EquipamentoVarianteEletrica.fase == fase,
                        EquipamentoVarianteEletrica.frequencia_hz == freq,
                    )
                )).scalar_one_or_none()
                if existente:
                    for k, v in campos.items():
                        setattr(existente, k, v)
                    ve_upd += 1
                else:
                    db.add(EquipamentoVarianteEletrica(
                        equipamento_id=eq.id, tensao=tensao, fase=fase, frequencia_hz=freq, **campos,
                    ))
                    ve_ins += 1

        # ── Aba Resistencia Degelo (opcional) — aplica a AC e EC do modelo ──
        rd_ins = rd_upd = rd_pul = 0
        if ws_rd is not None:
            idx_rd = _mapear_cabecalho(ws_rd)

            def cel_rd(row, nome):
                return row[idx_rd[nome]] if nome in idx_rd else None

            for i, row in enumerate(ws_rd.iter_rows(min_row=2, values_only=True), start=2):
                modelo = cel_rd(row, "modelo")
                if not modelo or _eh_referencia(ws_rd, i):
                    continue
                modelo = str(modelo).strip()
                tensao = _texto(cel_rd(row, "tensao"))
                potencia = _num(cel_rd(row, "potencia_individual_w"))
                corrente = _num(cel_rd(row, "corrente_a"))
                if not (tensao and potencia and corrente):
                    print(f"PULADA (Resistencia Degelo, dados incompletos) linha {i}: {row}")
                    rd_pul += 1
                    continue
                equipamentos = [eq for (m, _tm), eq in equip_por_chave.items() if m == modelo]
                if not equipamentos:
                    result = await db.execute(
                        select(Equipamento).where(Equipamento.modelo == modelo, Equipamento.categoria_id == cat.id)
                    )
                    equipamentos = result.scalars().all()
                if not equipamentos:
                    print(f"PULADA (Resistencia Degelo, modelo '{modelo}' não encontrado) linha {i}")
                    rd_pul += 1
                    continue
                nao_equilibrado = _bool(cel_rd(row, "consumo_nao_equilibrado"))
                for eq in equipamentos:
                    existente = (await db.execute(
                        select(EquipamentoResistenciaDegelo).where(
                            EquipamentoResistenciaDegelo.equipamento_id == eq.id,
                            EquipamentoResistenciaDegelo.tensao == tensao,
                        )
                    )).scalar_one_or_none()
                    if existente:
                        existente.potencia_individual_w = potencia
                        existente.corrente_a = corrente
                        existente.consumo_nao_equilibrado = nao_equilibrado
                        rd_upd += 1
                    else:
                        db.add(EquipamentoResistenciaDegelo(
                            equipamento_id=eq.id, tensao=tensao,
                            potencia_individual_w=potencia, corrente_a=corrente,
                            consumo_nao_equilibrado=nao_equilibrado,
                        ))
                        rd_ins += 1

        # ── Aba Fatores Correcao (opcional, por fabricante) ─────────────────
        fc_ins = fc_upd = 0
        if ws_fc is not None:
            idx_fc = _mapear_cabecalho(ws_fc)

            def cel_fc(row, nome):
                return row[idx_fc[nome]] if nome in idx_fc else None

            for i, row in enumerate(ws_fc.iter_rows(min_row=2, values_only=True), start=2):
                fab_nome = cel_fc(row, "fabricante")
                if not fab_nome:
                    continue
                fluido_base = _texto(cel_fc(row, "fluido_base"))
                fluido = _texto(cel_fc(row, "fluido"))
                fator = _num(cel_fc(row, "fator"))
                if not (fluido_base and fluido and fator is not None):
                    print(f"PULADA (Fatores Correcao, dados incompletos) linha {i}: {row}")
                    continue
                fab = await obter_fabricante(fab_nome)
                existente = (await db.execute(
                    select(FatorCorrecaoFluido).where(
                        FatorCorrecaoFluido.fabricante_id == fab.id,
                        FatorCorrecaoFluido.fluido_base == fluido_base,
                        FatorCorrecaoFluido.fluido == fluido,
                    )
                )).scalar_one_or_none()
                if existente:
                    existente.fator = fator
                    fc_upd += 1
                else:
                    db.add(FatorCorrecaoFluido(
                        fabricante_id=fab.id, fluido_base=fluido_base, fluido=fluido, fator=fator,
                    ))
                    fc_ins += 1

        await db.commit()

    print(f"EQUIPAMENTOS          — inseridos: {eq_ins} | atualizados: {eq_upd} | referência (puladas): {eq_ref}")
    print(f"PERFORMANCE           — inseridas: {pf_ins} | atualizadas: {pf_upd} | referência: {pf_ref} | puladas: {pf_pul}")
    if ws_ve is not None:
        print(f"VARIANTES ELÉTRICAS   — inseridas: {ve_ins} | atualizadas: {ve_upd} | puladas: {ve_pul}")
    if ws_rd is not None:
        print(f"RESISTÊNCIA DEGELO    — inseridas: {rd_ins} | atualizadas: {rd_upd} | puladas: {rd_pul}")
    if ws_fc is not None:
        print(f"FATORES DE CORREÇÃO   — inseridos: {fc_ins} | atualizados: {fc_upd}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Uso: python scripts/importar_equipamentos.py <planilha.xlsx> "Unidade Condensadora"|"Evaporadora"')
        sys.exit(1)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(importar(sys.argv[1], sys.argv[2]))
