"""Consulta (só leitura) de um usuário por username/e-mail/nome parcial — sessões
ativas, empresa, papel, status da conta. Não grava nada no banco.

Uso:
    cd backend
    $env:DATABASE_URL = "postgresql+psycopg://...producao..."   # no seu terminal, não aqui no chat
    ..\.venv\Scripts\python.exe scripts\buscar_usuario.py "claudino"
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, func, or_  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
from app.models.empresa import Empresa  # noqa: E402
from app.models.sessao_usuario import SessaoUsuario  # noqa: E402


async def buscar(termo: str):
    async with SessionLocal() as db:
        termo_like = f"%{termo}%"
        usuarios = (await db.execute(
            select(Usuario).where(or_(
                Usuario.username.ilike(termo_like),
                Usuario.email.ilike(termo_like),
            ))
        )).scalars().all()

        if not usuarios:
            print(f"Nenhum usuário encontrado para '{termo}'.")
            return

        for u in usuarios:
            print(f"\n=== {u.username} ===")
            print(f"  id:             {u.id}")
            print(f"  email:          {u.email}")
            print(f"  email_verified: {u.email_verified}")
            print(f"  is_active:      {u.is_active}")
            print(f"  papel:          {u.papel}")
            print(f"  empresa_id:     {u.empresa_id}")
            print(f"  created_at:     {u.created_at}")

            if u.empresa_id:
                empresa = (await db.execute(
                    select(Empresa).where(Empresa.id == u.empresa_id)
                )).scalar_one_or_none()
                if empresa:
                    print(f"  empresa:        {empresa.nome} | plano={empresa.plano} | status={empresa.status_assinatura}")
            else:
                print("  empresa:        NENHUMA — get_empresa_atual vai dar 403")

            sessoes = (await db.execute(
                select(SessaoUsuario).where(SessaoUsuario.usuario_id == u.id)
                .order_by(SessaoUsuario.created_at.desc())
            )).scalars().all()
            ativas = [s for s in sessoes if s.revogada_em is None]
            print(f"  sessoes ativas: {len(ativas)} (de {len(sessoes)} totais)")
            for s in sessoes[:6]:
                estado = "REVOGADA" if s.revogada_em else "ATIVA"
                print(f"    [{estado}] id={s.id} ip={s.ip} ua={(s.user_agent or '')[:60]}")
                print(f"              criada={s.created_at} ultimo_uso={s.ultimo_uso_em}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python scripts/buscar_usuario.py "termo de busca (username ou email)"')
        sys.exit(1)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(buscar(sys.argv[1]))
