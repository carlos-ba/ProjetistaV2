"""Consulta (só leitura) os dados salvos de um projeto por nome parcial — imprime
gabinete (só os campos técnicos, sem a imagem base64), inputs de carga térmica e
o resultado já calculado (dados_completos). Não grava nada no banco.

Uso:
    cd backend
    $env:DATABASE_URL = "postgresql+psycopg://...producao..."   # no seu terminal, não aqui no chat
    ..\\.venv\\Scripts\\python.exe scripts\\buscar_projeto.py "tatiminas"
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, or_  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.projeto import Projeto  # noqa: E402
from app.models.catalogo import PerfilProdutoTermico  # noqa: E402

# Campos do gabinete relevantes pra carga térmica — exclui imagem_projeto (base64,
# gigante e irrelevante aqui).
CAMPOS_GABINETE = (
    "comprimento", "largura", "altura", "temperatura_interna",
    "espessura", "nucleo", "tipo_piso",
)


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


async def buscar(termo: str):
    async with SessionLocal() as db:
        termo_like = f"%{termo}%"
        projetos = (await db.execute(
            select(Projeto).where(or_(
                Projeto.nome.ilike(termo_like),
                Projeto.cliente.ilike(termo_like),
            ))
        )).scalars().all()

        if not projetos:
            print(f"Nenhum projeto encontrado para '{termo}'.")
            return

        for p in projetos:
            print(f"\n=== {p.nome} ===")
            print(f"  id:          {p.id}")
            print(f"  cliente:     {p.cliente}")
            print(f"  empresa_id:  {p.empresa_id}")
            print(f"  created_at:  {p.created_at}")
            dc = p.dados_completos or {}

            gabinete = dc.get("gabinete") or {}
            gabinete_filtrado = {k: gabinete.get(k) for k in CAMPOS_GABINETE if k in gabinete}
            print("\n  --- gabinete (Card 1, só campos tecnicos) ---")
            _print_json(gabinete_filtrado)

            inputs_ct = dc.get("inputs_carga_termica") or {}
            print("\n  --- inputs_carga_termica (Card 2) ---")
            _print_json(inputs_ct)

            id_produto = inputs_ct.get("produtoSelecionado")
            if id_produto:
                perfil = (await db.execute(
                    select(PerfilProdutoTermico).where(PerfilProdutoTermico.id == int(id_produto))
                )).scalar_one_or_none()
                print(f"\n  --- perfil_produto_termico id={id_produto} (catálogo, usado no cálculo) ---")
                if perfil:
                    _print_json({
                        "nome": perfil.nome,
                        "ponto_congelamento": perfil.ponto_congelamento,
                        "calor_especifico_acima_congelamento": perfil.calor_especifico_acima_congelamento,
                        "calor_latente_congelamento": perfil.calor_latente_congelamento,
                        "calor_especifico_abaixo_congelamento": perfil.calor_especifico_abaixo_congelamento,
                        "taxa_respiracao": perfil.taxa_respiracao,
                    })
                else:
                    print("  (não encontrado no catálogo)")

            print("\n  --- carga_termica (valor final salvo) ---")
            _print_json(dc.get("carga_termica"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python scripts/buscar_projeto.py "termo de busca (nome ou cliente)"')
        sys.exit(1)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(buscar(sys.argv[1]))
