from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.catalogo import (
    CategoriaOut, FabricanteOut, PerfilProdutoTermicoOut,
    TipoProdutoTermicoOut, MaterialOut, EquipamentoOut,
)
from app.services.catalogo import (
    listar_categorias, listar_fabricantes, listar_perfis_produto,
    listar_tipos_produto, listar_materiais, listar_equipamentos,
)

router = APIRouter(prefix="/api/v1/catalogo", tags=["catalogo"])


@router.get("/perfis-produto", response_model=list[PerfilProdutoTermicoOut])
async def get_perfis_produto(db: AsyncSession = Depends(get_db)):
    return await listar_perfis_produto(db)


@router.get("/tipos-produto", response_model=list[TipoProdutoTermicoOut])
async def get_tipos_produto(db: AsyncSession = Depends(get_db)):
    return await listar_tipos_produto(db)


@router.get("/categorias", response_model=list[CategoriaOut])
async def get_categorias(db: AsyncSession = Depends(get_db)):
    return await listar_categorias(db)


@router.get("/fabricantes", response_model=list[FabricanteOut])
async def get_fabricantes(db: AsyncSession = Depends(get_db)):
    return await listar_fabricantes(db)


@router.get("/materiais", response_model=list[MaterialOut])
async def get_materiais(db: AsyncSession = Depends(get_db)):
    return await listar_materiais(db)


@router.get("/equipamentos", response_model=list[EquipamentoOut])
async def get_equipamentos(
    categoria: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await listar_equipamentos(db, categoria)
