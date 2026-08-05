from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ConfiguracaoMontagem(Base):
    __tablename__ = "configuracao_montagem"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=False)

    tipo_filtro: Mapped[str] = mapped_column(String(10), default="solda")
    tipo_visor: Mapped[str] = mapped_column(String(10), default="solda")
    trecho_vet_evap: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.50"))
    trecho_evap_sifao: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.50"))
    trecho_subida: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"))
    trecho_sifao_gbc: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.50"))
    incluir_filtro:      Mapped[bool] = mapped_column(Boolean, default=True)
    incluir_visor:       Mapped[bool] = mapped_column(Boolean, default=True)
    incluir_gbc_entrada: Mapped[bool] = mapped_column(Boolean, default=True)
    incluir_gbc_saida:   Mapped[bool] = mapped_column(Boolean, default=True)
