from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PerfilMetalico(Base):
    __tablename__ = "perfil_metalico"
    __table_args__ = (
        UniqueConstraint("fabricante_id", "codigo_fabricante", name="uq_perfil_metalico_fabricante_codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    codigo_fabricante: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # Ângulo Interno, Ângulo Externo, Liso, U, Z

    # Genéricas, preenchidas conforme o tipo: Liso usa só medida_1 (largura);
    # Ângulo (Interno/Externo) usa medida_1/medida_2 (aba1/aba2); U e Z usam
    # as três (aba1/alma-ou-aba2/aba3).
    medida_1_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    medida_2_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    medida_3_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    comprimento_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao_original: Mapped[str] = mapped_column(String(200), nullable=False)

    fabricante: Mapped["Fabricante"] = relationship()
