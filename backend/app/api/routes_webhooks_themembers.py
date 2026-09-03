import json
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.webhook_themembers import processar_webhook

router = APIRouter(prefix="/api/webhooks/themembers", tags=["webhooks"])


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def receber_webhook_checkout(
    request: Request,
    x_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook do Checkout TheMembers/TheBank — token estático em `x-signature`,
    não o HMAC da Área de Membros (são 2 sistemas diferentes na TheMembers,
    ver docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md §2).

    Sem JWT de propósito — provedor externo não carrega sessão de usuário.
    """
    token_configurado = settings.THEMEMBERS_WEBHOOK_TOKEN
    if not token_configurado or not x_signature or not secrets.compare_digest(x_signature, token_configurado):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida.")

    # Trava real da Etapa 1 (achado na revisão de código: validar_producao() só
    # cobre consistência de config no startup, não impedia a rota de processar
    # de verdade se o token fosse configurado antes da hora). Fica DEPOIS da
    # checagem de token de propósito — o passo de deploy da spec (§18.6) exige
    # confirmar que token ausente/incorreto retorna 401 mesmo desabilitado.
    if not settings.THEMEMBERS_WEBHOOK_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook desabilitado.")

    corpo_bruto = await request.body()
    try:
        body = json.loads(corpo_bruto)
        if not isinstance(body, dict):
            raise ValueError("Corpo do webhook precisa ser um objeto JSON.")
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="JSON inválido ou contrato não reconhecido.")

    try:
        registro = await processar_webhook(db, body, corpo_bruto)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Contrato do evento não reconhecido.")

    # Processamento é só transacional — nunca chama API externa/e-mail aqui
    # (spec §5). Toda combinação de status_processamento responde 200: o
    # provedor só precisa saber que recebemos, o estado fica auditável na
    # tabela pra diagnóstico administrativo.
    return {"recebido": True, "status": registro.status_processamento}
