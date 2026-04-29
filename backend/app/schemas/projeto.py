from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any

class ProjetoBase(BaseModel):
    nome: str
    status: str = "rascunho"

class ProjetoCreate(ProjetoBase):
    pass

class ProjetoUpdate(BaseModel):
    nome: Optional[str] = None
    status: Optional[str] = None

class Projeto(ProjetoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

from app.schemas.calculo import CalculoResponse

class ProjetoComCalculos(Projeto):
    calculos: List[CalculoResponse] = []
