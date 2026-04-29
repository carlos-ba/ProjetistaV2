from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, JSON, func
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any

from app.models.base import Base

class Calculo(Base):
    __tablename__ = "calculo"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    projeto_id: Mapped[UUID] = mapped_column(ForeignKey("projeto.id", ondelete="CASCADE"), nullable=False)
    payload_entrada: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    resultado: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    versao_regra: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    projeto: Mapped["Projeto"] = relationship(back_populates="calculos")
