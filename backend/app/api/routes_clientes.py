from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.auth import UserOut
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteOut
from app.services import clientes as service
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/clientes", tags=["clientes"])


@router.get("", response_model=List[ClienteOut])
async def listar_clientes(
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    return await service.get_clientes(db, owner_id=usuario.id)


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def criar_cliente(
    payload: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    return await service.create_cliente(db, payload, owner_id=usuario.id)


@router.patch("/{cliente_id}", response_model=ClienteOut)
async def atualizar_cliente(
    cliente_id: UUID,
    payload: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    cliente = await service.get_cliente(db, cliente_id, owner_id=usuario.id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return await service.update_cliente(db, cliente, payload)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    cliente = await service.get_cliente(db, cliente_id, owner_id=usuario.id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    await service.delete_cliente(db, cliente)
