from uuid import UUID, uuid4
from typing import List, Optional

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.empresa import PAPEL_ADMIN


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuario"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Verificação de email
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Recuperação de senha
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Preferência: app só como seleção/lista de engenharia (sem jornada de orçamento)
    modo_engenharia: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Multi-tenancy — o escopo dos dados é a empresa; owner_id nos registros é o autor
    empresa_id: Mapped[UUID] = mapped_column(
        ForeignKey("empresa.id", ondelete="RESTRICT"), nullable=False
    )
    papel: Mapped[str] = mapped_column(String(30), default=PAPEL_ADMIN, server_default=PAPEL_ADMIN)

    empresa: Mapped["Empresa | None"] = relationship(back_populates="usuarios")

    projetos: Mapped[List["Projeto"]] = relationship(back_populates="owner")
    clientes: Mapped[List["Cliente"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
