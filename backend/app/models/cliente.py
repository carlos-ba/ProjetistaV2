from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Cliente(Base, TimestampMixin):
    __tablename__ = "cliente"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contato: Mapped[str | None] = mapped_column(String(100), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)

    owner: Mapped["Usuario"] = relationship(back_populates="clientes")
