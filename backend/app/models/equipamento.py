from decimal import Decimal
from typing import List

from sqlalchemy import String, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Equipamento(Base):
    __tablename__ = "equipamento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    unidade_medida_id: Mapped[int] = mapped_column(ForeignKey("unidade_medida.id"), nullable=False)

    qtde_ventiladores: Mapped[int] = mapped_column(Integer, default=0)
    diametro_ventilador_mm: Mapped[int] = mapped_column(Integer, default=0)
    vazao_ar_m3h: Mapped[int] = mapped_column(Integer, default=0)
    flecha_ar_m: Mapped[int] = mapped_column(Integer, default=0)

    # Dados físicos para estimativa de carga de fluido
    volume_interno_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    conexao_liquido:   Mapped[str | None]     = mapped_column(String(10),    nullable=True)
    conexao_succao:    Mapped[str | None]     = mapped_column(String(10),    nullable=True)

    categoria: Mapped["Categoria"] = relationship(back_populates="equipamentos")
    fabricante: Mapped["Fabricante"] = relationship(back_populates="equipamentos")
    unidade_medida: Mapped["UnidadeMedida"] = relationship(back_populates="equipamentos")
    performance: Mapped[List["PerformanceEquipamento"]] = relationship(
        back_populates="equipamento", cascade="all, delete-orphan"
    )


class PerformanceEquipamento(Base):
    __tablename__ = "performance_equipamento"
    __table_args__ = (
        UniqueConstraint(
            "equipamento_id", "fluido", "temp_ambiente", "temp_evaporacao", "delta_t",
            name="uq_performance_equipamento"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False)
    fluido: Mapped[str] = mapped_column(String(20), nullable=False)
    temp_ambiente: Mapped[int] = mapped_column(Integer, default=32)   # °C — T.Amb do catálogo do fabricante
    temp_evaporacao: Mapped[int] = mapped_column(Integer, nullable=False)
    delta_t: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)          # kcal/h
    consumo_kw: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)  # kW

    equipamento: Mapped["Equipamento"] = relationship(back_populates="performance")
