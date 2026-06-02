from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IsolamentoTubulacao(Base):
    """
    Catálogo de isolamentos para tubulação frigorífica (espuma elastomérica).

    Padrões de espessura:
      D → 6 a 7,5 mm   | F → 9 a 12 mm   | H → 13 a 16 mm
      M → 19 a 26 mm   | R → 25 a 32,5 mm | T → 32 a 45 mm

    Seleção: diametro_cu_mm + padrao → referencia + espessura_mm real
    """
    __tablename__ = "isolamento_tubulacao"
    __table_args__ = (
        UniqueConstraint("fabricante_id", "padrao", "referencia",
                         name="uq_isolamento_tubulacao"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)

    diametro_cu_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    diametro_fe_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    diametro_interno_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    diametro_interno_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)

    padrao: Mapped[str] = mapped_column(String(2),  nullable=False)   # D F H M R T
    referencia: Mapped[str] = mapped_column(String(20), nullable=False)  # ex: F-22
    espessura_mm: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    fabricante: Mapped["Fabricante"] = relationship()
