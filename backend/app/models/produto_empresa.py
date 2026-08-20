from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ProdutoEmpresa(Base, TimestampMixin):
    __tablename__ = "produto_empresa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    descricao: Mapped[str] = mapped_column(String(250), nullable=False)
    codigo_interno: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unidade: Mapped[str] = mapped_column(String(10), default="un", server_default="un")
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # 'material' | 'equipamento' — qual tabela ref_global referencia, quando setado.
    # Metadado pra UI de busca no catálogo global — o casamento de preço em si é por
    # descrição normalizada (app/core/matching.py), não por ref_global.
    tipo_catalogo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ref_global: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
