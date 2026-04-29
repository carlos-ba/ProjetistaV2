from decimal import Decimal
from typing import Any

from sqlalchemy import String, Numeric, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Material(Base):
    __tablename__ = "material"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    fabricante_id: Mapped[int | None] = mapped_column(ForeignKey("fabricante.id"), nullable=True)
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unidade_medida_id: Mapped[int] = mapped_column(ForeignKey("unidade_medida.id"), nullable=False)
    diametro_conexao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacidade_nominal: Mapped[float] = mapped_column(Float, default=0)
    detalhes_tecnicos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    categoria: Mapped["Categoria"] = relationship(back_populates="materiais")
    fabricante: Mapped["Fabricante | None"] = relationship(back_populates="materiais")
    unidade_medida: Mapped["UnidadeMedida"] = relationship(back_populates="materiais")
