from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate


async def get_clientes(db: AsyncSession, owner_id: UUID):
    result = await db.execute(
        select(Cliente).where(Cliente.owner_id == owner_id).order_by(Cliente.nome)
    )
    return result.scalars().all()


async def get_cliente(db: AsyncSession, cliente_id: UUID, owner_id: UUID):
    result = await db.execute(
        select(Cliente).where(Cliente.id == cliente_id, Cliente.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def create_cliente(db: AsyncSession, payload: ClienteCreate, owner_id: UUID):
    cliente = Cliente(**payload.model_dump(), owner_id=owner_id)
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def update_cliente(db: AsyncSession, cliente: Cliente, payload: ClienteUpdate):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, field, value)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def delete_cliente(db: AsyncSession, cliente: Cliente):
    await db.delete(cliente)
    await db.commit()
