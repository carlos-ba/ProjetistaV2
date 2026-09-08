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


class ComponentesFluxoResponse(BaseModel):
    selecionados: list[ComponenteSelecionado]
    # Categoria sem nenhum componente no catálogo que cubra a capacidade
    # pedida — achado testando com UC grande (Bitzer): sem isso, o item
    # some da lista em silêncio, sem indicar ao técnico que faltou cadastro
    # (mesmo padrão de avisos_kit_montagem do Card 1).
    avisos: list[str] = []
