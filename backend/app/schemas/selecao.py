from pydantic import BaseModel


class SelecaoRequest(BaseModel):
    carga_termica_total: float
    temp_evaporacao: float = -10.0
    temp_ambiente: float = 32.0    # T.Amb do projeto — usado para filtrar o catálogo
    fluido: str = "R22"
    tipo: str = "Unidade Condensadora"


class EquipamentoSelecionado(BaseModel):
    id: int
    modelo: str
    fabricante: str
    capacidade_real: float
    vazao_ar: int
    preco: float
    diferenca: float
    percentual: float
    status: str
    volume_interno_kg: float | None = None
    conexao_liquido:   str   | None = None
    conexao_succao:    str   | None = None
    consumo_kw: float | None = None
    # Corrente de trabalho (A): campo ainda não existe no cadastro (Equipamento/
    # PerformanceEquipamento) — sempre None por enquanto. Deixado no schema pra o
    # card do frontend já saber exibir assim que o cadastro/importador ganhar essa
    # coluna e o service passar a preenchê-la.
    corrente_a: float | None = None
