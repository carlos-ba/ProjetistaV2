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


def _bracket(pontos_desc: list, valor: float, attr: str):
    """Acha o ponto imediatamente acima e abaixo de `valor` no atributo `attr`,
    dado `pontos_desc` já ordenado descendente por esse atributo e sem empates
    nesse atributo (garantido pela chave única do cadastro dentro de um mesmo
    grupo de T.Ambiente). None em algum lado => `valor` está fora do intervalo
    cadastrado — não extrapola."""
    acima = None
    abaixo = None
    for p in pontos_desc:
        v = getattr(p, attr)
        if v >= valor:
            acima = p
        if v <= valor:
            abaixo = p
            break
    return acima, abaixo


def _capacidade_em_ambiente(pontos_evap_desc: list, temp_evaporacao: float) -> tuple[float, float | None] | None:
    """Capacidade e consumo_kw interpolados em T.Evaporação, dentro de UM grupo
    de T.Ambiente fixo (mesma regra de interpolação de sempre). None se
    T.Evaporação sai do intervalo cadastrado pra esse grupo."""
    acima, abaixo = _bracket(pontos_evap_desc, temp_evaporacao, "temp_evaporacao")
    if not (acima and abaixo):
        return None
    if acima.temp_evaporacao == temp_evaporacao:
        capacidade = float(acima.capacidade)
    else:
        capacidade = _interpolar(
            temp_evaporacao,
            float(abaixo.temp_evaporacao), float(abaixo.capacidade),
            float(acima.temp_evaporacao), float(acima.capacidade),
        )
    return capacidade, _consumo_kw(acima, abaixo, temp_evaporacao)


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
        pontos_fluido = [p for p in eq.performance if p.fluido == req.fluido]
        if not pontos_fluido:
            continue

        # Agrupa por T.Ambiente cadastrada — cada grupo é uma curva em T.Evaporação,
        # exatamente como antes; a novidade é interpolar TAMBÉM entre grupos.
        por_ambiente: dict[int, list] = {}
        for p in pontos_fluido:
            por_ambiente.setdefault(p.temp_ambiente, []).append(p)
        for grupo in por_ambiente.values():
            grupo.sort(key=lambda p: p.temp_evaporacao, reverse=True)

        if len(por_ambiente) == 1:
            # Só existe UM ponto de T.Ambiente cadastrado pra esse fluido/equipamento
            # — não há eixo real pra bracketar. Caso normal da Evaporadora: capacidade
            # não depende de T.Ambiente (só de T.Evaporação), então o cadastro só tem
            # um valor-placeholder (hoje sempre 32°C) em vez de uma curva de verdade.
            # Usa esse único ponto direto, sem exigir que a T.Ambiente do projeto caia
            # dentro de nenhum intervalo — do contrário qualquer T.Ambiente ≠ placeholder
            # zerava a busca de evaporador.
            unico_amb = next(iter(por_ambiente))
            resultado_acima = _capacidade_em_ambiente(por_ambiente[unico_amb], req.temp_evaporacao)
            if resultado_acima is None:
                continue
            capacidade, consumo_kw = resultado_acima
        else:
            amb_acima = amb_abaixo = None
            for a in sorted(por_ambiente.keys(), reverse=True):
                if a >= req.temp_ambiente:
                    amb_acima = a
                if a <= req.temp_ambiente:
                    amb_abaixo = a
                    break
            if amb_abaixo is None and amb_acima is not None:
                # T.Ambiente do projeto abaixo do menor ponto cadastrado — clampa no piso
                # em vez de descartar. Seguro: capacidade real a uma T.Ambiente menor
                # tende a ser MAIOR que no piso cadastrado (menos pressão de condensação),
                # nunca menor — não superdimensiona. Extrapolar pra CIMA do maior ponto
                # cadastrado continua proibido (capacidade cairia, seria otimista).
                amb_abaixo = amb_acima
            if amb_acima is None or amb_abaixo is None:
                continue  # T.Ambiente do projeto acima do maior ponto cadastrado — não extrapola

            resultado_acima = _capacidade_em_ambiente(por_ambiente[amb_acima], req.temp_evaporacao)
            if resultado_acima is None:
                continue

            if amb_acima == amb_abaixo:
                capacidade, consumo_kw = resultado_acima
            else:
                resultado_abaixo = _capacidade_em_ambiente(por_ambiente[amb_abaixo], req.temp_evaporacao)
                if resultado_abaixo is None:
                    continue
                cap_acima, cons_acima = resultado_acima
                cap_abaixo, cons_abaixo = resultado_abaixo
                capacidade = _interpolar(req.temp_ambiente, amb_abaixo, cap_abaixo, amb_acima, cap_acima)
                if cons_acima is not None and cons_abaixo is not None:
                    consumo_kw = _interpolar(req.temp_ambiente, amb_abaixo, cons_abaixo, amb_acima, cons_acima)
                else:
                    consumo_kw = cons_acima if cons_acima is not None else cons_abaixo

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
