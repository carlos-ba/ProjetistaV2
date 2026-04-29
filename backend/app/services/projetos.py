from __future__ import annotations
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projeto import Projeto
from app.schemas.projeto import ProjetoCreate, ProjetoUpdate


async def create_projeto(db: AsyncSession, projeto_in: ProjetoCreate, owner_id: UUID | None = None) -> Projeto:
    db_projeto = Projeto(
        nome=projeto_in.nome,
        status=projeto_in.status,
        owner_id=owner_id,
    )
    db.add(db_projeto)
    await db.flush()
    await db.refresh(db_projeto)
    return db_projeto


async def get_projeto(db: AsyncSession, projeto_id: UUID, owner_id: UUID | None = None) -> Projeto | None:
    stmt = select(Projeto).where(Projeto.id == projeto_id)
    if owner_id is not None:
        stmt = stmt.where(Projeto.owner_id == owner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_projetos(db: AsyncSession, skip: int = 0, limit: int = 100, owner_id: UUID | None = None) -> list[Projeto]:
    stmt = select(Projeto)
    if owner_id is not None:
        stmt = stmt.where(Projeto.owner_id == owner_id)
    stmt = stmt.offset(skip).limit(limit).order_by(Projeto.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_projeto(db: AsyncSession, db_projeto: Projeto, projeto_in: ProjetoUpdate) -> Projeto:
    if projeto_in.nome is not None:
        db_projeto.nome = projeto_in.nome
    if projeto_in.status is not None:
        db_projeto.status = projeto_in.status
    await db.flush()
    await db.refresh(db_projeto)
    return db_projeto


async def delete_projeto(db: AsyncSession, db_projeto: Projeto) -> None:
    await db.delete(db_projeto)
    await db.flush()
