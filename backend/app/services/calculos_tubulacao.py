from __future__ import annotations
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, ItemTubulacao
from app.models.isolamento import IsolamentoTubulacao
from app.models.peso_tubo_cobre import PesoTuboCobre

# ═══════════════════════════════════════════════════════════════════════════
# TABELAS ASHRAE — Capacidade máxima da LINHA DE SUCÇÃO em kcal/h
# Referência: ASHRAE Refrigeration Handbook 2014, Cap. 1 — Halocarbon Systems
# Critério: queda de pressão equivalente a 1°C por 30m de comprimento equivalente
# (ΔP ≈ 1 K / 30 m — padrão de mercado brasileiro / NBR)
#
# REVISÃO v2: valores corrigidos em relação à versão anterior.
# A tabela anterior estava com capacidades ~2,5× acima dos valores ASHRAE reais,
# causando seleção de bitolas subdimensionadas (principalmente na sucção).
# Os valores abaixo foram calibrados com fator 0,40 sobre a base original,
# alinhando com dados de fabricantes (Danfoss, Embraco) e prática de engenharia.
# ═══════════════════════════════════════════════════════════════════════════

# Ordenação das bitolas (crescente por capacidade — não alterar a ordem)
_BITOLAS_SUCCAO = [
    '3/8"', '1/2"', '5/8"', '3/4"', '7/8"',
    '1.1/8"', '1.3/8"', '1.5/8"', '2.1/8"',
]

# Temperaturas de evaporação disponíveis nas tabelas (°C)
_T_EVAP_PONTOS = [-40, -20, -10, 0, 5]

# cap[fluido][T.Evap][bitola] = kcal/h máx para 30m equivalente (critério 1°C/30m)
_SUCCAO_CAP: dict[str, dict[int, dict[str, int]]] = {
    "R22": {
        -40: {'3/8"':  140,  '1/2"':  280,  '5/8"':  520,  '3/4"':  880,
              '7/8"': 1320,  '1.1/8"': 2600, '1.3/8"': 4200, '1.5/8"':  6400, '2.1/8"': 12800},
        -20: {'3/8"':  360,  '1/2"':  680,  '5/8"': 1280,  '3/4"': 2160,
              '7/8"': 3280,  '1.1/8"': 6400, '1.3/8"':10400, '1.5/8"': 15800, '2.1/8"': 31800},
        -10: {'3/8"':  560,  '1/2"': 1080,  '5/8"': 2040,  '3/4"': 3440,
              '7/8"': 5200,  '1.1/8"':10200, '1.3/8"':16600, '1.5/8"': 25200, '2.1/8"': 50800},
          0: {'3/8"':  840,  '1/2"': 1640,  '5/8"': 3080,  '3/4"': 5200,
              '7/8"': 7800,  '1.1/8"':15400, '1.3/8"':25000, '1.5/8"': 38000, '2.1/8"': 76400},
          5: {'3/8"': 1120,  '1/2"': 2200,  '5/8"': 4160,  '3/4"': 7000,
              '7/8"':10600,  '1.1/8"':20800, '1.3/8"':33800, '1.5/8"': 51200, '2.1/8"':103200},
    },
    "R404A": {
        -40: {'3/8"':  170,  '1/2"':  320,  '5/8"':  600,  '3/4"': 1040,
              '7/8"': 1560,  '1.1/8"': 3080, '1.3/8"': 5000, '1.5/8"':  7600, '2.1/8"': 15200},
        -20: {'3/8"':  400,  '1/2"':  780,  '5/8"': 1480,  '3/4"': 2520,
              '7/8"': 3800,  '1.1/8"': 7520, '1.3/8"':12200, '1.5/8"': 18480, '2.1/8"': 37200},
        -10: {'3/8"':  620,  '1/2"': 1200,  '5/8"': 2280,  '3/4"': 3880,
              '7/8"': 5840,  '1.1/8"':11560, '1.3/8"':18800, '1.5/8"': 28480, '2.1/8"': 57200},
          0: {'3/8"':  920,  '1/2"': 1780,  '5/8"': 3360,  '3/4"': 5720,
              '7/8"': 8640,  '1.1/8"':17080, '1.3/8"':27800, '1.5/8"': 42000, '2.1/8"': 84800},
          5: {'3/8"': 1240,  '1/2"': 2400,  '5/8"': 4560,  '3/4"': 7760,
              '7/8"':11720,  '1.1/8"':23160, '1.3/8"':37600, '1.5/8"': 57200, '2.1/8"':114800},
    },
}

# ── Linha de Líquido (capacidade pouco dependente de temperatura) ──────────
# REVISÃO v2: fator de correção 0,56 aplicado sobre valores originais.
# Calibração com 4 casos reais (jun/2026):
#   3/8" real: entre 3.841 e 5.128 kcal/h → estimativa 4.500 kcal/h (fator 4500/8000 = 0,56)
#   Sucção: corrigida na v1 (fator 0,40) — confirmada em 4 casos
_BITOLAS_LIQUIDO = ['1/4"', '3/8"', '1/2"', '5/8"', '7/8"', '1.1/8"', '1.3/8"', '1.5/8"', '2.1/8"']

_LIQUIDO_CAP: dict[str, dict[str, int]] = {
    "R22":   {'1/4"': 1400,  '3/8"': 4200,  '1/2"':  8400, '5/8"': 14560,
              '7/8"': 30800, '1.1/8"': 56000,'1.3/8"': 89600,'1.5/8"':134400,'2.1/8"':235200},
    "R404A": {'1/4"': 1570,  '3/8"': 4480,  '1/2"':  8960, '5/8"': 15680,
              '7/8"': 33600, '1.1/8"': 61600,'1.3/8"': 98000,'1.5/8"':148400,'2.1/8"':257600},
}
# Fluidos sem tabela própria → usa R22 como fallback conservador
_FLUIDO_FALLBACK = "R22"

# ── Conversão bitola imperial → diâmetro externo Cu em mm ─────────────────
_BITOLA_PARA_MM: dict[str, float] = {
    '1/4"':   6.0,  '3/8"':  10.0, '1/2"':  12.0, '5/8"':  15.0,
    '3/4"':  18.0,  '7/8"':  22.0, '1.1/8"': 28.0, '1.3/8"': 35.0,
    '1.5/8"': 42.0, '2.1/8"': 54.0,'2.5/8"': 64.0, '3.1/8"': 76.2,
}

# ── Sugestão de padrão de isolamento por T.Evap ───────────────────────────
_SUGESTAO_PADRAO = [
    ( 0,   float('inf'),  "D", "Resfriados leves — risco baixo de condensação"),
    (-5,   0,             "F", "Resfriados normais — proteção padrão"),
    (-15,  -5,            "H", "Resfriados pesados — maior proteção térmica"),
    (-25,  -15,           "M", "Congelados — isolamento reforçado obrigatório"),
    (-35,  -25,           "R", "Congelados pesados — alta resistência térmica"),
    (float('-inf'), -35,  "T", "Ultra-congelados — máxima espessura"),
]

_INFO_PADRAO = {
    "D": ("6–7,5 mm",   "Resfriados leves ≥ 0°C"),
    "F": ("9–12 mm",    "Resfriados normais -5°C a 0°C"),
    "H": ("13–16 mm",   "Resfriados pesados -15°C a -5°C"),
    "M": ("19–26 mm",   "Congelados -25°C a -15°C"),
    "R": ("25–32,5 mm", "Congelados pesados -35°C a -25°C"),
    "T": ("32–45 mm",   "Ultra-congelados < -35°C"),
}


def sugerir_padrao(temp_evap: float) -> tuple[str, str]:
    for t_min, t_max, padrao, just in _SUGESTAO_PADRAO:
        if t_min <= temp_evap < t_max:
            faixa, _ = _INFO_PADRAO[padrao]
            return padrao, f"Padrão {padrao} ({faixa}) — {just}"
    return "H", "Padrão H por segurança"


def _interpolar_cap(fluido: str, tabela_raw: dict, t_evap: float, bitola: str) -> float:
    """
    Interpola linearmente a capacidade máxima para uma bitola e T.Evap exatos.
    Se T.Evap estiver fora da faixa, usa o valor do extremo mais próximo.
    """
    pontos = sorted(tabela_raw.keys())  # temperaturas disponíveis

    if t_evap <= pontos[0]:
        return float(tabela_raw[pontos[0]].get(bitola, 0))
    if t_evap >= pontos[-1]:
        return float(tabela_raw[pontos[-1]].get(bitola, 0))

    # Encontrar os dois pontos que cercam t_evap
    t_abaixo = max(t for t in pontos if t <= t_evap)
    t_acima  = min(t for t in pontos if t >= t_evap)

    if t_abaixo == t_acima:
        return float(tabela_raw[t_abaixo].get(bitola, 0))

    cap_ab = float(tabela_raw[t_abaixo].get(bitola, 0))
    cap_ac = float(tabela_raw[t_acima].get(bitola, 0))

    # Interpolação linear
    frac = (t_evap - t_abaixo) / (t_acima - t_abaixo)
    return cap_ab + frac * (cap_ac - cap_ab)


def _selecionar_succao(fluido: str, capacidade: float, t_evap: float, fator: float) -> str:
    """
    Seleciona a menor bitola de sucção ASHRAE que atende à capacidade,
    interpolando entre os pontos de T.Evap disponíveis.
    """
    tabela = _SUCCAO_CAP.get(fluido, _SUCCAO_CAP[_FLUIDO_FALLBACK])

    for bitola in _BITOLAS_SUCCAO:
        cap_interp = _interpolar_cap(fluido, tabela, t_evap, bitola)
        if capacidade <= cap_interp * fator:
            return bitola
    return "Consultar Engenharia"


def _selecionar_liquido(fluido: str, capacidade: float, fator: float) -> str:
    """Seleciona a menor bitola de líquido ASHRAE para a capacidade dada."""
    tabela = _LIQUIDO_CAP.get(fluido, _LIQUIDO_CAP[_FLUIDO_FALLBACK])

    for bitola in _BITOLAS_LIQUIDO:
        cap_max = float(tabela.get(bitola, 0))
        if capacidade <= cap_max * fator:
            return bitola
    return "Consultar Engenharia"




async def _buscar_isolamento(db: AsyncSession, bitola: str, padrao: str) -> tuple[str, float] | None:
    diam_mm = _BITOLA_PARA_MM.get(bitola)
    if diam_mm is None:
        return None
    result = await db.execute(
        select(IsolamentoTubulacao).where(
            IsolamentoTubulacao.diametro_cu_mm == diam_mm,
            IsolamentoTubulacao.padrao         == padrao.upper(),
        )
    )
    iso = result.scalar_one_or_none()
    if iso:
        return str(iso.referencia), float(iso.espessura_mm)
    return None


async def calcular_tubulacao(req: TubulacaoRequest, db: AsyncSession) -> TubulacaoResponse:

    if req.capacidade_real <= 100:
        raise ValueError("Capacidade muito baixa (mínimo 100 kcal/h).")

    fluido = req.fluido.upper()
    fluido_tabela = fluido if fluido in _SUCCAO_CAP else _FLUIDO_FALLBACK
    nota_fluido = "" if fluido in _SUCCAO_CAP else f" (tabela {_FLUIDO_FALLBACK} usada como referência)"

    # ── Fator de distância: compensa queda de pressão em linhas longas ──────
    # Base das tabelas: 30m equivalente
    # Referência ASHRAE: queda equivalente a 1°C / 100m
    fator_distancia = 1.0
    if req.distancia > 30:  fator_distancia = 0.90
    if req.distancia > 50:  fator_distancia = 0.80
    if req.distancia > 80:  fator_distancia = 0.70
    if req.distancia > 120: fator_distancia = 0.60

    # ── Fator de alta eficiência ─────────────────────────────────────────────
    # Alta eficiência: linha de sucção com menor queda de pressão
    # → pipe deve suportar 133% da carga real (sobe uma bitola tipicamente)
    # Fator corrigido: 0.75 (antes era 0.5 — muito conservador)
    fator_efic_succao  = 0.75 if req.alta_eficiencia else 1.0
    fator_efic_liquido = 1.0   # líquido: velocidade é o critério, não eficiência

    fator_succao  = fator_distancia * fator_efic_succao
    fator_liquido = fator_efic_liquido

    # ── Seleção dos diâmetros ─────────────────────────────────────────────────
    diam_succao  = _selecionar_succao(fluido_tabela, req.capacidade_real, req.temp_evap, fator_succao)
    diam_liquido = _selecionar_liquido(fluido_tabela, req.capacidade_real, fator_liquido)

    # ── Quantidades ───────────────────────────────────────────────────────────
    # Cada unidade condensadora = 1 circuito independente (sucção + líquido + conexões)
    circuitos  = max(1, req.num_circuitos)
    qtd_tubo_1 = math.ceil(req.distancia * 1.1)   # +10% para conexões e curvas (por circuito)
    qtd_tubo   = qtd_tubo_1 * circuitos

    # ── Notas técnicas ────────────────────────────────────────────────────────
    cap_interp = _interpolar_cap(fluido_tabela, _SUCCAO_CAP.get(fluido_tabela, _SUCCAO_CAP[_FLUIDO_FALLBACK]), req.temp_evap, diam_succao)
    nota_succao = (
        f"Fluido: {fluido}{nota_fluido} | "
        f"T.Evap: {req.temp_evap}°C | "
        f"Cap.interpolada: {cap_interp:.0f} kcal/h | "
        f"{'Alta efic. (fator 0.75)' if req.alta_eficiencia else 'Padrão ASHRAE'}"
    )

    # ── Materiais ─────────────────────────────────────────────────────────────
    padrao_sugerido, just_sugerido = sugerir_padrao(req.temp_evap)
    padrao = req.padrao_isolamento.upper()

    # ── Pesos por metro (tabela Forming Tubing) ───────────────────────────────
    async def _peso_tubo(bitola: str, parede: str) -> tuple[float | None, float | None]:
        row = (await db.execute(
            select(PesoTuboCobre).where(PesoTuboCobre.bitola_pol == bitola)
        )).scalar_one_or_none()
        if row is None:
            return None, None
        kg_m = row.parede_fina if parede == "fina" else row.parede_grossa
        kg_total = round(kg_m * qtd_tubo, 3) if kg_m is not None else None
        return kg_m, kg_total

    peso_liq_m, peso_liq_total = await _peso_tubo(diam_liquido, req.parede_liquido)
    peso_suc_m, peso_suc_total = await _peso_tubo(diam_succao,  req.parede_succao)

    parede_liq_desc = "parede fina 0,79mm (1/32\")" if req.parede_liquido == "fina" else "parede grossa 1,59mm (1/16\")"
    parede_suc_desc = "parede fina 0,79mm (1/32\")" if req.parede_succao  == "fina" else "parede grossa 1,59mm (1/16\")"

    materiais: list[ItemTubulacao] = [
        ItemTubulacao(
            item=f'Tubo Cobre {diam_liquido} (Líquido)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=f"Linha de alta pressão — ASHRAE | {parede_liq_desc}",
            peso_por_metro=peso_liq_m,
            quantidade_kg=peso_liq_total,
        ),
        ItemTubulacao(
            item=f'Tubo Cobre {diam_succao} (Sucção)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=nota_succao + f" | {parede_suc_desc}",
            peso_por_metro=peso_suc_m,
            quantidade_kg=peso_suc_total,
        ),
    ]

    # Isolamento sucção (sempre)
    iso_succao = await _buscar_isolamento(db, diam_succao, padrao)
    if iso_succao:
        ref, esp = iso_succao
        materiais.append(ItemTubulacao(
            item=f'Isolamento Armacel {ref} (Sucção)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=f"Espessura {esp}mm | Padrão {padrao} | {diam_succao}",
        ))
    else:
        materiais.append(ItemTubulacao(
            item=f'Isolamento Armacel padrão {padrao} (Sucção)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=f"Consultar catálogo para bitola {diam_succao}",
        ))

    # Isolamento líquido (opcional)
    if req.isolar_liquido:
        iso_liq = await _buscar_isolamento(db, diam_liquido, padrao)
        if iso_liq:
            ref, esp = iso_liq
            materiais.append(ItemTubulacao(
                item=f'Isolamento Armacel {ref} (Líquido)',
                quantidade=qtd_tubo, unidade="m",
                detalhe=f"Espessura {esp}mm | Padrão {padrao} | {diam_liquido}",
            ))
        else:
            materiais.append(ItemTubulacao(
                item=f'Isolamento Armacel padrão {padrao} (Líquido)',
                quantidade=qtd_tubo, unidade="m",
                detalhe=f"Consultar catálogo para bitola {diam_liquido}",
            ))


    return TubulacaoResponse(
        diametro_liquido=diam_liquido,
        diametro_succao=diam_succao,
        distancia_considerada=req.distancia,
        temp_evap_calculada=req.temp_evap,
        padrao_isolamento_usado=padrao,
        sugestao_padrao=just_sugerido,
        lista_materiais=materiais,
    )