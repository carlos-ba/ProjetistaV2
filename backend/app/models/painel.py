from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PainelFrigorifico(Base):
    __tablename__ = "painel_frigorifico"
    __table_args__ = (
        UniqueConstraint(
            "fabricante_id", "nucleo", "espessura_mm", "largura_mm",
            name="uq_painel_frigorifico"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    produto: Mapped[str] = mapped_column(String(100), nullable=False)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    nucleo: Mapped[str] = mapped_column(String(10), nullable=False)          # PIR, PUR, EPS
    espessura_mm: Mapped[int] = mapped_column(Integer, nullable=False)       # mm
    largura_mm: Mapped[int] = mapped_column(Integer, nullable=False)         # mm
    comprimento_max_m: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    auto_portancia_mm: Mapped[int] = mapped_column(Integer, nullable=True)   # vão máximo sem apoio
    peso_kg_m2: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=True)
    u_global: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False) # W/(m²·K) — dado real do fabricante
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)        # R$/m²

    fabricante: Mapped["Fabricante"] = relationship()
