from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.catalogo import Categoria
from app.models.componente import ComponenteTecnico, PerformanceComponente
from app.schemas.componente import ComponenteFluxoRequest, ComponenteSelecionado

# Categorias selecionadas por faixa de capacidade + temperatura de evaporação
_CATEGORIAS_POR_TEMP_EVAP = [
    "Válvula de Expansão Termostática",
    "Filtro Secador",
    "Válvula Solenoide",
]

# Categorias selecionadas apenas por capacidade (temperatura é referência, não filtro rígido)
_CATEGORIAS_POR_CAPACIDADE = [
    "Separador de Líquido",
]


async def _buscar_por_temp_e_capacidade(
    db: AsyncSession,
    cat_nome: str,
    fluido: str,
    temp_evap: float,
    capacidade: float,
) -> PerformanceComponente | None:
    """Busca componente filtrando por fluido, T.Evap ≤ T.Projeto e faixa de capacidade."""
    stmt = (
        select(PerformanceComponente)
        .join(PerformanceComponente.componente)
        .join(ComponenteTecnico.categoria)
        .join(ComponenteTecnico.fabricante)
        .where(
            Categoria.nome == cat_nome,
            PerformanceComponente.fluido == fluido,
            PerformanceComponente.temp_evaporacao <= temp_evap,
            PerformanceComponente.capacidade_kcalh >= capacidade,
            PerformanceComponente.capacidade_min_kcalh <= capacidade,
        )
        .options(
            selectinload(PerformanceComponente.componente).selectinload(ComponenteTecnico.categoria),
            selectinload(PerformanceComponente.componente).selectinload(ComponenteTecnico.fabricante),
        )
        .order_by(PerformanceComponente.capacidade_kcalh)
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _interpolar(t: float, t1: float, v1: float, t2: float, v2: float) -> float:
    """Interpolação linear entre dois pontos."""
    if t1 == t2:
        return v1
    return v1 + (t - t1) * (v2 - v1) / (t2 - t1)


async def _buscar_por_capacidade_interpolado(
    db: AsyncSession,
    cat_nome: str,
    fluido: str,
    temp_evap: float,
    capacidade: float,
) -> tuple[ComponenteTecnico | None, float, float]:
    """
    Seleciona componente por interpolação linear na T.Evap do projeto.

    Para cada modelo:
      1. Encontra os dois pontos da tabela que cercam T.Evap do projeto
      2. Interpola cap_max e cap_min na T.Evap exata
      3. Verifica se capacidade_projeto está dentro da faixa interpolada

    Retorna (componente, cap_max_interp, cap_min_interp) do menor modelo adequado.
    """
    # Carregar todos os pontos da categoria agrupados por componente
    stmt = (
        select(ComponenteTecnico)
        .join(ComponenteTecnico.categoria)
        .join(ComponenteTecnico.fabricante)
        .where(Categoria.nome == cat_nome)
        .options(
            selectinload(ComponenteTecnico.tabela_capacidade),
            selectinload(ComponenteTecnico.categoria),
            selectinload(ComponenteTecnico.fabricante),
        )
        .order_by(ComponenteTecnico.capacidade_nominal)   # menor primeiro
    )
    result = await db.execute(stmt)
    componentes = result.scalars().unique().all()

    for comp in componentes:
        # Filtrar pontos do fluido solicitado, ordenados por T.Evap decrescente
        pontos = sorted(
            [p for p in comp.tabela_capacidade if p.fluido == fluido],
            key=lambda p: p.temp_evaporacao,
            reverse=True,
        )
        if not pontos:
            continue

        # Encontrar ponto acima e abaixo da T.Evap do projeto
        p_acima  = None
        p_abaixo = None
        for p in pontos:
            if p.temp_evaporacao >= temp_evap:
                p_acima = p
            if p.temp_evaporacao <= temp_evap:
                p_abaixo = p
                break

        # Calcular capacidades interpoladas
        if p_acima and p_acima.temp_evaporacao == temp_evap:
            # Ponto exato na tabela
            cap_max_i = float(p_acima.capacidade_kcalh)
            cap_min_i = float(p_acima.capacidade_min_kcalh)

        elif p_acima and p_abaixo:
            # Interpolação linear entre os dois pontos
            t1, t2 = float(p_acima.temp_evaporacao), float(p_abaixo.temp_evaporacao)
            cap_max_i = _interpolar(
                temp_evap, t1, float(p_acima.capacidade_kcalh),
                t2, float(p_abaixo.capacidade_kcalh)
            )
            cap_min_i = _interpolar(
                temp_evap, t1, float(p_acima.capacidade_min_kcalh),
                t2, float(p_abaixo.capacidade_min_kcalh)
            )

        elif p_abaixo:
            # T.Evap acima do maior ponto da tabela → usa o maior ponto
            cap_max_i = float(p_abaixo.capacidade_kcalh)
            cap_min_i = float(p_abaixo.capacidade_min_kcalh)

        else:
            continue

        # Verificar se a capacidade do projeto está na faixa
        if cap_min_i <= capacidade <= cap_max_i:
            return comp, cap_max_i, cap_min_i

    return None, 0.0, 0.0


async def selecionar_componentes_fluxo(
    req: ComponenteFluxoRequest, db: AsyncSession
) -> list[ComponenteSelecionado]:
    selecionados: list[ComponenteSelecionado] = []

    for cat_nome in _CATEGORIAS_POR_TEMP_EVAP:
        melhor = await _buscar_por_temp_e_capacidade(
            db, cat_nome, req.fluido, req.temp_evap, req.capacidade_kcalh
        )
        if melhor:
            comp = melhor.componente
            selecionados.append(ComponenteSelecionado(
                categoria=cat_nome,
                modelo=comp.modelo,
                codigo_fabricante=comp.codigo_fabricante,
                fabricante=comp.fabricante.nome,
                conexao_entrada=comp.conexao_entrada,
                custo=float(comp.custo),
                faixa_operacao=f"{melhor.capacidade_min_kcalh:.0f} a {melhor.capacidade_kcalh:.0f} kcal/h",
            ))

    for cat_nome in _CATEGORIAS_POR_CAPACIDADE:
        comp, cap_max_i, cap_min_i = await _buscar_por_capacidade_interpolado(
            db, cat_nome, req.fluido, req.temp_evap, req.capacidade_kcalh
        )
        if comp:
            selecionados.append(ComponenteSelecionado(
                categoria=cat_nome,
                modelo=comp.modelo,
                codigo_fabricante=comp.codigo_fabricante,
                fabricante=comp.fabricante.nome,
                conexao_entrada=comp.conexao_entrada,
                custo=float(comp.custo),
                faixa_operacao=(
                    f"{cap_min_i:.0f} a {cap_max_i:.0f} kcal/h "
                    f"@ {req.temp_evap:.0f}°C (interpolado)"
                ),
            ))

    return selecionados
