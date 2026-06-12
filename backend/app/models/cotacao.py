from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Numeric, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Fornecedor(Base, TimestampMixin):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(18), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contato: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    cotacoes: Mapped[List["Cotacao"]] = relationship(back_populates="fornecedor")


class Cotacao(Base, TimestampMixin):
    __tablename__ = "cotacao"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedor.id"), nullable=False
    )
    projeto_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("projeto.id", ondelete="SET NULL"), nullable=True
    )
    nome_projeto: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # rascunho | enviada | recebida | processada | cancelada
    status: Mapped[str] = mapped_column(String(20), default="rascunho")
    validade_dias: Mapped[int] = mapped_column(Integer, default=30)
    data_recebimento: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fornecedor: Mapped["Fornecedor"] = relationship(back_populates="cotacoes")
    itens: Mapped[List["CotacaoItem"]] = relationship(
        back_populates="cotacao", cascade="all, delete-orphan"
    )


class CotacaoItem(Base):
    __tablename__ = "cotacao_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cotacao_id: Mapped[UUID] = mapped_column(
        ForeignKey("cotacao.id", ondelete="CASCADE"), nullable=False
    )

    # O que foi pedido (snapshot — não depende do catálogo)
    tipo_item: Mapped[str] = mapped_column(String(30), nullable=False)   # Equipamento | Material | Componente | Painel | Porta...
    ref_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # id na tabela de origem
    descricao: Mapped[str] = mapped_column(String(250), nullable=False)
    detalhe: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    qtde: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=1)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False, default="un")

    # O que o fornecedor devolveu (preenchido na importação — Fase 2)
    preco_unitario: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    marca_modelo_cotado: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    prazo_entrega_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    obs_fornecedor: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    cotacao: Mapped["Cotacao"] = relationship(back_populates="itens")
