from pydantic import BaseModel


class EmbalagemFluido(BaseModel):
    id: int
    fluido: str
    peso_kg: float

    class Config:
        from_attributes = True
