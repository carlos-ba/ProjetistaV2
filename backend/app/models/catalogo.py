from decimal import Decimal
from typing import List

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    equipamentos: Mapped[List["Equipamento"]] = relationship(back_populates="categoria")
    materiais: Mapped[List["Material"]] = relationship(back_populates="categoria")
    componentes: Mapped[List["ComponenteTecnico"]] = relationship(back_populates="categoria")


class Fabricante(Base):
    __tablename__ = "fabricante"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    equipamentos: Mapped[List["Equipamento"]] = relationship(back_populates="fabricante")
    materiais: Mapped[List["Material"]] = relationship(back_populates="fabricante")
    componentes: Mapped[List["ComponenteTecnico"]] = relationship(back_populates="fabricante")


class UnidadeMedida(Base):
    __tablename__ = "unidade_medida"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    sigla: Mapped[str] = mapped_column(String(10), nullable=False)

    equipamentos: Mapped[List["Equipamento"]] = relationship(back_populates="unidade_medida")
    materiais: Mapped[List["Material"]] = relationship(back_populates="unidade_medida")


class TipoProdutoTermico(Base):
    __tablename__ = "tipo_produto_termico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    perfis: Mapped[List["PerfilProdutoTermico"]] = relationship(back_populates="tipo")


class PerfilProdutoTermico(Base):
    __tablename__ = "perfil_produto_termico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipo_produto_termico.id"), nullable=False)

    ponto_congelamento: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    calor_especifico_acima_congelamento: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    calor_latente_congelamento: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    calor_especifico_abaixo_congelamento: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    taxa_respiracao: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    temperatura_conservacao: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    umidade_relativa: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    teor_agua: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    tipo: Mapped["TipoProdutoTermico"] = relationship(back_populates="perfis")
