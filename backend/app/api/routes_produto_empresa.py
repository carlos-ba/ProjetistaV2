"""Lista de preços por empresa (Fase B) — autoadministração.

O admin_empresa (ou superadmin, pra própria empresa) cadastra/edita a própria lista de
preços sem precisar acionar o superadmin pra cada mudança. `membro` só lê (usa o
mapa de preços pra gerar orçamento, mas não edita a lista).

Implantação pelo superadmin em QUALQUER empresa é um conjunto de rotas à parte —
ver `/api/v1/admin/empresas/{empresa_id}/produtos` em `routes_admin.py`.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.empresa import PAPEL_ADMIN, PAPEL_SUPERADMIN
from app.schemas.auth import UserOut
from app.schemas.produto_empresa import ProdutoEmpresaCreate, ProdutoEmpresaUpdate, ProdutoEmpresaOut, ItemMapaPreco
from app.services.auth import get_current_user, get_empresa_atual
from app.services.produto_empresa import (
    listar_produtos, criar_produto, atualizar_produto, remover_produto, obter_mapa_precos,
)

router = APIRouter(prefix="/api/v1/produto-empresa", tags=["produto-empresa"])


async def _exigir_editor(usuario: UserOut = Depends(get_current_user)) -> UUID:
    """admin_empresa ou superadmin, editando a própria empresa."""
    if not usuario.empresa_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                             detail="Usuário sem empresa vinculada. Contate o administrador.")
    if usuario.papel not in (PAPEL_ADMIN, PAPEL_SUPERADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                             detail="Só administradores da empresa editam a lista de preços.")
    return usuario.empresa_id


@router.get("", response_model=list[ProdutoEmpresaOut])
async def listar(
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    return await listar_produtos(db, empresa_id)


@router.get("/mapa-precos", response_model=dict[str, ItemMapaPreco])
async def mapa_precos(
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    """Descrição normalizada → preço sugerido (lista da empresa ou última cotação
    confirmada). Consumido pelo frontend antes de gerar o orçamento."""
    return await obter_mapa_precos(db, empresa_id)


@router.post("", response_model=ProdutoEmpresaOut, status_code=status.HTTP_201_CREATED)
async def criar(
    payload: ProdutoEmpresaCreate,
    empresa_id: UUID = Depends(_exigir_editor),
    db: AsyncSession = Depends(get_db),
):
    return await criar_produto(db, empresa_id, payload)


@router.patch("/{produto_id}", response_model=ProdutoEmpresaOut)
async def atualizar(
    produto_id: int,
    payload: ProdutoEmpresaUpdate,
    empresa_id: UUID = Depends(_exigir_editor),
    db: AsyncSession = Depends(get_db),
):
    return await atualizar_produto(db, empresa_id, produto_id, payload)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(
    produto_id: int,
    empresa_id: UUID = Depends(_exigir_editor),
    db: AsyncSession = Depends(get_db),
):
    await remover_produto(db, empresa_id, produto_id)
