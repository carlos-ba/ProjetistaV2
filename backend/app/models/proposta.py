from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PropostaComercial(Base, TimestampMixin):
    __tablename__ = "proposta_comercial"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    projeto_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("projeto.id", ondelete="SET NULL"), nullable=True
    )
    # rascunho | enviada | aceita | recusada
    status: Mapped[str] = mapped_column(String(20), default="rascunho")
    # Composição completa: fonte de preços, custos, margem, condições, valores
    dados: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
