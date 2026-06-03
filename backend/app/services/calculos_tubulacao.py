from __future__ import annotations
import math
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, ItemTubulacao
from app.models.isolamento import IsolamentoTubulacao

# ═══════════════════════════════════════════════════════════════════════════
# TABELAS ASHRAE — Capacidade máxima da LINHA DE SUCÇÃO em kcal/h
# Referência: ASHRAE Refrigeration Handbook, Chapter 1 — Halocarbon Systems
# Critério: queda de pressão equivalente a 1°C por 100m de comprimento equivalente
# Base: 30m de comprimento equivalente (aplicar fator_distancia para outros comprimentos)
# ═══════════════════════════════════════════════════════════════════════════

# Ordenação das bitolas (crescente por capacidade — não alterar a ordem)
_BITOLAS_SUCCAO = [
    '3/8"', '1/2"', '5/8"', '3/4"', '7/8"',
    '1.1/8"', '1.3/8"', '1.5/8"', '2.1/8"',
]

# Temperaturas de evaporação disponíveis nas tabelas (°C)
_T_EVAP_PONTOS = [-40, -20, -10, 0, 5]

# cap[fluido][T.Evap][bitola] = kcal/h máx para 30m equivalente
_SUCCAO_CAP: dict[str, dict[int, dict[str, int]]] = {
    "R22": {
        -40: {'3/8"': 350,   '1/2"': 700,   '5/8"': 1300,  '3/4"': 2200,
              '7/8"': 3300,  '1.1/8"': 6500, '1.3/8"': 10500,'1.5/8"': 16000, '2.1/8"': 32000},
        -20: {'3/8"': 900,   '1/2"': 1700,  '5/8"': 3200,  '3/4"': 5400,
              '7/8"': 8200,  '1.1/8"': 16000,'1.3/8"': 26000,'1.5/8"': 39500, '2.1/8"': 79500},
        -10: {'3/8"': 1400,  '1/2"': 2700,  '5/8"': 5100,  '3/4"': 8600,
              '7/8"': 13000, '1.1/8"': 25500,'1.3/8"': 41500,'1.5/8"': 63000, '2.1/8"': 127000},
          0: {'3/8"': 2100,  '1/2"': 4100,  '5/8"': 7700,  '3/4"': 13000,
              '7/8"': 19500, '1.1/8"': 38500,'1.3/8"': 62500,'1.5/8"': 95000, '2.1/8"': 191000},
          5: {'3/8"': 2800,  '1/2"': 5500,  '5/8"': 10400, '3/4"': 17500,
              '7/8"': 26500, '1.1/8"': 52000,'1.3/8"': 84500,'1.5/8"': 128000,'2.1/8"': 258000},
    },
    "R404A": {
        -40: {'3/8"': 420,   '1/2"': 800,   '5/8"': 1500,  '3/4"': 2600,
              '7/8"': 3900,  '1.1/8"': 7700, '1.3/8"': 12500,'1.5/8"': 19000, '2.1/8"': 38000},
        -20: {'3/8"': 1000,  '1/2"': 1950,  '5/8"': 3700,  '3/4"': 6300,
              '7/8"': 9500,  '1.1/8"': 18800,'1.3/8"': 30500,'1.5/8"': 46200, '2.1/8"': 93000},
        -10: {'3/8"': 1550,  '1/2"': 3000,  '5/8"': 5700,  '3/4"': 9700,
              '7/8"': 14600, '1.1/8"': 28900,'1.3/8"': 47000,'1.5/8"': 71200, '2.1/8"': 143000},
          0: {'3/8"': 2300,  '1/2"': 4450,  '5/8"': 8400,  '3/4"': 14300,
              '7/8"': 21600, '1.1/8"': 42700,'1.3/8"': 69500,'1.5/8"': 105000,'2.1/8"': 212000},
          5: {'3/8"': 3100,  '1/2"': 6000,  '5/8"': 11400, '3/4"': 19400,
              '7/8"': 29300, '1.1/8"': 57900,'1.3/8"': 94000,'1.5/8"': 143000,'2.1/8"': 287000},
    },
}

# ── Linha de Líquido (capacidade pouco dependente de temperatura) ──────────
_BITOLAS_LIQUIDO = ['1/4"', '3/8"', '1/2"', '5/8"', '7/8"', '1.1/8"', '1.3/8"', '1.5/8"', '2.1/8"']

_LIQUIDO_CAP: dict[str, dict[str, int]] = {
    "R22":   {'1/4"': 2500,  '3/8"': 7500,  '1/2"': 15000, '5/8"': 26000,
              '7/8"': 55000, '1.1/8"': 100000,'1.3/8"': 160000,'1.5/8"': 240000,'2.1/8"': 420000},
    "R404A": {'1/4"': 2800,  '3/8"': 8000,  '1/2"': 16000, '5/8"': 28000,
              '7/8"': 60000, '1.1/8"': 110000,'1.3/8"': 175000,'1.5/8"': 265000,'2.1/8"': 460000},
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


# ── Tabela de conexões por faixa de distância (Opção 2) ───────────────────
# Valores baseados em prática de mercado (ASHRAE / NBR)
def _curvas_auto(distancia: float) -> int:
    """Estimativa automática de curvas 90° pela distância total."""
    if distancia <= 10:  return 2
    if distancia <= 20:  return 4
    if distancia <= 40:  return 6
    if distancia <= 60:  return 8
    return 10


def _calcular_conexoes(
    diam_succao:  str,
    diam_liquido: str,
    distancia:    float,
    num_curvas_90: int | None,
    incluir_sifao: bool,
) -> tuple[list[ItemTubulacao], int, str]:
    """
    Retorna (lista_conexoes, curvas_usadas, origem).

    Regras:
    - Curvas 90°, 45°, uniões e reduções são iguais nas duas linhas
    - Sifão e contra-sifão: somente na sucção (saída do evaporador)
    - Curvas 45° ≈ metade das 90°
    - Uniões = mesmo número das 90°
    - Reduções: 1 para distâncias curtas, 2 para longas
    """
    if num_curvas_90 is not None:
        curvas_90 = num_curvas_90
        origem    = "informado pelo técnico"
    else:
        curvas_90 = _curvas_auto(distancia)
        origem    = "automático (tabela por distância)"

    curvas_45 = max(0, curvas_90 // 2)
    unioes    = curvas_90
    reducoes  = 1 if distancia <= 30 else 2

    conexoes: list[ItemTubulacao] = []

    def add(item, qtd, detalhe):
        if qtd > 0:
            conexoes.append(ItemTubulacao(item=item, quantidade=qtd,
                                          unidade="un", detalhe=detalhe))

    # ── Curvas 90° ────────────────────────────────────────────────────────
    add(f'Curva 90° {diam_succao} (Sucção)',   curvas_90,
        f'Mudança de direção | {origem}')
    add(f'Curva 90° {diam_liquido} (Líquido)', curvas_90,
        f'Mudança de direção | {origem}')

    # ── Curvas 45° ────────────────────────────────────────────────────────
    add(f'Curva 45° {diam_succao} (Sucção)',   curvas_45,
        f'Desvio suave | {origem}')
    add(f'Curva 45° {diam_liquido} (Líquido)', curvas_45,
        f'Desvio suave | {origem}')

    # ── Uniões / Luvas ────────────────────────────────────────────────────
    add(f'União/Luva {diam_succao} (Sucção)',   unioes,
        'Emenda de tubos | linha de sucção')
    add(f'União/Luva {diam_liquido} (Líquido)', unioes,
        'Emenda de tubos | linha de líquido')

    # ── Reduções (transição entre bitolas) ────────────────────────────────
    if diam_succao != diam_liquido:
        add(f'Redução {diam_succao} × {diam_liquido}', reducoes,
            'Transição sucção → líquido')

    # ── Sifão e contra-sifão (sucção — saída do evaporador) ───────────────
    if incluir_sifao:
        add(f'Sifão {diam_succao} (Sucção)', 1,
            'Saída do evaporador — evita retorno de óleo ao compressor')
        add(f'Contra-sifão {diam_succao} (Sucção)', 1,
            'Saída do evaporador — previne bolsas de líquido na linha')

    return conexoes, curvas_90, origem


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
    qtd_tubo  = math.ceil(req.distancia * 1.1)   # +10% para conexões e curvas
    match     = re.search(r"(\d+)", diam_succao)
    valor_diam= int(match.group()) if match else 1
    qtd_solda = math.ceil((qtd_tubo / 5) * (valor_diam / 2))

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

    materiais: list[ItemTubulacao] = [
        ItemTubulacao(
            item=f'Tubo Cobre {diam_liquido} (Líquido)',
            quantidade=qtd_tubo, unidade="m",
            detalhe="Linha de alta pressão — ASHRAE",
        ),
        ItemTubulacao(
            item=f'Tubo Cobre {diam_succao} (Sucção)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=nota_succao,
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

    # ── Conexões (curvas, uniões, reduções, sifão) ────────────────────────
    conexoes, curvas_usadas, origem_curvas = _calcular_conexoes(
        diam_succao   = diam_succao,
        diam_liquido  = diam_liquido,
        distancia     = req.distancia,
        num_curvas_90 = req.num_curvas_90,
        incluir_sifao = req.incluir_sifao,
    )
    materiais.extend(conexoes)

    # ── Solda: emendas de tubo + uma por conexão ──────────────────────────
    qtd_solda_total = qtd_solda + len(conexoes)
    materiais.append(ItemTubulacao(
        item="Solda Prata 15% / Foscoper",
        quantidade=qtd_solda_total, unidade="vareta",
        detalhe=f"{qtd_solda} emendas de tubo + {len(conexoes)} conexões ({diam_succao})",
    ))

    return TubulacaoResponse(
        diametro_liquido=diam_liquido,
        diametro_succao=diam_succao,
        distancia_considerada=req.distancia,
        temp_evap_calculada=req.temp_evap,
        padrao_isolamento_usado=padrao,
        sugestao_padrao=just_sugerido,
        curvas_90_usadas=curvas_usadas,
        origem_curvas=origem_curvas,
        lista_materiais=materiais,
    )
