from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.catalogo import PerfilProdutoTermico
from app.schemas.carga_termica import CargaTermicaRequest, CargaTermicaResponse

_K_VALUES = {"PUR": 0.022, "PIR": 0.023, "EPS": 0.038}
_H_INT = 8.7
_H_EXT = 23.0
_W_PARA_KCALH = 0.86
_KJ_PARA_KCAL = 1 / 4.184
_DENSIDADE_AR = 1.2
_ENTALPIA_EXTERNA = 85.0
_ENTALPIA_INTERNA = 9.0
_CALOR_PESSOA_KCALH = 250.0


def _trocas_ar(volume: float) -> float:
    if volume < 10: return 44.0
    if volume < 25: return 33.0
    if volume < 50: return 26.0
    if volume < 100: return 20.0
    if volume < 250: return 14.0
    if volume < 500: return 9.0
    return 7.0


async def calcular_carga_termica(req: CargaTermicaRequest, db: AsyncSession) -> CargaTermicaResponse:
    comp, larg, alt = req.comprimento, req.largura, req.altura
    k_iso = _K_VALUES.get(req.nucleo, 0.022)
    esp_m = req.espessura_painel_mm / 1000.0
    t_ext, t_int = req.temp_externa, req.temp_interna

    # Condução
    u = 1 / ((esp_m / k_iso) + (1 / _H_INT) + (1 / _H_EXT))
    area_paredes_teto = (comp * alt * 2) + (larg * alt * 2) + (comp * larg)
    q_paredes_teto = u * area_paredes_teto * (t_ext - t_int)

    area_piso = comp * larg
    if req.tipo_piso in ("painel", "convencional"):
        q_piso = u * area_piso * (t_ext - t_int)
    else:
        fator = 25.0 if t_int < -10 else 15.0
        q_piso = area_piso * fator

    q_cond = (q_paredes_teto + q_piso) * _W_PARA_KCALH

    # Infiltração
    q_inf = 0.0
    if req.calcular_infiltracao:
        vol = comp * larg * alt
        q_inf = (vol * _trocas_ar(vol) * _DENSIDADE_AR * (_ENTALPIA_EXTERNA - _ENTALPIA_INTERNA) * _KJ_PARA_KCAL) / 24.0

    # Produto
    q_prod, q_resp = 0.0, 0.0
    if req.id_produto and req.movimentacao_diaria_kg > 0:
        result = await db.execute(select(PerfilProdutoTermico).where(PerfilProdutoTermico.id == req.id_produto))
        perfil = result.scalar_one_or_none()
        if perfil:
            c1 = float(perfil.calor_especifico_acima_congelamento)
            c_lat = float(perfil.calor_latente_congelamento)
            c2 = float(perfil.calor_especifico_abaixo_congelamento)
            t_cong = float(perfil.ponto_congelamento)
            t_ent = req.temp_entrada_produto
            mov = req.movimentacao_diaria_kg

            q_kcal = 0.0
            if t_ent > t_cong:
                q_kcal += mov * c1 * (t_ent - t_cong)
            if t_ent > t_cong and t_int < t_cong:
                q_kcal += mov * c_lat
            if t_int < t_cong:
                ts = t_cong if t_ent > t_cong else t_ent
                q_kcal += mov * c2 * (ts - t_int)

            q_prod = q_kcal / req.tempo_resfriamento_h
            if perfil.taxa_respiracao and float(perfil.taxa_respiracao) > 0:
                q_resp = mov * float(perfil.taxa_respiracao) / 24.0

    # Cargas internas
    q_ilum = (req.potencia_iluminacao_w * _W_PARA_KCALH * req.horas_iluminacao_dia) / 24
    q_pess = (req.numero_pessoas * _CALOR_PESSOA_KCALH * req.horas_pessoas_dia) / 24
    q_moto = (req.potencia_outros_motores_w * _W_PARA_KCALH * req.horas_outros_motores_dia) / 24
    q_int = q_ilum + q_pess + q_moto

    total = q_cond + q_inf + q_prod + q_resp + q_int
    total_seg = total * (1 + req.fator_seguranca_perc / 100)
    capacidade = total_seg * (24.0 / req.horas_funcionamento_motor)

    return CargaTermicaResponse(
        carga_conducao_kcalh=round(q_cond, 2),
        info_construtiva=f"Núcleo: {req.nucleo} (k={k_iso}) | U={round(u, 4)} | Piso: {req.tipo_piso}",
        carga_infiltracao_kcalh=round(q_inf, 2),
        carga_produto_kcalh=round(q_prod, 2),
        carga_respiracao_kcalh=round(q_resp, 2),
        carga_iluminacao_kcalh=round(q_ilum, 2),
        carga_pessoas_kcalh=round(q_pess, 2),
        carga_motores_kcalh=round(q_moto, 2),
        carga_internas_total_kcalh=round(q_int, 2),
        carga_total_24h_kcalh=round(total, 2),
        carga_total_com_seguranca_kcalh=round(total_seg, 2),
        capacidade_requerida_equipamento_kcalh=round(capacidade, 2),
        fator_seguranca_aplicado=f"{req.fator_seguranca_perc}%",
        baseado_em_horas_funcionamento=req.horas_funcionamento_motor,
    )
