from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.catalogo import (
    Categoria, Fabricante, UnidadeMedida,
    TipoProdutoTermico, PerfilProdutoTermico,
)
from app.models.equipamento import Equipamento
from app.models.material import Material
from app.models.painel import PainelFrigorifico
from app.models.porta import PortaFrigoriifica


async def listar_perfis_produto(db: AsyncSession):
    result = await db.execute(
        select(PerfilProdutoTermico)
        .options(selectinload(PerfilProdutoTermico.tipo))   # eager load do objeto tipo
        .order_by(PerfilProdutoTermico.tipo_id, PerfilProdutoTermico.nome)
    )
    return result.scalars().all()


async def listar_tipos_produto(db: AsyncSession):
    result = await db.execute(select(TipoProdutoTermico).order_by(TipoProdutoTermico.nome))
    return result.scalars().all()


async def listar_categorias(db: AsyncSession):
    result = await db.execute(select(Categoria).order_by(Categoria.nome))
    return result.scalars().all()


async def listar_fabricantes(db: AsyncSession):
    result = await db.execute(select(Fabricante).order_by(Fabricante.nome))
    return result.scalars().all()


async def listar_materiais(db: AsyncSession):
    result = await db.execute(select(Material).order_by(Material.nome))
    return result.scalars().all()


async def listar_equipamentos(db: AsyncSession, categoria_nome: str | None = None):
    stmt = select(Equipamento)
    if categoria_nome:
        stmt = stmt.join(Equipamento.categoria).where(Equipamento.categoria.has(nome=categoria_nome))
    stmt = stmt.order_by(Equipamento.modelo)
    result = await db.execute(stmt)
    return result.scalars().all()


async def listar_paineis(
    db: AsyncSession,
    fabricante_id: int | None = None,
    nucleo: str | None = None,
    espessura_mm: int | None = None,
) -> list[PainelFrigorifico]:
    stmt = (
        select(PainelFrigorifico)
        .options(selectinload(PainelFrigorifico.fabricante))
        .order_by(PainelFrigorifico.nucleo, PainelFrigorifico.espessura_mm, PainelFrigorifico.largura_mm)
    )
    if fabricante_id:
        stmt = stmt.where(PainelFrigorifico.fabricante_id == fabricante_id)
    if nucleo:
        stmt = stmt.where(PainelFrigorifico.nucleo == nucleo.upper())
    if espessura_mm:
        stmt = stmt.where(PainelFrigorifico.espessura_mm == espessura_mm)
    result = await db.execute(stmt)
    return result.scalars().all()


async def listar_fabricantes_paineis(db: AsyncSession) -> list[Fabricante]:
    """Retorna apenas fabricantes que possuem painéis cadastrados."""
    from sqlalchemy import distinct
    result = await db.execute(
        select(Fabricante)
        .where(Fabricante.id.in_(
            select(distinct(PainelFrigorifico.fabricante_id))
        ))
        .order_by(Fabricante.nome)
    )
    return result.scalars().all()


async def listar_portas(
    db: AsyncSession,
    classificacao: str | None = None,
    tipo: str | None = None,
) -> list[PortaFrigoriifica]:
    """Lista portas frigoríficas com filtros opcionais."""
    stmt = (
        select(PortaFrigoriifica)
        .options(selectinload(PortaFrigoriifica.fabricante))
        .order_by(PortaFrigoriifica.classificacao, PortaFrigoriifica.largura_mm)
    )
    if classificacao:
        stmt = stmt.where(PortaFrigoriifica.classificacao == classificacao.lower())
    if tipo:
        stmt = stmt.where(PortaFrigoriifica.tipo == tipo.lower())
    result = await db.execute(stmt)
    return result.scalars().all()
