from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.catalogo import Categoria
from app.models.componente import ComponenteTecnico, PerformanceComponente
from app.schemas.componente import ComponenteFluxoRequest, ComponenteSelecionado

_CATEGORIAS_OBRIGATORIAS = [
    "Válvula de Expansão",
    "Filtro Secador",
    "Válvula Solenoide",
    "Acumulador de Sucção",
    "Separador de Óleo",
    "Separador de Líquido",
]


async def selecionar_componentes_fluxo(req: ComponenteFluxoRequest, db: AsyncSession) -> list[ComponenteSelecionado]:
    selecionados: list[ComponenteSelecionado] = []

    for cat_nome in _CATEGORIAS_OBRIGATORIAS:
        stmt = (
            select(PerformanceComponente)
            .join(PerformanceComponente.componente)
            .join(ComponenteTecnico.categoria)
            .join(ComponenteTecnico.fabricante)
            .where(
                Categoria.nome == cat_nome,
                PerformanceComponente.fluido == req.fluido,
                PerformanceComponente.temp_evaporacao <= req.temp_evap,
                PerformanceComponente.capacidade_kcalh >= req.capacidade_kcalh,
                PerformanceComponente.capacidade_min_kcalh <= req.capacidade_kcalh,
            )
            .options(
                selectinload(PerformanceComponente.componente).selectinload(ComponenteTecnico.categoria),
                selectinload(PerformanceComponente.componente).selectinload(ComponenteTecnico.fabricante),
            )
            .order_by(PerformanceComponente.capacidade_kcalh)
            .limit(1)
        )
        result = await db.execute(stmt)
        melhor = result.scalar_one_or_none()

        if not melhor:
            continue

        comp = melhor.componente
        selecionados.append(ComponenteSelecionado(
            categoria=cat_nome,
            modelo=comp.modelo,
            codigo_fabricante=comp.codigo_fabricante,
            fabricante=comp.fabricante.nome,
            conexao_entrada=comp.conexao_entrada,
            custo=float(comp.custo),
            faixa_operacao=f"{melhor.capacidade_min_kcalh} a {melhor.capacidade_kcalh} kcal/h",
        ))

    return selecionados
