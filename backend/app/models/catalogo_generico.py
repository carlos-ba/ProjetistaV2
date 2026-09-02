from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CatalogoGenerico(Base):
    """Cadastro genérico pra itens simples — sempre o mesmo produto, só varia
    fabricante/embalagem, sem seleção por especificação (mesmo conceito de
    selante_montagem/rebite/parafuso_bucha, que continuam em tabelas próprias
    por já existirem antes desta). Pensado pra não abrir uma tabela nova a
    cada novo item descoberto (1ª leva foi o kit de montagem, 2ª a barreira
    de vapor — ver DESIGN_DESMEMBRAR_BARREIRA_VAPOR_2026-09-02.md).

    Busca padrão: `WHERE tipo_item = '...' AND ativo ORDER BY id LIMIT 1`."""

    __tablename__ = "catalogo_generico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo_item: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    codigo_fabricante: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_embalagem: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    fabricante: Mapped["Fabricante"] = relationship()
