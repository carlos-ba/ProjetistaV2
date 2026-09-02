from pydantic import BaseModel, Field


class PerfilManualItem(BaseModel):
    """Perfil metálico extra escolhido manualmente (Liso, Z, ou variação fora do
    padrão de 40mm) — entra nos cálculos de selante/rebite/parafuso+bucha junto
    com os perfis da seleção automática."""
    perfil_id: int
    quantidade_barras: int = Field(gt=0)


class GabineteRequest(BaseModel):
    comprimento: float
    largura: float
    altura: float
    largura_painel: float
    espessura_mm: float = 100.0
    nucleo: str = "PUR"
    tipo_piso: str = "nenhum"
    espessura_concreto_cm: float = 0.0
    piso_rebaixado: bool = False   # convencional rebaixado (nivelado, sem degrau)
    # Kit de montagem (Configurações → perfil de montagem ativo)
    largura_aba_padrao_mm: int = Field(40, gt=0)
    rendimento_selante_m_por_embalagem: float = Field(12.0, gt=0)
    fator_seguranca_selante: float = Field(0.10, ge=0)
    perfis_manuais: list[PerfilManualItem] = []


class GabineteDXFRequest(BaseModel):
    """Payload do botão 'Baixar Projeto CAD (.DXF)' do Card 1 (dimensões em metros)."""
    comprimento: float
    largura: float
    altura: float
    largura_painel: float = 1.1
    espessura: float = 100.0   # mm


class ItemCorte(BaseModel):
    item: str
    quantidade: int
    comprimento: float
    area_total: float
    descricao: str
    tipo_item: str | None = None


class MaterialExtra(BaseModel):
    item: str
    qtd: str  # texto pronto pra exibição inline (ex: "126.89 m²") — usado na prévia do Card 1
    quantidade: float  # valor numérico puro, pra planilhas/orçamento (colunas separadas)
    unidade: str
    detalhe: str
    tipo_item: str | None = None


class GabineteResponse(BaseModel):
    lista_corte: list[ItemCorte]
    materiais_extras: list[MaterialExtra]
    nucleo_selecionado: str
    espessura_considerada: str
    altura_util_calculada: float
    perda_altura: float
    # Expostos pra alimentar o cálculo do kit de montagem (feito à parte, na
    # rota, por depender do banco) sem duplicar a geometria aqui.
    comp_parede_m: float = 0.0
    area_total_paineis_m2: float = 0.0
    # Idem, mas pra alimentar o cálculo da barreira de vapor (piso convencional) —
    # 0.0 quando o piso não é "convencional" (nesse caso a barreira não se aplica).
    area_piso_m2: float = 0.0
    # Avisos de catálogo faltando — agrega tanto o kit de montagem quanto a
    # barreira de vapor (mesmo mecanismo, mesmo banner no Card 1; ver CLAUDE.md).
    avisos_kit_montagem: list[str] = []
