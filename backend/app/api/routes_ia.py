"""Rotas de IA da proposta (beta fechado).

POST /api/v1/ia/descritivo — redige o descritivo técnico a partir dos fatos já
calculados. Liberado por empresa (`Empresa.ia_descritivo_habilitado`), conferido
AQUI no backend: cada chamada custa dinheiro, então esconder o botão no frontend
não basta (ao contrário de `recursos_avancados_habilitados`).
"""
import logging
import time
from collections import defaultdict, deque
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.auth import UserOut
from app.services.auth import get_current_user
from app.services.ia_descritivo import MODELO, gerar_descritivo_ia

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ia", tags=["ia"])

# Teto de segurança por empresa, em memória (o Render roda 1 processo só —
# WEB_CONCURRENCY=1; zera num restart). É só uma rede de proteção contra loop/abuso
# do beta; o limite "de verdade" por projeto (5) é do frontend. Medição de uso
# persistente fica pra quando a IA for liberada pra um plano.
_MAX_POR_HORA = 20
_JANELA_S = 3600
_chamadas: dict[UUID, deque] = defaultdict(deque)


def _checar_teto(empresa_id: UUID) -> None:
    agora = time.monotonic()
    fila = _chamadas[empresa_id]
    while fila and agora - fila[0] > _JANELA_S:
        fila.popleft()
    if len(fila) >= _MAX_POR_HORA:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas gerações por IA na última hora. Tente novamente mais tarde.",
        )
    fila.append(agora)


class SecaoFatos(BaseModel):
    titulo: str | None = Field(None, max_length=120)
    paragrafos: list[str] = Field(..., max_length=20)


class DescritivoIARequest(BaseModel):
    secoes: list[SecaoFatos] = Field(..., min_length=1, max_length=10)


class DescritivoIAResponse(BaseModel):
    texto: str
    numeros_fora_dos_fatos: list[str]
    modelo: str


@router.post("/descritivo", response_model=DescritivoIAResponse)
async def gerar_descritivo(
    payload: DescritivoIARequest,
    usuario: UserOut = Depends(get_current_user),
):
    if not usuario.empresa_id:
        raise HTTPException(status_code=403, detail="Usuário sem empresa vinculada. Contate o administrador.")
    if not usuario.empresa_ia_descritivo_habilitado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A redação por IA não está habilitada para a sua empresa.",
        )
    if any(len(p) > 1500 for s in payload.secoes for p in s.paragrafos):
        raise HTTPException(status_code=422, detail="Parágrafo de fatos grande demais.")

    _checar_teto(usuario.empresa_id)
    try:
        texto, fora = await gerar_descritivo_ia([s.model_dump() for s in payload.secoes])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        logger.exception("Falha ao gerar descritivo por IA (empresa_id=%s)", usuario.empresa_id)
        raise HTTPException(status_code=502, detail="Não foi possível gerar o texto agora. Tente novamente.")
    return DescritivoIAResponse(texto=texto, numeros_fora_dos_fatos=fora, modelo=MODELO)
