from pydantic import BaseModel


class SelecaoRequest(BaseModel):
    carga_termica_total: float
    temp_evaporacao: float = -10.0
    temp_ambiente: float = 35.0    # T.Amb do projeto — variável mandatária; T.Cond = T.Amb+10 é derivada, nunca enviada
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
    carga_refrigerante_kg: float | None = None
    conexao_liquido:   str   | None = None
    conexao_succao:    str   | None = None
    consumo_kw: float | None = None
    # Corrente de trabalho (A): campo ainda não existe no cadastro (Equipamento/
    # PerformanceEquipamento) — sempre None por enquanto. Deixado no schema pra o
    # card do frontend já saber exibir assim que o cadastro/importador ganhar essa
    # coluna e o service passar a preenchê-la.
    corrente_a: float | None = None
    qtde_ventiladores: int | None = None
    # None pra fabricante que ainda não teve esse dado digitado no catálogo
    # (ex: Mipal Hd/Hdl400 Pro, 2026-09) — o frontend mostra "não informado"
    # em vez de esconder o campo, pronto pra quando o cadastro for completado.
    diametro_ventilador_mm: int | None = None
