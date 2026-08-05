from typing import Any, List
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Projeto(Base, TimestampMixin):
    __tablename__ = "projeto"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cliente: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="rascunho")
    dados_completos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)

    owner: Mapped["Usuario | None"] = relationship(back_populates="projetos")
    calculos: Mapped[List["Calculo"]] = relationship(back_populates="projeto", cascade="all, delete-orphan")
