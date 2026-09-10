from __future__ import annotations
import math
from app.schemas.gabinete import GabineteRequest, GabineteResponse, ItemCorte, MaterialExtra


def _dividir_por_autoportancia(vao: float, auto_portancia_mm: float | None) -> tuple[int, float]:
    """Divide um vão (largura do teto/piso) em pedaços iguais dentro da
    auto-portância do painel (vão máximo sem apoio, catálogo) — sem isso, uma
    câmara larga pediria uma peça única maior do que o painel suporta
    estruturalmente. Pedaços iguais, não pedaços do tamanho máximo da
    auto-portância + sobra (ex: vão 10m / auto-portância 7m → 2 peças de 5m,
    não 7m + 3m). Sem auto_portancia cadastrada, mantém 1 peça (comportamento
    anterior à esta regra)."""
    if not auto_portancia_mm:
        return 1, vao
    auto_portancia_m = auto_portancia_mm / 1000.0
    if vao <= auto_portancia_m:
        return 1, vao
    num_pecas = math.ceil(vao / auto_portancia_m)
    return num_pecas, round(vao / num_pecas, 3)


def calcular_gabinete(req: GabineteRequest) -> GabineteResponse:
    esp_m = req.espessura_mm / 1000.0             # espessura do painel (teto/piso)
    concreto_m = req.espessura_concreto_cm / 100.0
    lista_corte: list[ItemCorte] = []
    materiais_extras: list[MaterialExtra] = []
    area_total_paineis = 0.0

    # ── Comprimento da peça do painel de parede ────────────────────────────
    # O teto apoia sobre as paredes → sempre desconta a espessura do teto.
    # O que muda embaixo depende do piso:
    #   painel        → desconta também o piso em painel (parede fica entre teto e piso)
    #   convencional  → apoiado: só teto; rebaixado: teto − mas parede desce no rebaixo (+ isolamento + concreto)
    #   nenhum        → só teto
    rebaixo = esp_m + concreto_m                  # profundidade do rebaixo (isolamento do piso + concreto)
    if req.tipo_piso == "painel":
        comp_parede = req.altura - 2 * esp_m
    elif req.tipo_piso == "convencional" and req.piso_rebaixado:
        comp_parede = req.altura - esp_m + rebaixo
    else:  # convencional apoiado / nenhum
        comp_parede = req.altura - esp_m
    comp_parede = round(comp_parede, 3)

    # Paredes
    dim_linear = (req.comprimento * 2) + ((req.largura - 2 * esp_m) * 2)
    qtde_parede = math.ceil(dim_linear / req.largura_painel)
    area_paredes = qtde_parede * comp_parede * req.largura_painel
    area_total_paineis += area_paredes
    lista_corte.append(ItemCorte(
        item="Painéis de Parede",
        quantidade=int(qtde_parede),
        comprimento=comp_parede,
        area_total=round(area_paredes, 2),
        descricao=f"Peças de {comp_parede}m (comprimento do painel)",
        tipo_item="painel_parede",
    ))

    # Teto
    fileiras_teto = math.ceil(req.comprimento / req.largura_painel)
    num_pecas_teto, comp_peca_teto = _dividir_por_autoportancia(req.largura, req.auto_portancia_mm)
    qtde_teto = fileiras_teto * num_pecas_teto
    area_teto = qtde_teto * comp_peca_teto * req.largura_painel
    area_total_paineis += area_teto
    descricao_teto = (
        f"Peças de {comp_peca_teto}m (Largura)" if num_pecas_teto == 1
        else f"Peças de {comp_peca_teto}m ({num_pecas_teto}x por fileira — largura dividida pela auto-portância do painel)"
    )
    lista_corte.append(ItemCorte(
        item="Painéis de Teto",
        quantidade=int(qtde_teto),
        comprimento=comp_peca_teto,
        area_total=round(area_teto, 2),
        descricao=descricao_teto,
        tipo_item="painel_teto",
    ))

    # Piso
    altura_util = req.altura - esp_m
    area_piso = 0.0        # só "convencional" usa — alimenta a barreira de vapor (resolvida à parte, depende do banco)
    volume_concreto = 0.0  # idem — só informativo no Card 1, não é MaterialExtra (obra civil, não é peça de refrigeração)
    if req.tipo_piso == "painel":
        fileiras_piso = math.ceil(req.comprimento / req.largura_painel)
        num_pecas_piso, comp_peca_piso = _dividir_por_autoportancia(req.largura, req.auto_portancia_mm)
        qtde_piso = fileiras_piso * num_pecas_piso
        area_piso_painel = qtde_piso * comp_peca_piso * req.largura_painel
        area_total_paineis += area_piso_painel
        descricao_piso = (
            f"Peças de {comp_peca_piso}m (Largura)" if num_pecas_piso == 1
            else f"Peças de {comp_peca_piso}m ({num_pecas_piso}x por fileira — largura dividida pela auto-portância do painel)"
        )
        lista_corte.append(ItemCorte(
            item="Painéis de Piso",
            quantidade=int(qtde_piso),
            comprimento=comp_peca_piso,
            area_total=round(area_piso_painel, 2),
            descricao=descricao_piso,
            tipo_item="painel_piso",
        ))
        altura_util -= esp_m
    elif req.tipo_piso == "convencional":
        area_piso = req.comprimento * req.largura
        esp_camada = req.espessura_mm / 2.0
        materiais_extras.append(MaterialExtra(
            item=f"Placas Isolamento ({req.nucleo})",
            qtd=f"{area_piso * 2:.2f} m²",
            quantidade=round(area_piso * 2, 2),
            unidade="m²",
            detalhe=f"2 camadas de {esp_camada:.0f}mm (Juntas Desencontradas)",
            tipo_item="placa_isolamento",
        ))
        if req.espessura_concreto_cm > 0:
            volume_concreto = round(area_piso * concreto_m, 2)
        # Altura útil: apoiado desce pelo isolamento + concreto (cria degrau na porta);
        # rebaixado preenche o rebaixo e o piso fica nivelado (só desconta o teto).
        if not req.piso_rebaixado:
            altura_util -= esp_m + concreto_m

    return GabineteResponse(
        lista_corte=lista_corte,
        materiais_extras=materiais_extras,
        nucleo_selecionado=req.nucleo,
        espessura_considerada=f"{req.espessura_mm}mm",
        altura_util_calculada=round(altura_util, 3),
        perda_altura=round(req.altura - altura_util, 3),
        comp_parede_m=comp_parede,
        area_total_paineis_m2=round(area_total_paineis, 2),
        area_piso_m2=round(area_piso, 2),
        volume_concreto_m3=volume_concreto,
        linhas_sustentacao_perfil_t=max(num_pecas_teto - 1, 0),
    )
