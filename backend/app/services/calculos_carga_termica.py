from __future__ import annotations
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.catalogo import PerfilProdutoTermico
from app.schemas.carga_termica import CargaTermicaRequest, CargaTermicaResponse

_K_VALUES = {"PUR": 0.022, "PIR": 0.023, "EPS": 0.038}
_H_INT = 8.7           # W/(m²·K) — convecção interna
_H_EXT = 23.0          # W/(m²·K) — convecção externa (vento moderado)
_W_PARA_KCALH = 0.86   # 1 W = 0.86 kcal/h
_KJ_PARA_KCAL = 1 / 4.184   # 1 kJ = 1/4.184 kcal
_DENSIDADE_AR = 1.2    # kg/m³
_CALOR_PESSOA_KCALH = 250.0  # kcal/h por pessoa
_P_ATM = 101.325       # kPa — pressão atmosférica ao nível do mar

# Método simplificado — entalpias fixas (ASHRAE simplificado)
_ENTALPIA_EXT_SIMPL = 85.0   # kJ/kg (~35°C / 60% UR)
_ENTALPIA_INT_SIMPL = 9.0    # kJ/kg (~0°C)


def _trocas_ar(volume: float) -> float:
    """Número de trocas de ar por dia (tabela ASHRAE)."""
    if volume < 10:  return 44.0
    if volume < 25:  return 33.0
    if volume < 50:  return 26.0
    if volume < 100: return 20.0
    if volume < 250: return 14.0
    if volume < 500: return 9.0
    return 7.0


def _pressao_saturacao(t: float) -> float:
    """
    Pressão de saturação do vapor d'água em kPa — fórmula de Magnus.
    Válida de -40°C a +60°C (ASHRAE Fundamentals, Cap. 1).
    """
    return 0.6105 * math.exp(17.27 * t / (t + 237.3))


def _razao_umidade(t: float, ur: float) -> float:
    """
    Razão de umidade W em kg_água / kg_ar_seco (ASHRAE).
    ur em % (0–100).
    """
    pws = _pressao_saturacao(t)          # kPa
    pw  = (ur / 100.0) * pws             # pressão parcial do vapor
    pw  = min(pw, _P_ATM - 0.001)       # evita divisão por zero
    return 0.622 * pw / (_P_ATM - pw)


def _entalpia_ar_umido(t: float, ur: float) -> float:
    """
    Entalpia do ar úmido em kJ/kg_ar_seco (ASHRAE Fundamentals, Cap. 1).
    h = 1.006·T + W·(2501 + 1.86·T)
    """
    W = _razao_umidade(t, ur)
    return 1.006 * t + W * (2501.0 + 1.86 * t)


def _calcular_infiltracao(
    vol: float,
    metodo: str,
    t_ext: float, ur_ext: float,
    t_int: float, ur_int: float,
) -> tuple[float, str]:
    """
    Retorna (q_inf_kcalh, info_texto).

    Método simplificado  → entalpias fixas (ASHRAE tabela)
    Método psicrométrico → entalpias calculadas pela temperatura e UR reais
    """
    trocas = _trocas_ar(vol)

    if metodo == "psicrometrico":
        h_ext = _entalpia_ar_umido(t_ext, ur_ext)
        h_int = _entalpia_ar_umido(t_int, ur_int)
        metodo_label = "Psicrométrico"
    else:
        h_ext = _ENTALPIA_EXT_SIMPL
        h_int = _ENTALPIA_INT_SIMPL
        metodo_label = "Simplificado"

    delta_h = max(h_ext - h_int, 0.0)   # kJ/kg
    # q = V × trocas/dia × ρ × Δh (kJ/kg) × (kcal/kJ) / 24h → kcal/h
    q_inf = (vol * trocas * _DENSIDADE_AR * delta_h * _KJ_PARA_KCAL) / 24.0

    info = (
        f"Infiltração [{metodo_label}] | "
        f"Trocas: {trocas:.0f}/dia | "
        f"h_ext={h_ext:.1f} kJ/kg | "
        f"h_int={h_int:.1f} kJ/kg | "
        f"Δh={delta_h:.1f} kJ/kg"
    )
    return q_inf, info


async def calcular_carga_termica(req: CargaTermicaRequest, db: AsyncSession) -> CargaTermicaResponse:
    comp, larg, alt = req.comprimento, req.largura, req.altura
    k_iso = _K_VALUES.get(req.nucleo, 0.022)
    esp_m = req.espessura_painel_mm / 1000.0
    t_ext, t_int = req.temp_externa, req.temp_interna

    # ── Condução ──────────────────────────────────────────────────────────
    u = 1 / ((esp_m / k_iso) + (1 / _H_INT) + (1 / _H_EXT))   # W/(m²·K)
    area_paredes_teto = (comp * alt * 2) + (larg * alt * 2) + (comp * larg)
    q_paredes_teto = u * area_paredes_teto * (t_ext - t_int)    # W

    area_piso = comp * larg
    if req.tipo_piso in ("painel", "convencional"):
        q_piso = u * area_piso * (t_ext - t_int)
    else:
        fator = 25.0 if t_int < -10 else 15.0
        q_piso = area_piso * fator

    q_cond = (q_paredes_teto + q_piso) * _W_PARA_KCALH          # kcal/h

    # ── Infiltração ───────────────────────────────────────────────────────
    q_inf = 0.0
    info_inf = "Infiltração não calculada"
    if req.calcular_infiltracao:
        vol = comp * larg * alt
        q_inf, info_inf = _calcular_infiltracao(
            vol,
            req.metodo_infiltracao,
            t_ext, req.ur_externa,
            t_int, req.ur_interna,
        )

    # ── Produto ──────────────────────────────────────────────────────────
    # Unidades ASHRAE (banco):
    #   c1, c2  → kJ/(kg·K)  → converter com _KJ_PARA_KCAL
    #   c_lat   → kJ/kg      → converter com _KJ_PARA_KCAL
    #   taxa_respiracao → W/tonne → (mov/1000) × taxa × _W_PARA_KCALH
    q_prod, q_resp = 0.0, 0.0
    if req.id_produto and req.movimentacao_diaria_kg > 0:
        result = await db.execute(
            select(PerfilProdutoTermico).where(PerfilProdutoTermico.id == req.id_produto)
        )
        perfil = result.scalar_one_or_none()
        if perfil:
            c1    = float(perfil.calor_especifico_acima_congelamento)   # kJ/(kg·K)
            c_lat = float(perfil.calor_latente_congelamento)             # kJ/kg
            c2    = float(perfil.calor_especifico_abaixo_congelamento)  # kJ/(kg·K)
            t_cong = float(perfil.ponto_congelamento)
            t_ent  = req.temp_entrada_produto
            mov    = req.movimentacao_diaria_kg

            q_kj = 0.0
            if t_ent > t_cong:
                q_kj += mov * c1 * (t_ent - t_cong)    # kg × kJ/(kg·K) × K = kJ
            if t_ent > t_cong and t_int < t_cong:
                q_kj += mov * c_lat                     # kg × kJ/kg = kJ
            if t_int < t_cong:
                ts = t_cong if t_ent > t_cong else t_ent
                q_kj += mov * c2 * (ts - t_int)         # kg × kJ/(kg·K) × K = kJ

            # kJ → kcal / horas de resfriamento = kcal/h
            q_prod = (q_kj * _KJ_PARA_KCAL) / req.tempo_resfriamento_h

            # Respiração: W/tonne → kcal/h
            if perfil.taxa_respiracao and float(perfil.taxa_respiracao) > 0:
                q_resp = (mov / 1000.0) * float(perfil.taxa_respiracao) * _W_PARA_KCALH

    # ── Cargas internas ───────────────────────────────────────────────────
    q_ilum = (req.potencia_iluminacao_w * _W_PARA_KCALH * req.horas_iluminacao_dia) / 24
    q_pess = (req.numero_pessoas * _CALOR_PESSOA_KCALH * req.horas_pessoas_dia) / 24
    q_moto = (req.potencia_outros_motores_w * _W_PARA_KCALH * req.horas_outros_motores_dia) / 24
    q_int  = q_ilum + q_pess + q_moto

    total     = q_cond + q_inf + q_prod + q_resp + q_int
    total_seg = total * (1 + req.fator_seguranca_perc / 100)
    capacidade = total_seg * (24.0 / req.horas_funcionamento_motor)

    return CargaTermicaResponse(
        carga_conducao_kcalh=round(q_cond, 2),
        info_construtiva=(
            f"Núcleo: {req.nucleo} (k={k_iso} W/m·K) | "
            f"U={round(u, 4)} W/(m²·K) | "
            f"Piso: {req.tipo_piso}"
        ),
        carga_infiltracao_kcalh=round(q_inf, 2),
        info_infiltracao=info_inf,
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
