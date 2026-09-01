from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.catalogo import (
    CategoriaOut, FabricanteOut, PerfilProdutoTermicoOut,
    TipoProdutoTermicoOut, MaterialOut, EquipamentoOut,
    PainelFrigorificoOut, PortaFrigoriificaOut, PerfilMetalicoOut,
)
from app.services.catalogo import (
    listar_categorias, listar_fabricantes, listar_perfis_produto,
    listar_tipos_produto, listar_materiais, listar_equipamentos,
    listar_paineis, listar_fabricantes_paineis, listar_portas,
    listar_perfis_metalicos,
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


@router.get("/paineis/fabricantes", response_model=list[FabricanteOut])
async def get_fabricantes_paineis(db: AsyncSession = Depends(get_db)):
    """Fabricantes que possuem painéis frigoríficos cadastrados."""
    return await listar_fabricantes_paineis(db)


@router.get("/paineis", response_model=list[PainelFrigorificoOut])
async def get_paineis(
    fabricante_id: int | None = Query(default=None),
    nucleo: str | None = Query(default=None),
    espessura_mm: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Lista painéis com filtros opcionais: fabricante, núcleo, espessura."""
    return await listar_paineis(db, fabricante_id, nucleo, espessura_mm)


@router.get("/portas", response_model=list[PortaFrigoriificaOut])
async def get_portas(
    classificacao: str | None = Query(default=None, description="resfriados | congelada | ultra-congelada"),
    tipo: str | None = Query(default=None, description="giratoria | deslizante | rapida"),
    db: AsyncSession = Depends(get_db),
):
    """Lista portas frigoríficas com filtros opcionais."""
    return await listar_portas(db, classificacao, tipo)


@router.get("/perfis-metalicos", response_model=list[PerfilMetalicoOut])
async def get_perfis_metalicos(
    tipo: str | None = Query(default=None, description="Ângulo Interno | Ângulo Externo | Liso | U | Z"),
    db: AsyncSession = Depends(get_db),
):
    """Lista perfis metálicos, usado na seleção manual de perfis extras (Card 1)."""
    return await listar_perfis_metalicos(db, tipo)
