from decimal import Decimal
from typing import List, Any

from sqlalchemy import String, Numeric, ForeignKey, Integer, Float, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ComponenteTecnico(Base):
    __tablename__ = "componente_tecnico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_fabricante: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    conexao_entrada: Mapped[str] = mapped_column(String(20), nullable=False)
    conexao_saida: Mapped[str] = mapped_column(String(20), nullable=False)
    capacidade_nominal: Mapped[float] = mapped_column(Float, default=0)
    dados_especificos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    categoria: Mapped["Categoria"] = relationship(back_populates="componentes")
    fabricante: Mapped["Fabricante"] = relationship(back_populates="componentes")
    tabela_capacidade: Mapped[List["PerformanceComponente"]] = relationship(
        back_populates="componente", cascade="all, delete-orphan"
    )


class PerformanceComponente(Base):
    __tablename__ = "performance_componente"
    __table_args__ = (
        UniqueConstraint(
            "componente_id", "fluido", "temp_evaporacao", "temp_condensacao",
            name="uq_performance_componente"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    componente_id: Mapped[int] = mapped_column(ForeignKey("componente_tecnico.id", ondelete="CASCADE"), nullable=False)
    fluido: Mapped[str] = mapped_column(String(20), nullable=False)
    temp_evaporacao: Mapped[int] = mapped_column(Integer, nullable=False)
    temp_condensacao: Mapped[int] = mapped_column(Integer, default=45)
    capacidade_kcalh: Mapped[float] = mapped_column(Float, nullable=False)
    capacidade_min_kcalh: Mapped[float] = mapped_column(Float, default=0)

    componente: Mapped["ComponenteTecnico"] = relationship(back_populates="tabela_capacidade")
