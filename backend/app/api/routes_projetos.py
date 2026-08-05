from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.database.session import get_db
from app.schemas.auth import UserOut
from app.schemas.projeto import Projeto, ProjetoCreate, ProjetoUpdate, ProjetoComCalculos
from app.services import projetos as service_projetos
from app.services.auth import get_current_user, get_empresa_atual

router = APIRouter(prefix="/api/v1/projetos", tags=["projetos"])


@router.post("", response_model=Projeto, status_code=status.HTTP_201_CREATED)
async def criar_projeto(
    payload: ProjetoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    return await service_projetos.create_projeto(db, payload, owner_id=usuario.id, empresa_id=empresa_id)


@router.get("", response_model=List[Projeto])
async def listar_projetos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    return await service_projetos.get_projetos(db, skip, limit, empresa_id=empresa_id)


@router.get("/{projeto_id}", response_model=ProjetoComCalculos)
async def obter_projeto(
    projeto_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    db_projeto = await service_projetos.get_projeto(db, projeto_id, empresa_id=empresa_id)
    if not db_projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return db_projeto


@router.patch("/{projeto_id}", response_model=Projeto)
async def atualizar_projeto(
    projeto_id: UUID,
    payload: ProjetoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    db_projeto = await service_projetos.get_projeto(db, projeto_id, empresa_id=empresa_id)
    if not db_projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return await service_projetos.update_projeto(db, db_projeto, payload)


@router.delete("/{projeto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_projeto(
    projeto_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    db_projeto = await service_projetos.get_projeto(db, projeto_id, empresa_id=empresa_id)
    if not db_projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    await service_projetos.delete_projeto(db, db_projeto)
    return None
