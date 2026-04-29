from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.catalogo import (
    Categoria, Fabricante, UnidadeMedida,
    TipoProdutoTermico, PerfilProdutoTermico,
)
from app.models.equipamento import Equipamento
from app.models.material import Material


async def listar_perfis_produto(db: AsyncSession):
    result = await db.execute(
        select(PerfilProdutoTermico).order_by(PerfilProdutoTermico.tipo_id, PerfilProdutoTermico.nome)
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
