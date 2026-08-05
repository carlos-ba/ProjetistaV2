from datetime import date
from uuid import UUID, uuid4
from typing import List, Optional

from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

# Papéis de usuário
PAPEL_SUPERADMIN = "superadmin_icenexus"   # equipe IceNexus — cura catálogo, acessa cross-empresa
PAPEL_ADMIN = "admin_empresa"              # administra a própria empresa
PAPEL_MEMBRO = "membro"                    # usa o app dentro da empresa

# Status de assinatura que liberam o uso
STATUS_ATIVOS = ("ativa", "trial")


class Empresa(Base, TimestampMixin):
    """Tenant. Todo dado de projeto/cliente/cotação é escopado por empresa."""

    __tablename__ = "empresa"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    plano: Mapped[str] = mapped_column(String(30), default="trial", server_default="trial")
    status_assinatura: Mapped[str] = mapped_column(String(20), default="ativa", server_default="ativa")
    assinatura_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assinatura_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="empresa")

    @property
    def ativa(self) -> bool:
        return self.status_assinatura in STATUS_ATIVOS
