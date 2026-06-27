from sqlalchemy import Column, Integer, String, Float
from app.models.base import Base


class PesoTuboCobre(Base):
    __tablename__ = "peso_tubo_cobre"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    bitola_pol    = Column(String(10), nullable=False, unique=True)
    diametro_mm   = Column(Float, nullable=False)
    parede_fina   = Column(Float, nullable=True)   # kg/m — 0.79mm (1/32")
    parede_grossa = Column(Float, nullable=True)   # kg/m — 1.59mm (1/16")
