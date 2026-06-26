from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Dict

class ProjetoBase(BaseModel):
    nome: str
    cliente: Optional[str] = None
    status: str = "rascunho"

class ProjetoCreate(ProjetoBase):
    dados_completos: Optional[Dict[str, Any]] = None

class ProjetoUpdate(BaseModel):
    nome: Optional[str] = None
    cliente: Optional[str] = None
    status: Optional[str] = None
    dados_completos: Optional[Dict[str, Any]] = None

class Projeto(ProjetoBase):
    id: UUID
    dados_completos: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from app.schemas.calculo import CalculoResponse

class ProjetoComCalculos(Projeto):
    calculos: List[CalculoResponse] = []
