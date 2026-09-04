"""Consulta (só leitura) de eventos do webhook do Checkout TheMembers — status,
e-mail associado, empresa. Sem argumento lista pendentes/erro/produto
desconhecido (o que precisa de atenção); com um argumento, filtra por
status_processamento exato ou por e-mail (substring).

Uso:
    cd backend
    $env:DATABASE_URL = "postgresql+psycopg://...producao..."   # no seu terminal, não aqui no chat
    ..\.venv\Scripts\python.exe scripts\listar_eventos_webhook.py
    ..\.venv\Scripts\python.exe scripts\listar_eventos_webhook.py erro
    ..\.venv\Scripts\python.exe scripts\listar_eventos_webhook.py cliente@exemplo.com
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, or_  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.webhook_checkout_evento import (  # noqa: E402
    WebhookCheckoutEvento,
    STATUS_ERRO,
    STATUS_PENDENTE_USUARIO,
    STATUS_PRODUTO_DESCONHECIDO,
)

STATUS_QUE_PRECISAM_ATENCAO = (STATUS_ERRO, STATUS_PENDENTE_USUARIO, STATUS_PRODUTO_DESCONHECIDO)


async def listar(filtro: str | None):
    async with SessionLocal() as db:
        stmt = select(WebhookCheckoutEvento).order_by(WebhookCheckoutEvento.recebido_em.desc()).limit(50)
        if filtro is None:
            stmt = stmt.where(WebhookCheckoutEvento.status_processamento.in_(STATUS_QUE_PRECISAM_ATENCAO))
        elif filtro in STATUS_QUE_PRECISAM_ATENCAO or filtro in (
            "recebido", "processado", "ignorado",
        ):
            stmt = stmt.where(WebhookCheckoutEvento.status_processamento == filtro)
        else:
            like = f"%{filtro}%"
            stmt = stmt.where(or_(
                WebhookCheckoutEvento.email_comprador_normalizado.ilike(like),
                WebhookCheckoutEvento.chave_evento.ilike(like),
            ))

        eventos = (await db.execute(stmt)).scalars().all()
        if not eventos:
            print("Nenhum evento encontrado.")
            return

        for e in eventos:
            print(f"\n=== {e.chave_evento} ===")
            print(f"  status:        {e.status_processamento}")
            print(f"  tipo_evento:   {e.tipo_evento}")
            print(f"  produto_id:    {e.produto_id}")
            print(f"  email:         {e.email_comprador_normalizado}")
            print(f"  empresa_id:    {e.empresa_id}")
            print(f"  erro_resumido: {e.erro_resumido}")
            print(f"  recebido_em:   {e.recebido_em}")
            print(f"  processado_em: {e.processado_em}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(listar(sys.argv[1] if len(sys.argv) > 1 else None))
