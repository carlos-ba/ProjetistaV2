from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EventoNormalizado(BaseModel):
    """Saída do normalizador — não tenta tipar o payload bruto (a documentação
    mostra 2 formatos de envelope diferentes, com campos opcionais em todo
    lugar); a normalização é procedural, feita em
    `app.services.webhook_themembers.normalizar_payload`. Este é o formato
    estável que o resto do serviço consome dali em diante.
    """

    event: str
    objeto: Optional[str] = None
    external_id: Optional[str] = None
    produto_id: Optional[str] = None
    email_comprador: Optional[str] = None
    data: dict[str, Any] = {}
    criado_em_provedor: Optional[datetime] = None
    proxima_cobranca_em: Optional[datetime] = None
    expira_em: Optional[datetime] = None
    external_customer_id: Optional[str] = None
    external_order_id: Optional[str] = None
    external_subscription_code: Optional[str] = None


class WebhookProcessResultado(BaseModel):
    """Resposta interna do serviço pro router decidir o HTTP status —
    nunca é devolvida como está pro chamador externo (a rota sempre responde
    200/401/400/500 conforme a tabela da spec, não expõe este detalhe)."""

    status_processamento: str
    empresa_id: Optional[str] = None
    motivo: Optional[str] = None
