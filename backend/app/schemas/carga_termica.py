from pydantic import BaseModel


class CargaTermicaRequest(BaseModel):
    comprimento: float
    largura: float
    altura: float
    espessura_painel_mm: float
    nucleo: str = "PUR"
    temp_externa: float
    temp_interna: float
    tipo_piso: str = "painel"
    calcular_infiltracao: bool = True
    id_produto: int | None = None
    movimentacao_diaria_kg: float = 0.0
    temp_entrada_produto: float = 0.0
    tempo_resfriamento_h: float = 24.0
    potencia_iluminacao_w: float = 0.0
    horas_iluminacao_dia: float = 0.0
    numero_pessoas: int = 0
    horas_pessoas_dia: float = 0.0
    potencia_outros_motores_w: float = 0.0
    horas_outros_motores_dia: float = 0.0
    fator_seguranca_perc: float = 10.0
    horas_funcionamento_motor: float = 18.0


class CargaTermicaResponse(BaseModel):
    carga_conducao_kcalh: float
    info_construtiva: str
    carga_infiltracao_kcalh: float
    carga_produto_kcalh: float
    carga_respiracao_kcalh: float
    carga_iluminacao_kcalh: float
    carga_pessoas_kcalh: float
    carga_motores_kcalh: float
    carga_internas_total_kcalh: float
    carga_total_24h_kcalh: float
    carga_total_com_seguranca_kcalh: float
    capacidade_requerida_equipamento_kcalh: float
    fator_seguranca_aplicado: str
    baseado_em_horas_funcionamento: float
