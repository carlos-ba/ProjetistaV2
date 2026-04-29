from __future__ import annotations
import math
import re
from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, ItemTubulacao

_TABELA_LIQUIDO: dict[str, int] = {
    '1/4"': 2500, '3/8"': 8000, '1/2"': 15000, '5/8"': 25000, '7/8"': 45000,
    '1.1/8"': 70000, '1.3/8"': 110000, '1.5/8"': 160000, '2.1/8"': 280000,
    '2.5/8"': 450000, '3.1/8"': 650000, '3.5/8"': 850000, '4.1/8"': 1200000,
}

_TABELA_SUCCAO_MEDIA: dict[str, int] = {
    '3/8"': 1200, '1/2"': 2500, '5/8"': 4500, '3/4"': 7000, '7/8"': 11000,
    '1.1/8"': 18000, '1.3/8"': 28000, '1.5/8"': 38000, '2.1/8"': 60000,
    '2.5/8"': 110000, '3.1/8"': 180000, '3.5/8"': 260000, '4.1/8"': 380000,
}

_TABELA_SUCCAO_BAIXA: dict[str, int] = {
    '1/2"': 1500, '5/8"': 3000, '3/4"': 4500, '7/8"': 7500,
    '1.1/8"': 12000, '1.3/8"': 20000, '1.5/8"': 28000, '2.1/8"': 45000,
    '2.5/8"': 85000, '3.1/8"': 130000, '3.5/8"': 190000, '4.1/8"': 280000,
}


def _selecionar_diametro(tabela: dict[str, int], capacidade: float, fator: float) -> str:
    for diam, cap_max in sorted(tabela.items(), key=lambda x: x[1]):
        if capacidade <= cap_max * fator:
            return diam
    return "Consultar Engenharia"


def calcular_tubulacao(req: TubulacaoRequest) -> TubulacaoResponse:
    if req.capacidade_real <= 100:
        raise ValueError("Capacidade muito baixa (mínimo 100 kcal/h).")

    fator_eficiencia = 0.5 if req.alta_eficiencia else 1.0

    fator_distancia = 1.0
    if req.distancia > 20:
        fator_distancia = 0.9
    if req.distancia > 40:
        fator_distancia = 0.8
    if req.distancia > 60:
        fator_distancia = 0.7

    diam_liquido = _selecionar_diametro(_TABELA_LIQUIDO, req.capacidade_real, fator_eficiencia)

    tabela_succao = _TABELA_SUCCAO_BAIXA if req.temp_evap <= -18 else _TABELA_SUCCAO_MEDIA
    diam_succao = _selecionar_diametro(
        tabela_succao, req.capacidade_real, fator_distancia * fator_eficiencia
    )

    qtd_tubo = math.ceil(req.distancia * 1.1)

    espessura_isolamento = "13mm"
    tipo_isolamento = "Polietileno"
    if req.temp_evap < -5:
        espessura_isolamento = "19mm"
    if req.temp_evap < -20:
        espessura_isolamento = "25mm (Blindado)"
        tipo_isolamento = "Elastômero de Alta Densidade"

    match = re.search(r"(\d+)", diam_succao)
    valor_diam = int(match.group()) if match else 1
    qtd_solda = math.ceil((qtd_tubo / 5) * (valor_diam / 2))

    materiais = [
        ItemTubulacao(item=f'Tubo Cobre {diam_liquido} (Líq)', quantidade=qtd_tubo, unidade="m", detalhe="Linha de alta pressão"),
        ItemTubulacao(item=f'Tubo Cobre {diam_succao} (Suc)', quantidade=qtd_tubo, unidade="m", detalhe=f"Sucção dimensionada com ΔT de {req.delta_t_selecionado}K"),
        ItemTubulacao(item=f'Isolamento {tipo_isolamento} {espessura_isolamento} para {diam_succao}', quantidade=int(qtd_tubo / 2) + 1, unidade="br", detalhe=f"Proteção contra condensação (Evap: {req.temp_evap}°C)"),
        ItemTubulacao(item="Solda Prata 15% / Foscoper", quantidade=qtd_solda, unidade="vareta", detalhe=f"Calculado para conexões de {diam_succao}"),
        ItemTubulacao(item="Fita PVC / Alumínio", quantidade=math.ceil(qtd_tubo / 10), unidade="rl", detalhe="Acabamento externo"),
    ]

    return TubulacaoResponse(
        diametro_liquido=diam_liquido,
        diametro_succao=diam_succao,
        distancia_considerada=req.distancia,
        temp_evap_calculada=req.temp_evap,
        lista_materiais=materiais,
    )
