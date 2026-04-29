from __future__ import annotations
import math
from app.schemas.gabinete import GabineteRequest, GabineteResponse, ItemCorte, MaterialExtra


def calcular_gabinete(req: GabineteRequest) -> GabineteResponse:
    esp_m = req.espessura_mm / 1000.0
    lista_corte: list[ItemCorte] = []
    materiais_extras: list[MaterialExtra] = []
    area_total_paineis = 0.0

    # Paredes
    dim_linear = (req.comprimento * 2) + ((req.largura - 2 * esp_m) * 2)
    qtde_parede = math.ceil(dim_linear / req.largura_painel)
    area_paredes = qtde_parede * req.altura * req.largura_painel
    area_total_paineis += area_paredes
    lista_corte.append(ItemCorte(
        item="Painéis de Parede",
        quantidade=int(qtde_parede),
        comprimento=req.altura,
        area_total=round(area_paredes, 2),
        descricao=f"Peças de {req.altura}m (Altura)",
    ))

    # Teto
    qtde_teto = math.ceil(req.comprimento / req.largura_painel)
    area_teto = qtde_teto * req.largura * req.largura_painel
    area_total_paineis += area_teto
    lista_corte.append(ItemCorte(
        item="Painéis de Teto",
        quantidade=int(qtde_teto),
        comprimento=req.largura,
        area_total=round(area_teto, 2),
        descricao=f"Peças de {req.largura}m (Largura)",
    ))

    # Piso
    altura_util = req.altura - esp_m
    if req.tipo_piso == "painel":
        qtde_piso = math.ceil(req.comprimento / req.largura_painel)
        area_piso_painel = qtde_piso * req.largura * req.largura_painel
        area_total_paineis += area_piso_painel
        lista_corte.append(ItemCorte(
            item="Painéis de Piso",
            quantidade=int(qtde_piso),
            comprimento=req.largura,
            area_total=round(area_piso_painel, 2),
            descricao=f"Peças de {req.largura}m (Largura)",
        ))
        altura_util -= esp_m
    elif req.tipo_piso == "convencional":
        area_piso = req.comprimento * req.largura
        esp_camada = req.espessura_mm / 2.0
        materiais_extras.append(MaterialExtra(
            item=f"Placas Isolamento ({req.nucleo})",
            qtd=f"{area_piso * 2:.2f} m²",
            detalhe=f"2 camadas de {esp_camada:.0f}mm (Juntas Desencontradas)",
        ))
        materiais_extras.append(MaterialExtra(
            item="Barreira de Vapor",
            qtd=f"{area_piso * 1.1:.2f} m²",
            detalhe="Sob isolamento (1 camada)",
        ))
        if req.espessura_concreto_cm > 0:
            vol = area_piso * (req.espessura_concreto_cm / 100)
            materiais_extras.append(MaterialExtra(
                item="Concreto Armado",
                qtd=f"{vol:.2f} m³",
                detalhe=f"Esp. {req.espessura_concreto_cm}cm",
            ))
            altura_util -= esp_m + (req.espessura_concreto_cm / 100)
        else:
            altura_util -= esp_m

    materiais_extras.append(MaterialExtra(
        item="Acessórios de Montagem (Kit)",
        qtd=f"{area_total_paineis:.2f} m²",
        detalhe="Silicone, Fixadores, Cantoneiras (Base: Área Total de Painéis)",
    ))

    return GabineteResponse(
        lista_corte=lista_corte,
        materiais_extras=materiais_extras,
        nucleo_selecionado=req.nucleo,
        espessura_considerada=f"{req.espessura_mm}mm",
        altura_util_calculada=round(altura_util, 3),
        perda_altura=round(req.altura - altura_util, 3),
    )
