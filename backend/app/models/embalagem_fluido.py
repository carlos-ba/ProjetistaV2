from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class EmbalagemFluido(Base):
    __tablename__ = "embalagem_fluido"

    id:       Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    fluido:   Mapped[str]   = mapped_column(String(20), nullable=False)
    peso_kg:  Mapped[float] = mapped_column(Float, nullable=False)
