from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.calculo import Calculo
from app.schemas.calculo import CalculoResultado, EquipamentoEntrada, SelecaoEquipamento, CalculoRequest


def interpolar_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    if x1 == x2:
        return y1
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))


@dataclass
class ParametrosSelecao:
    carga_termica_total: float
    temp_evap_projeto: float
    fluido_projeto: str
    tipo_equipamento: str


def _capacidade_interpolada(equipamento: EquipamentoEntrada, temp_evap: float) -> float | None:
    pontos = sorted(equipamento.pontos, key=lambda p: p.temp_evaporacao, reverse=True)
    if not pontos:
        return None

    ponto_acima = None
    ponto_abaixo = None
    for p in pontos:
        if p.temp_evaporacao >= temp_evap:
            ponto_acima = p
        if p.temp_evaporacao <= temp_evap:
            ponto_abaixo = p
            break

    if ponto_acima and ponto_abaixo and ponto_acima.temp_evaporacao == temp_evap:
        return ponto_acima.capacidade
    if ponto_acima and ponto_abaixo:
        return interpolar_linear(
            temp_evap,
            ponto_abaixo.temp_evaporacao,
            ponto_abaixo.capacidade,
            ponto_acima.temp_evaporacao,
            ponto_acima.capacidade,
        )
    return None


def selecionar_equipamentos(
    equipamentos: list[EquipamentoEntrada],
    parametros: ParametrosSelecao,
) -> list[SelecaoEquipamento]:
    candidatos: list[SelecaoEquipamento] = []

    for eq in equipamentos:
        if eq.fluido != parametros.fluido_projeto:
            continue
        if eq.categoria != parametros.tipo_equipamento:
            continue

        capacidade_calculada = _capacidade_interpolada(eq, parametros.temp_evap_projeto)
        if capacidade_calculada is None or parametros.carga_termica_total <= 0:
            continue

        diff = capacidade_calculada - parametros.carga_termica_total
        percentual = (capacidade_calculada / parametros.carga_termica_total) * 100

        if not 80 <= percentual <= 300:
            continue

        status = "ideal"
        if percentual < 90:
            status = "menor"
        elif percentual > 110:
            status = "maior"

        candidatos.append(
            SelecaoEquipamento(
                id=eq.id,
                modelo=eq.modelo,
                fabricante=eq.fabricante,
                capacidade_real=round(capacidade_calculada, 0),
                vazao_ar=eq.vazao_ar_m3h,
                preco=eq.preco,
                diferenca=diff,
                percentual=round(percentual, 1),
                status=status,
            )
        )

    candidatos.sort(key=lambda x: abs(x.diferenca))
    return candidatos[:5]


def calcular_volume_e_selecao(
    largura: float,
    altura: float,
    comprimento: float,
    equipamentos: list[EquipamentoEntrada],
    temp_evaporacao: float,
    fluido: str,
    tipo_equipamento: str,
) -> CalculoResultado:
    volume = largura * altura * comprimento
    # Estimativa simples para o MVP de contrato
    carga_estimativa_kcalh = round(volume * 1000, 2)

    parametros = ParametrosSelecao(
        carga_termica_total=carga_estimativa_kcalh,
        temp_evap_projeto=temp_evaporacao,
        fluido_projeto=fluido,
        tipo_equipamento=tipo_equipamento,
    )
    selecao = selecionar_equipamentos(equipamentos=equipamentos, parametros=parametros)

    return CalculoResultado(
        volume=round(volume, 2),
        carga_estimativa_kcalh=carga_estimativa_kcalh,
        selecao=selecao,
    )


async def processar_e_salvar_calculo(
    db: AsyncSession,
    payload: CalculoRequest
) -> Calculo:
    resultado = calcular_volume_e_selecao(
        largura=payload.entrada.largura,
        altura=payload.entrada.altura,
        comprimento=payload.entrada.comprimento,
        equipamentos=payload.equipamentos,
        temp_evaporacao=payload.temp_evaporacao,
        fluido=payload.fluido,
        tipo_equipamento=payload.tipo_equipamento,
    )
    
    db_calculo = Calculo(
        projeto_id=payload.projeto_id,
        payload_entrada=payload.model_dump(),
        resultado=resultado.model_dump(),
        versao_regra="v1"
    )
    
    db.add(db_calculo)
    await db.flush()
    await db.refresh(db_calculo)
    return db_calculo
