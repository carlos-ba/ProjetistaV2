from decimal import Decimal
from typing import List

from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Equipamento(Base):
    __tablename__ = "equipamento"
    __table_args__ = (
        # Achado na evolução do modelo pra suportar AC/EC (mesmo modelo físico,
        # capacidade/consumo diferentes — catálogo Mipal Hd/Hdl400 Pro): antes
        # não existia constraint real no banco, só a checagem do importador.
        # tipo_motor entra na identidade porque fabricante que só tem 1 tipo
        # de motor grava NULL — e 2 NULLs não colidem em UNIQUE (comportamento
        # padrão do Postgres), então segue funcionando pros catálogos antigos.
        UniqueConstraint(
            "modelo", "fabricante_id", "categoria_id", "tipo_motor",
            name="uq_equipamento_modelo_fabricante_categoria_motor"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    unidade_medida_id: Mapped[int] = mapped_column(ForeignKey("unidade_medida.id"), nullable=False)

    qtde_ventiladores: Mapped[int] = mapped_column(Integer, default=0)
    diametro_ventilador_mm: Mapped[int] = mapped_column(Integer, default=0)
    vazao_ar_m3h: Mapped[int] = mapped_column(Integer, default=0)
    flecha_ar_m: Mapped[int] = mapped_column(Integer, default=0)

    # Dados físicos para estimativa de carga de fluido
    volume_interno_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    conexao_liquido:   Mapped[str | None]     = mapped_column(String(10),    nullable=True)
    conexao_succao:    Mapped[str | None]     = mapped_column(String(10),    nullable=True)

    # AC = ventilador de velocidade fixa, EC = eletrônico de velocidade
    # variável — capacidade/vazão/consumo diferem entre os dois mesmo pro
    # mesmo modelo físico. NULL = fabricante que só publica 1 tipo de motor
    # (não se aplica a distinção).
    tipo_motor: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Cotas mínimas pra viabilizar, numa versão futura, checar se o
    # equipamento cabe na câmara (comparando com as dimensões internas já
    # calculadas no Card 1) — de propósito só a "caixa envolvente", sem as
    # cotas internas de fixação (só interessam pra quem desenha/instala).
    comprimento_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    altura_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profundidade_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    peso_liquido_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    ruido_dba: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Carga de refrigerante já publicada pronta pelo fabricante (kg) — quando
    # presente, preferida à estimativa por volume que o serviço de carga de
    # fluido já faz hoje a partir de volume_interno_kg. Campo novo e
    # independente de propósito, pra não mexer em cadastro antigo que já usa
    # volume_interno_kg do jeito que está.
    carga_refrigerante_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)

    biblioteca_tecnica_id: Mapped[int | None] = mapped_column(
        ForeignKey("biblioteca_tecnica.id"), nullable=True
    )

    # Achado no catálogo Bitzer Combat/Combat+/BIG CDU — dados de compressor
    # de unidade condensadora, sem análogo em evaporador. Só informativo por
    # ora (nenhum Card consome ainda), mesmo padrão do peso/ruído do Mipal.
    volume_deslocado_m3h: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    potencia_nominal_hp: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    motor_ventilador_corrente_a: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    motor_ventilador_potencia_w: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    # Texto livre de propósito — o formato varia demais entre modelos (faixa
    # de tensão + faixa de potência, às vezes com marca "PTC") pra estruturar
    # em campos numéricos sem perder informação, e nenhum Card lê isso hoje.
    capacitor_marcha_especificacao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resistencia_carter_especificacao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tanque_liquido_l: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    categoria: Mapped["Categoria"] = relationship(back_populates="equipamentos")
    fabricante: Mapped["Fabricante"] = relationship(back_populates="equipamentos")
    unidade_medida: Mapped["UnidadeMedida"] = relationship(back_populates="equipamentos")
    biblioteca_tecnica: Mapped["BibliotecaTecnica | None"] = relationship()
    performance: Mapped[List["PerformanceEquipamento"]] = relationship(
        back_populates="equipamento", cascade="all, delete-orphan"
    )
    variantes_eletricas: Mapped[List["EquipamentoVarianteEletrica"]] = relationship(
        back_populates="equipamento", cascade="all, delete-orphan"
    )
    resistencias_degelo: Mapped[List["EquipamentoResistenciaDegelo"]] = relationship(
        back_populates="equipamento", cascade="all, delete-orphan"
    )


class PerformanceEquipamento(Base):
    __tablename__ = "performance_equipamento"
    __table_args__ = (
        UniqueConstraint(
            "equipamento_id", "fluido", "temp_ambiente", "temp_evaporacao", "delta_t",
            name="uq_performance_equipamento"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False)
    fluido: Mapped[str] = mapped_column(String(20), nullable=False)
    temp_ambiente: Mapped[int] = mapped_column(Integer, default=32)   # °C — T.Amb do catálogo do fabricante
    temp_evaporacao: Mapped[int] = mapped_column(Integer, nullable=False)
    delta_t: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)          # kcal/h
    consumo_kw: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)  # kW

    # Quando true, `fluido` acima guarda o fluido de referência publicado
    # pelo fabricante (ex: "R22") e `capacidade` é o valor bruto naquele
    # fluido — o valor real pro fluido pedido é calculado aplicando
    # fator_correcao_fluido na leitura, não gravado aqui de novo por fluido
    # (catálogo Mipal: capacidade só é medida em R-22, os demais fluidos são
    # o mesmo valor × um fator do fabricante, não uma medição própria).
    usa_fator_correcao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    equipamento: Mapped["Equipamento"] = relationship(back_populates="performance")


class FatorCorrecaoFluido(Base):
    """Fator multiplicador de capacidade por fluido, publicado por alguns
    fabricantes em vez de medir cada fluido separadamente (ex: Mipal publica
    só em R-22 + tabela de fatores). Por fabricante porque a referência e os
    fatores variam de catálogo pra catálogo — não é universal."""

    __tablename__ = "fator_correcao_fluido"
    __table_args__ = (
        UniqueConstraint("fabricante_id", "fluido_base", "fluido", name="uq_fator_correcao_fluido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    fluido_base: Mapped[str] = mapped_column(String(20), nullable=False)   # fluido em que o catálogo publica (ex: "R22")
    fluido: Mapped[str] = mapped_column(String(20), nullable=False)        # fluido alvo do fator (ex: "R404A")
    fator: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    fabricante: Mapped["Fabricante"] = relationship()


class EquipamentoVarianteEletrica(Base):
    """1 linha por combinação de tensão/fase/frequência de um equipamento —
    vazão de ar e consumo variam por combinação (achado no catálogo Mipal:
    motor AC tem até 7 combinações distintas de tensão×frequência)."""

    __tablename__ = "equipamento_variante_eletrica"
    __table_args__ = (
        UniqueConstraint(
            "equipamento_id", "tensao", "fase", "frequencia_hz",
            name="uq_equipamento_variante_eletrica"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False)
    tensao: Mapped[str] = mapped_column(String(20), nullable=False)        # ex: "220V", "230V/380V"
    fase: Mapped[int] = mapped_column(Integer, nullable=False)             # 1 ou 3
    # Nullable de propósito: motor EC (eletrônico) não depende de frequência
    # — o catálogo publica um valor só, sem separar 50Hz/60Hz como o AC.
    frequencia_hz: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vazao_ar_m3h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    potencia_w: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    corrente_a: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Achado no catálogo Bitzer: aqui a "variante elétrica" é o compressor da
    # unidade condensadora, não um motor de ventilador — código de fabricante
    # muda por tensão (SKU próprio pra 220V vs 380V do mesmo modelo físico,
    # 1ª vez que o catálogo técnico precisa disso pra qualquer fabricante) e
    # LRA (corrente de partida/rotor bloqueado) fica ao lado do corrente_a
    # (FLA) já existente. vazao_ar_m3h/potencia_w ficam NULL nessas linhas —
    # são do ventilador, não do compressor.
    codigo_fabricante: Mapped[str | None] = mapped_column(String(30), nullable=True)
    corrente_partida_a: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    equipamento: Mapped["Equipamento"] = relationship(back_populates="variantes_eletricas")


class EquipamentoResistenciaDegelo(Base):
    """Especificação elétrica da resistência de degelo, por tensão —
    ligada ao equipamento porque o dimensionamento dela acompanha o nº de
    ventiladores/tamanho do modelo, não é um item de catálogo à parte."""

    __tablename__ = "equipamento_resistencia_degelo"
    __table_args__ = (
        UniqueConstraint("equipamento_id", "tensao", name="uq_equipamento_resistencia_degelo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="CASCADE"), nullable=False)
    tensao: Mapped[str] = mapped_column(String(20), nullable=False)        # ex: "3~220V", "3~440V"
    potencia_individual_w: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    corrente_a: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    consumo_nao_equilibrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    equipamento: Mapped["Equipamento"] = relationship(back_populates="resistencias_degelo")


class BibliotecaTecnica(Base):
    """Referência a um documento técnico externo (catálogo PDF do
    fabricante) — genérica de propósito, não amarrada a evaporador, pra
    servir painel/UC/porta no futuro sem precisar de tabela nova. Sem upload
    nenhum: só um link pra onde o arquivo já mora (ex: Google Drive) — o
    projeto não tem infra de upload/armazenamento de arquivo hoje, e o banco
    de produção não tem espaço sobrando pra guardar PDF como BLOB."""

    __tablename__ = "biblioteca_tecnica"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[int] = mapped_column(ForeignKey("fabricante.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)       # ex: "Mipal HD/HDL400 Pro"
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # preenchido depois
    observacao: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    fabricante: Mapped["Fabricante"] = relationship()
