"""
Migra os dados do banco SQLite do V1 (projetista_frigorifico) para o PostgreSQL do V2.

Uso:
    cd backend/
    python scripts/seed_from_v1.py --v1-db <caminho_para_db.sqlite3>

Exemplo:
    python scripts/seed_from_v1.py --v1-db "C:/Users/carlo/PycharmProjects/projetista_frigorifico/backend/db.sqlite3"
"""
import argparse
import asyncio
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import (
    Categoria, Fabricante, UnidadeMedida, TipoProdutoTermico,
    PerfilProdutoTermico, Equipamento, PerformanceEquipamento,
    ComponenteTecnico, PerformanceComponente, Material,
)


def fetch_all(cursor, table: str) -> list[dict]:
    cursor.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


async def seed(v1_db_path: str) -> None:
    conn = sqlite3.connect(v1_db_path)
    cur = conn.cursor()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # --- categorias ---
        print("Importando categorias...")
        for row in fetch_all(cur, "produtos_categoria"):
            session.add(Categoria(id=row["id"], nome=row["nome"]))
        await session.flush()

        # --- fabricantes ---
        print("Importando fabricantes...")
        for row in fetch_all(cur, "produtos_fabricante"):
            session.add(Fabricante(id=row["id"], nome=row["nome"]))
        await session.flush()

        # --- unidades de medida ---
        print("Importando unidades de medida...")
        for row in fetch_all(cur, "produtos_unidademedida"):
            session.add(UnidadeMedida(id=row["id"], nome=row["nome"], sigla=row["sigla"]))
        await session.flush()

        # --- tipos de produto termico ---
        print("Importando tipos de produto termico...")
        for row in fetch_all(cur, "produtos_tipoprodutotermico"):
            session.add(TipoProdutoTermico(id=row["id"], nome=row["nome"]))
        await session.flush()

        # --- perfis de produto termico ---
        print("Importando perfis de produto termico...")
        for row in fetch_all(cur, "produtos_perfilprodutotermico"):
            session.add(PerfilProdutoTermico(
                id=row["id"],
                nome=row["nome"],
                tipo_id=row["tipo_id"],
                ponto_congelamento=row["ponto_congelamento"],
                calor_especifico_acima_congelamento=row["calor_especifico_acima_congelamento"],
                calor_latente_congelamento=row["calor_latente_congelamento"],
                calor_especifico_abaixo_congelamento=row["calor_especifico_abaixo_congelamento"],
                taxa_respiracao=row.get("taxa_respiracao"),
                temperatura_conservacao=row.get("temperatura_conservacao"),
                umidade_relativa=row.get("umidade_relativa"),
                teor_agua=row.get("teor_agua"),
            ))
        await session.flush()

        # --- equipamentos ---
        print("Importando equipamentos...")
        for row in fetch_all(cur, "produtos_equipamento"):
            session.add(Equipamento(
                id=row["id"],
                categoria_id=row["categoria_id"],
                modelo=row["modelo"],
                fabricante_id=row["fabricante_id"],
                custo=row["custo"],
                unidade_medida_id=row["unidade_medida_id"],
                qtde_ventiladores=row["qtde_ventiladores"],
                diametro_ventilador_mm=row["diametro_ventilador_mm"],
                vazao_ar_m3h=row["vazao_ar_m3h"],
                flecha_ar_m=row["flecha_ar_m"],
            ))
        await session.flush()

        # --- performance equipamento ---
        print("Importando curvas de performance de equipamento...")
        for row in fetch_all(cur, "produtos_performanceequipamento"):
            session.add(PerformanceEquipamento(
                id=row["id"],
                equipamento_id=row["equipamento_id"],
                fluido=row["fluido"],
                temp_condensacao=row["temp_condensacao"],
                temp_evaporacao=row["temp_evaporacao"],
                delta_t=row["delta_t"],
                capacidade=row["capacidade"],
                consumo_w=row.get("consumo_w"),
            ))
        await session.flush()

        # --- componentes tecnicos ---
        print("Importando componentes tecnicos...")
        for row in fetch_all(cur, "produtos_componentetecnico"):
            import json
            dados = row.get("dados_especificos")
            if isinstance(dados, str):
                try:
                    dados = json.loads(dados)
                except Exception:
                    dados = {}
            session.add(ComponenteTecnico(
                id=row["id"],
                categoria_id=row["categoria_id"],
                modelo=row["modelo"],
                codigo_fabricante=row.get("codigo_fabricante"),
                fabricante_id=row["fabricante_id"],
                conexao_entrada=row["conexao_entrada"],
                conexao_saida=row["conexao_saida"],
                capacidade_nominal=row["capacidade_nominal"],
                dados_especificos=dados or {},
                custo=row["custo"],
            ))
        await session.flush()

        # --- performance componente ---
        print("Importando performance de componentes...")
        for row in fetch_all(cur, "produtos_performancecomponente"):
            session.add(PerformanceComponente(
                id=row["id"],
                componente_id=row["componente_id"],
                fluido=row["fluido"],
                temp_evaporacao=row["temp_evaporacao"],
                temp_condensacao=row["temp_condensacao"],
                capacidade_kcalh=row["capacidade_kcalh"],
                capacidade_min_kcalh=row["capacidade_min_kcalh"],
            ))
        await session.flush()

        # --- materiais ---
        print("Importando materiais...")
        for row in fetch_all(cur, "produtos_material"):
            import json
            detalhes = row.get("detalhes_tecnicos")
            if isinstance(detalhes, str):
                try:
                    detalhes = json.loads(detalhes)
                except Exception:
                    detalhes = {}
            session.add(Material(
                id=row["id"],
                nome=row["nome"],
                categoria_id=row["categoria_id"],
                fabricante_id=row.get("fabricante_id"),
                custo=row["custo"],
                unidade_medida_id=row["unidade_medida_id"],
                diametro_conexao=row.get("diametro_conexao"),
                capacidade_nominal=row["capacidade_nominal"],
                detalhes_tecnicos=detalhes or {},
            ))
        await session.flush()

        await session.commit()
        print("\nImportacao concluida com sucesso!")

    conn.close()
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed V2 database from V1 SQLite")
    parser.add_argument("--v1-db", required=True, help="Caminho para o db.sqlite3 do V1")
    args = parser.parse_args()

    if not os.path.exists(args.v1_db):
        print(f"Erro: arquivo nao encontrado: {args.v1_db}")
        sys.exit(1)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(seed(args.v1_db))
