from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClienteBase(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    contato: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    contato: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None


class ClienteOut(ClienteBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
