from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ApelidoFornecedorItem(Base, TimestampMixin):
    """Apelido aprendido: como um fornecedor específico nomeia um item nosso.

    Alimentado pela confirmação humana no fluxo de importação de cotação em PDF
    (ver DESIGN_IMPORTACAO_PDF_COTACAO_2026-09-01.md) — não é busca semântica, é
    lookup direto por (fornecedor_id, termo_fornecedor) normalizado. A IA só
    entra pra resolver o "cold start" (termo nunca visto daquele fornecedor);
    uma vez confirmado, casa sozinho sem precisar de IA de novo.
    """

    __tablename__ = "apelido_fornecedor_item"
    __table_args__ = (
        UniqueConstraint("fornecedor_id", "termo_fornecedor", name="uq_apelido_fornecedor_termo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id", ondelete="CASCADE"), nullable=False)
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)

    # Termo normalizado (norm()) extraído da descrição do fornecedor — a chave do lookup
    termo_fornecedor: Mapped[str] = mapped_column(String(200), nullable=False)

    # Nosso item correspondente — ref_id quando existe (mais estável), descrição sempre
    # (fallback quando não há ref_id, ex: materiais extras do gabinete)
    nosso_ref_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nosso_tipo_item: Mapped[str] = mapped_column(String(30), nullable=False)
    nosso_descricao: Mapped[str] = mapped_column(String(250), nullable=False)
