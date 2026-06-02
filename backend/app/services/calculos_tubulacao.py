from __future__ import annotations
import math
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, ItemTubulacao
from app.models.isolamento import IsolamentoTubulacao

# ── Tabelas de capacidade por bitola ──────────────────────────────────────
_TABELA_LIQUIDO: dict[str, int] = {
    '1/4"': 2500,    '3/8"': 8000,    '1/2"': 15000,   '5/8"': 25000,
    '7/8"': 45000,   '1.1/8"': 70000, '1.3/8"': 110000, '1.5/8"': 160000,
    '2.1/8"': 280000,'2.5/8"': 450000,'3.1/8"': 650000, '3.5/8"': 850000,
    '4.1/8"': 1200000,
}

_TABELA_SUCCAO_MEDIA: dict[str, int] = {
    '3/8"': 1200,    '1/2"': 2500,    '5/8"': 4500,    '3/4"': 7000,
    '7/8"': 11000,   '1.1/8"': 18000, '1.3/8"': 28000, '1.5/8"': 38000,
    '2.1/8"': 60000, '2.5/8"': 110000,'3.1/8"': 180000,'3.5/8"': 260000,
    '4.1/8"': 380000,
}

_TABELA_SUCCAO_BAIXA: dict[str, int] = {
    '1/2"': 1500,    '5/8"': 3000,    '3/4"': 4500,    '7/8"': 7500,
    '1.1/8"': 12000, '1.3/8"': 20000, '1.5/8"': 28000, '2.1/8"': 45000,
    '2.5/8"': 85000, '3.1/8"': 130000,'3.5/8"': 190000,'4.1/8"': 280000,
}

# ── Conversão bitola imperial → diâmetro externo Cu em mm ─────────────────
_BITOLA_PARA_MM: dict[str, float] = {
    '1/4"':   6.0,
    '3/8"':  10.0,
    '1/2"':  12.0,
    '5/8"':  15.0,
    '3/4"':  18.0,
    '7/8"':  22.0,
    '1.1/8"': 28.0,
    '1.3/8"': 35.0,
    '1.5/8"': 42.0,
    '2.1/8"': 54.0,
    '2.5/8"': 64.0,
    '3.1/8"': 76.2,
    '3.5/8"': 88.9,
    '4.1/8"': 101.6,
}

# ── Sugestão de padrão por temperatura de evaporação ─────────────────────
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
    """Retorna (padrao, justificativa) baseado na T.Evap."""
    for t_min, t_max, padrao, just in _SUGESTAO_PADRAO:
        if t_min <= temp_evap < t_max:
            faixa, _ = _INFO_PADRAO[padrao]
            return padrao, f"Padrão {padrao} ({faixa}) — {just}"
    return "H", "Padrão H por segurança (T.Evap fora dos limites da tabela)"


def _selecionar_diametro(tabela: dict[str, int], capacidade: float, fator: float) -> str:
    for diam, cap_max in sorted(tabela.items(), key=lambda x: x[1]):
        if capacidade <= cap_max * fator:
            return diam
    return "Consultar Engenharia"


async def _buscar_isolamento(
    db: AsyncSession, bitola: str, padrao: str
) -> tuple[str, float] | None:
    """
    Busca referência e espessura no catálogo Armacel.
    Retorna (referencia, espessura_mm) ou None se não encontrar.
    """
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


async def calcular_tubulacao(
    req: TubulacaoRequest, db: AsyncSession
) -> TubulacaoResponse:

    if req.capacidade_real <= 100:
        raise ValueError("Capacidade muito baixa (mínimo 100 kcal/h).")

    fator_eficiencia = 0.5 if req.alta_eficiencia else 1.0

    fator_distancia = 1.0
    if req.distancia > 20: fator_distancia = 0.9
    if req.distancia > 40: fator_distancia = 0.8
    if req.distancia > 60: fator_distancia = 0.7

    diam_liquido = _selecionar_diametro(_TABELA_LIQUIDO, req.capacidade_real, fator_eficiencia)
    tabela_succao = _TABELA_SUCCAO_BAIXA if req.temp_evap <= -18 else _TABELA_SUCCAO_MEDIA
    diam_succao   = _selecionar_diametro(
        tabela_succao, req.capacidade_real, fator_distancia * fator_eficiencia
    )

    qtd_tubo  = math.ceil(req.distancia * 1.1)
    match     = re.search(r"(\d+)", diam_succao)
    valor_diam= int(match.group()) if match else 1
    qtd_solda = math.ceil((qtd_tubo / 5) * (valor_diam / 2))

    padrao_sugerido, just_sugerido = sugerir_padrao(req.temp_evap)
    padrao = req.padrao_isolamento.upper()

    materiais: list[ItemTubulacao] = [
        ItemTubulacao(
            item=f'Tubo Cobre {diam_liquido} (Líquido)',
            quantidade=qtd_tubo, unidade="m",
            detalhe="Linha de alta pressão",
        ),
        ItemTubulacao(
            item=f'Tubo Cobre {diam_succao} (Sucção)',
            quantidade=qtd_tubo, unidade="m",
            detalhe=f"Sucção dimensionada com ΔT de {req.delta_t_selecionado}K",
        ),
    ]

    # ── Isolamento linha de sucção (sempre) ───────────────────────────────
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

    # ── Isolamento linha de líquido (opcional) ────────────────────────────
    if req.isolar_liquido:
        iso_liquido = await _buscar_isolamento(db, diam_liquido, padrao)
        if iso_liquido:
            ref, esp = iso_liquido
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

    # ── Solda ─────────────────────────────────────────────────────────────
    materiais.append(ItemTubulacao(
        item="Solda Prata 15% / Foscoper",
        quantidade=qtd_solda, unidade="vareta",
        detalhe=f"Calculado para conexões de {diam_succao}",
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
