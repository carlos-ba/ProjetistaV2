from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SelanteMontagem(Base):
    """Selante de PU (Sikaflex ou equivalente) — sempre o mesmo produto (400ml),
    só varia fabricante/embalagem. Sem seleção por especificação."""

    __tablename__ = "selante_montagem"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    codigo_fabricante: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_embalagem: Mapped[str] = mapped_column(String(20), nullable=False)  # "aplicador" | "salsicha"

    fabricante: Mapped["Fabricante"] = relationship()


class Rebite(Base):
    __tablename__ = "rebite"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    codigo_fabricante: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)

    fabricante: Mapped["Fabricante"] = relationship()


class ParafusoBucha(Base):
    """Conjunto parafuso+bucha — rastreado como 1 item só (sempre usados em par)."""

    __tablename__ = "parafuso_bucha"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    codigo_fabricante: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)

    fabricante: Mapped["Fabricante"] = relationship()
