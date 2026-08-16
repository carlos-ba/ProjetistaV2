from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.equipamento import Equipamento, PerformanceEquipamento
from app.schemas.selecao import SelecaoRequest, EquipamentoSelecionado


def _interpolar(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    if x1 == x2:
        return y1
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))


def _consumo_kw(ponto_acima, ponto_abaixo, temp_evaporacao: float) -> float | None:
    """Mesma lógica de interpolação da capacidade, mas pra consumo_kw — que é
    opcional no cadastro (~3% das UCs ainda não têm), então cai pro ponto que
    tiver valor quando não dá pra interpolar os dois."""
    ca = float(ponto_acima.consumo_kw) if ponto_acima and ponto_acima.consumo_kw is not None else None
    cb = float(ponto_abaixo.consumo_kw) if ponto_abaixo and ponto_abaixo.consumo_kw is not None else None
    if ponto_acima and ponto_acima.temp_evaporacao == temp_evaporacao:
        return ca
    if ca is not None and cb is not None:
        return _interpolar(
            temp_evaporacao,
            float(ponto_abaixo.temp_evaporacao), cb,
            float(ponto_acima.temp_evaporacao), ca,
        )
    return ca if ca is not None else cb


async def selecionar_equipamentos_db(req: SelecaoRequest, db: AsyncSession) -> list[EquipamentoSelecionado]:
    result = await db.execute(
        select(Equipamento)
        .join(Equipamento.categoria)
        .join(Equipamento.fabricante)
        .where(Equipamento.categoria.has(nome=req.tipo))
        .options(
            selectinload(Equipamento.performance),
            selectinload(Equipamento.fabricante),
        )
    )
    equipamentos = result.scalars().unique().all()

    candidatos: list[EquipamentoSelecionado] = []

    for eq in equipamentos:
        pontos = sorted(
            [p for p in eq.performance if p.fluido == req.fluido],
            key=lambda p: p.temp_evaporacao,
            reverse=True,
        )
        if not pontos:
            continue

        ponto_acima = None
        ponto_abaixo = None
        for p in pontos:
            if p.temp_evaporacao >= req.temp_evaporacao:
                ponto_acima = p
            if p.temp_evaporacao <= req.temp_evaporacao:
                ponto_abaixo = p
                break

        if ponto_acima and ponto_acima.temp_evaporacao == req.temp_evaporacao:
            capacidade = float(ponto_acima.capacidade)
        elif ponto_acima and ponto_abaixo:
            capacidade = _interpolar(
                req.temp_evaporacao,
                float(ponto_abaixo.temp_evaporacao), float(ponto_abaixo.capacidade),
                float(ponto_acima.temp_evaporacao), float(ponto_acima.capacidade),
            )
        else:
            continue

        consumo_kw = _consumo_kw(ponto_acima, ponto_abaixo, req.temp_evaporacao)

        if req.carga_termica_total <= 0:
            continue

        diff = capacidade - req.carga_termica_total
        percentual = (capacidade / req.carga_termica_total) * 100

        if not (80 <= percentual <= 300):
            continue

        status = "ideal"
        if percentual < 90:
            status = "menor"
        elif percentual > 110:
            status = "maior"

        candidatos.append(EquipamentoSelecionado(
            id=eq.id,
            modelo=eq.modelo,
            fabricante=eq.fabricante.nome,
            capacidade_real=round(capacidade, 0),
            vazao_ar=eq.vazao_ar_m3h,
            preco=float(eq.custo),
            diferenca=round(diff, 2),
            percentual=round(percentual, 1),
            status=status,
            volume_interno_kg=float(eq.volume_interno_kg) if eq.volume_interno_kg else None,
            conexao_liquido=eq.conexao_liquido,
            conexao_succao=eq.conexao_succao,
            consumo_kw=round(consumo_kw, 2) if consumo_kw is not None else None,
        ))

    candidatos.sort(key=lambda x: abs(x.diferenca))
    return candidatos[:5]
