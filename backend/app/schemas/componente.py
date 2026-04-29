from pydantic import BaseModel


class ComponenteFluxoRequest(BaseModel):
    capacidade_kcalh: float
    fluido: str = "R22"
    temp_evap: int = -10


class ComponenteSelecionado(BaseModel):
    categoria: str
    modelo: str
    codigo_fabricante: str | None
    fabricante: str
    conexao_entrada: str
    custo: float
    faixa_operacao: str
