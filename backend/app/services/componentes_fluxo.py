from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.catalogo import Categoria
from app.models.componente import ComponenteTecnico, PerformanceComponente
from app.schemas.componente import ComponenteFluxoRequest, ComponenteSelecionado, ComponentesFluxoResponse

# Categorias selecionadas por interpolação linear em T.Evap (busca o ponto
# exato ou interpola entre os 2 pontos mais próximos do catálogo) + faixa de
# capacidade. Filtro Secador e Válvula Solenoide NÃO entram aqui — catálogo
# dessas 2 categorias em `componente_tecnico` está sempre vazio (0 linhas,
# conferido em produção): são selecionadas por algoritmo próprio (Kv pra
# solenoide, diâmetro de linha pro filtro — ver acessorios.py/solenoide.py),
# nunca por busca direta no banco. Tinham ficado nessa lista por engano —
# toda busca aqui retornava None e o motivo de aviso (abaixo) ia gerar
# alarme falso permanente pras duas, já que o catálogo delas nunca vai ter
# linha nenhuma por design.
#
# VET entrou aqui em 2026-09-11 (achado testando produção, cliente WEM
# Refrigeração): a versão antiga (`_buscar_por_temp_e_capacidade`, removida)
# só filtrava `temp_evaporacao <= T.Evap do projeto` sem interpolar — ou
# seja, "arredondava pra baixo" pro ponto de 5°C mais frio disponível no
# catálogo, subestimando a capacidade real de qualquer modelo sempre que o
# T.Evap do projeto não caía exatamente num múltiplo de 5°C. Isso podia
# excluir um corpo/orifício menor que na realidade cobriria a capacidade
# pedida, empurrando a seleção pra um modelo maior que o necessário.
_CATEGORIAS_POR_CAPACIDADE = [
    "Separador de Líquido",
    "Separador de Óleo",
    "Válvula de Expansão Termostática",
]


def _interpolar(t: float, t1: float, v1: float, t2: float, v2: float) -> float:
    """Interpolação linear entre dois pontos."""
    if t1 == t2:
        return v1
    return v1 + (t - t1) * (v2 - v1) / (t2 - t1)


# Hierarquia de corpos da VET Danfoss, por custo/padrão de mercado (confirmada
# com o usuário em 2026-09-17) — T2 é o corpo mais simples/barato; só escala
# pra TE5/TE12/TE20/TE55 quando o T2 (até o maior orifício, T2-6) não cobre
# mais a capacidade pedida. Sem isso, `_avaliar_menor_cap_max` (que já existia
# antes desta mudança) tratava a categoria inteira como um pool só e podia
# escolher um TE5 pequeno em vez de um T2 maior, só porque o teto interpolado
# do TE5 era numericamente menor — mesmo o T2 maior também cobrindo a
# capacidade pedida (achado real: 5.860 kcal/h a -6°C/R404A caía dentro tanto
# do T2-5 quanto do TE5-0.5; o algoritmo antigo escolhia o TE5-0.5 por ter
# teto menor, ignorando que ficar no T2 é mais barato quando ele já resolve).
_ORDEM_FAMILIA_VET = ["T2", "TE5", "TE12", "TE20", "TE55"]


def _familia_modelo(modelo: str) -> str:
    """'T2 - 5' → 'T2', 'TE5 - 0.5' → 'TE5' — prefixo antes do ' - ' já usado
    como separador em todo o catálogo de VET (corpo + orifício)."""
    return modelo.split(" - ")[0].strip()


def _avaliar_menor_cap_max(
    componentes,
    fluido: str,
    temp_evap: float,
    capacidade: float,
) -> tuple[ComponenteTecnico | None, float, float]:
    """
    Para cada modelo do grupo recebido:
      1. Encontra os dois pontos da tabela que cercam T.Evap do projeto
      2. Interpola cap_max e cap_min na T.Evap exata
      3. Verifica se capacidade_projeto está dentro da faixa interpolada

    Avalia TODOS os modelos do grupo (não para no primeiro que atender) e
    retorna o de menor cap_max_interp entre os que atendem — "menor
    equipamento que cobre a capacidade pedida" sem depender de
    `ComponenteTecnico.capacidade_nominal` estar preenchido/ordenado direito
    (nem todo catálogo populou esse campo — ex: VET, onde vale 0 em todos os
    22 modelos cadastrados).

    Retorna (componente, cap_max_interp, cap_min_interp) do menor modelo
    adequado dentro do grupo recebido — o chamador decide o que é "o grupo"
    (categoria inteira, ou só uma família de corpo, ver `_ORDEM_FAMILIA_VET`).
    """
    melhor: ComponenteTecnico | None = None
    melhor_cap_max: float | None = None
    melhor_cap_min = 0.0

    for comp in componentes:
        # Filtrar pontos do fluido solicitado, ordenados por T.Evap decrescente
        pontos = sorted(
            [p for p in comp.tabela_capacidade if p.fluido == fluido],
            key=lambda p: p.temp_evaporacao,
            reverse=True,
        )
        if not pontos:
            continue

        # Encontrar ponto acima e abaixo da T.Evap do projeto
        p_acima  = None
        p_abaixo = None
        for p in pontos:
            if p.temp_evaporacao >= temp_evap:
                p_acima = p
            if p.temp_evaporacao <= temp_evap:
                p_abaixo = p
                break

        # Calcular capacidades interpoladas
        if p_acima and p_acima.temp_evaporacao == temp_evap:
            # Ponto exato na tabela
            cap_max_i = float(p_acima.capacidade_kcalh)
            cap_min_i = float(p_acima.capacidade_min_kcalh)

        elif p_acima and p_abaixo:
            # Interpolação linear entre os dois pontos
            t1, t2 = float(p_acima.temp_evaporacao), float(p_abaixo.temp_evaporacao)
            cap_max_i = _interpolar(
                temp_evap, t1, float(p_acima.capacidade_kcalh),
                t2, float(p_abaixo.capacidade_kcalh)
            )
            cap_min_i = _interpolar(
                temp_evap, t1, float(p_acima.capacidade_min_kcalh),
                t2, float(p_abaixo.capacidade_min_kcalh)
            )

        elif p_abaixo:
            # T.Evap acima do maior ponto da tabela → usa o maior ponto
            cap_max_i = float(p_abaixo.capacidade_kcalh)
            cap_min_i = float(p_abaixo.capacidade_min_kcalh)

        else:
            continue

        # Verificar se a capacidade do projeto está na faixa, e se é o menor
        # equipamento adequado encontrado até agora entre todos os modelos
        if cap_min_i <= capacidade <= cap_max_i:
            if melhor_cap_max is None or cap_max_i < melhor_cap_max:
                melhor, melhor_cap_max, melhor_cap_min = comp, cap_max_i, cap_min_i

    return melhor, (melhor_cap_max or 0.0), melhor_cap_min


async def _buscar_por_capacidade_interpolado(
    db: AsyncSession,
    cat_nome: str,
    fluido: str,
    temp_evap: float,
    capacidade: float,
    ordem_familia: list[str] | None = None,
) -> tuple[ComponenteTecnico | None, float, float]:
    """
    Seleciona componente por interpolação linear na T.Evap do projeto (ver
    `_avaliar_menor_cap_max` pra lógica de interpolação por modelo).

    Sem `ordem_familia` (Separadores): avalia a categoria inteira como um
    pool só, mesmo comportamento de sempre.

    Com `ordem_familia` (VET): tenta esgotar cada família nessa ordem —
    "T2" primeiro, só passa pra próxima família da lista quando a família
    atual não tem NENHUM modelo que cubra a capacidade pedida. Evita trocar
    de corpo de válvula (mais caro) quando o corpo mais simples ainda resolve.
    """
    # Carregar todos os pontos da categoria agrupados por componente
    stmt = (
        select(ComponenteTecnico)
        .join(ComponenteTecnico.categoria)
        .join(ComponenteTecnico.fabricante)
        .where(Categoria.nome == cat_nome)
        .options(
            selectinload(ComponenteTecnico.tabela_capacidade),
            selectinload(ComponenteTecnico.categoria),
            selectinload(ComponenteTecnico.fabricante),
        )
    )
    result = await db.execute(stmt)
    componentes = result.scalars().unique().all()

    if not ordem_familia:
        return _avaliar_menor_cap_max(componentes, fluido, temp_evap, capacidade)

    for familia in ordem_familia:
        grupo = [c for c in componentes if _familia_modelo(c.modelo) == familia]
        if not grupo:
            continue
        comp, cap_max_i, cap_min_i = _avaliar_menor_cap_max(grupo, fluido, temp_evap, capacidade)
        if comp:
            return comp, cap_max_i, cap_min_i

    return None, 0.0, 0.0


async def _maior_capacidade_cadastrada(db: AsyncSession, cat_nome: str, fluido: str) -> float | None:
    """Maior capacidade_kcalh cadastrada pra essa categoria+fluido, sem
    filtro de T.Evap — usado só pra compor uma mensagem de aviso mais útil
    (quanto falta pro maior modelo do catálogo), não pra seleção em si."""
    stmt = (
        select(PerformanceComponente.capacidade_kcalh)
        .join(PerformanceComponente.componente)
        .join(ComponenteTecnico.categoria)
        .where(Categoria.nome == cat_nome, PerformanceComponente.fluido == fluido)
        .order_by(PerformanceComponente.capacidade_kcalh.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    valor = result.scalar_one_or_none()
    return float(valor) if valor is not None else None


async def _aviso_sem_match(db: AsyncSession, cat_nome: str, req: ComponenteFluxoRequest) -> str:
    maior = await _maior_capacidade_cadastrada(db, cat_nome, req.fluido)
    base = (
        f"{cat_nome}: nenhum modelo do catálogo cobre {req.capacidade_kcalh:.0f} kcal/h "
        f"em {req.fluido} a {req.temp_evap:.0f}°C."
    )
    if maior is not None:
        return base + f" Maior capacidade cadastrada nesse fluido: {maior:.0f} kcal/h."
    return base + " Nenhum modelo cadastrado nesse fluido."


async def selecionar_componentes_fluxo(
    req: ComponenteFluxoRequest, db: AsyncSession
) -> ComponentesFluxoResponse:
    selecionados: list[ComponenteSelecionado] = []
    avisos: list[str] = []

    for cat_nome in _CATEGORIAS_POR_CAPACIDADE:
        ordem_familia = _ORDEM_FAMILIA_VET if cat_nome == "Válvula de Expansão Termostática" else None
        comp, cap_max_i, cap_min_i = await _buscar_por_capacidade_interpolado(
            db, cat_nome, req.fluido, req.temp_evap, req.capacidade_kcalh, ordem_familia
        )
        if comp:
            selecionados.append(ComponenteSelecionado(
                categoria=cat_nome,
                modelo=comp.modelo,
                codigo_fabricante=comp.codigo_fabricante,
                fabricante=comp.fabricante.nome,
                conexao_entrada=comp.conexao_entrada,
                custo=float(comp.custo),
                faixa_operacao=(
                    f"{cap_min_i:.0f} a {cap_max_i:.0f} kcal/h "
                    f"@ {req.temp_evap:.0f}°C (interpolado)"
                ),
            ))
        else:
            avisos.append(await _aviso_sem_match(db, cat_nome, req))

    return ComponentesFluxoResponse(selecionados=selecionados, avisos=avisos)
