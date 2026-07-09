from typing import List

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BlocoOrcamento(Base):
    """Nível 1 — bloco de apresentação/financeiro do orçamento."""
    __tablename__ = "bloco_orcamento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    classificacoes: Mapped[List["ClassificacaoItem"]] = relationship(
        back_populates="bloco", cascade="all, delete-orphan"
    )


class ClassificacaoItem(Base):
    """Nível 2 — classificação do item; aponta para um bloco."""
    __tablename__ = "classificacao_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    bloco_id: Mapped[int] = mapped_column(
        ForeignKey("bloco_orcamento.id", ondelete="CASCADE"), nullable=False
    )
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    bloco: Mapped["BlocoOrcamento"] = relationship(back_populates="classificacoes")
    itens: Mapped[List["ItemClassificacao"]] = relationship(
        back_populates="classificacao", cascade="all, delete-orphan"
    )


class ItemClassificacao(Base):
    """De-para: tipo_item (slug estável emitido pelos geradores) → classificação."""
    __tablename__ = "item_classificacao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo_item: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    classificacao_id: Mapped[int] = mapped_column(
        ForeignKey("classificacao_item.id", ondelete="CASCADE"), nullable=False
    )

    classificacao: Mapped["ClassificacaoItem"] = relationship(back_populates="itens")
