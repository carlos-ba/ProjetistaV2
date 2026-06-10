"""
Endpoint de seed — popula o banco de produção com dados iniciais.
Protegido por SECRET_KEY. Chamar UMA vez após o deploy.
Após executar com sucesso, pode ser desabilitado no main.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.session import get_db
from app.core.config import settings

router = APIRouter(prefix="/api/seed", tags=["seed"])


SEED_SQL = """
INSERT INTO unidade_medida (id, nome, sigla) VALUES
  (1,'unidade','un'),(2,'metro','m'),(3,'metro quadrado','m²'),
  (4,'quilograma','kg'),(5,'litro','L'),(6,'conjunto','cj')
ON CONFLICT DO NOTHING;

INSERT INTO fabricante (nome) VALUES
  ('Tecumseh'),('Embraco'),('Bitzer'),('Danfoss'),('Parker'),
  ('Elgin'),('Genérico'),('Kingspan Isoeste'),('RAC'),('Armacel')
ON CONFLICT (nome) DO NOTHING;

INSERT INTO categoria (id, nome) VALUES
  (1,'Unidade Condensadora'),(2,'Evaporadora'),(3,'Compressor'),
  (4,'Válvula de Expansão Termostática'),(5,'Filtro Secador'),
  (6,'Visor de Líquido'),(7,'Válvula Solenoide'),(8,'Pressostato'),
  (9,'Tubulação de Cobre'),(10,'Isolamento Térmico'),
  (11,'Material Elétrico'),(12,'Painel Frigorífico'),
  (13,'Solda e Fluxo'),(14,'Separador de Líquido')
ON CONFLICT DO NOTHING;

INSERT INTO tipo_produto_termico (id, nome) VALUES
  (1,'Carnes e Aves'),(2,'Laticínios'),(3,'FLV (Frutas, Legumes e Verduras)'),
  (4,'Pescados'),(5,'Frios e Embutidos'),(6,'Sorvetes e Congelados'),
  (7,'Bebidas'),(8,'Padaria e Confeitaria'),(9,'Geral / Industrial')
ON CONFLICT DO NOTHING;

INSERT INTO perfil_produto_termico
  (nome,tipo_id,ponto_congelamento,calor_especifico_acima_congelamento,
   calor_latente_congelamento,calor_especifico_abaixo_congelamento,
   taxa_respiracao,temperatura_conservacao,umidade_relativa,teor_agua)
VALUES
  ('Carne Bovina',1,-1.70,3.52,249.0,1.76,NULL,2.0,88.0,74.0),
  ('Carne Suína',1,-2.20,3.60,246.0,1.81,NULL,2.0,85.0,75.9),
  ('Frango Inteiro',1,-2.80,3.31,220.0,1.55,NULL,-1.0,85.0,66.0),
  ('Carne Congelada',1,-1.70,3.52,249.0,1.76,NULL,-18.0,90.0,74.0),
  ('Queijo Maturado',2,-6.00,2.09,84.0,1.26,NULL,6.0,80.0,37.0),
  ('Manteiga',2,-2.30,2.05,113.0,1.26,NULL,4.0,80.0,16.0),
  ('Leite Pasteurizado',2,-0.60,3.93,268.0,1.93,NULL,4.0,85.0,87.0),
  ('Alface',3,-0.20,3.96,256.0,1.97,62.0,2.0,95.0,95.0),
  ('Tomate Maduro',3,-0.50,3.94,255.0,1.96,28.0,10.0,90.0,94.0),
  ('Banana Madura',3,-0.80,3.35,224.0,1.65,25.0,14.0,90.0,74.0),
  ('Maçã',3,-1.50,3.73,243.0,1.84,10.0,2.0,92.0,84.0),
  ('Batata',3,-0.60,3.51,236.0,1.77,9.0,8.0,90.0,77.0),
  ('Peixe Fresco',4,-2.20,3.76,258.0,1.86,NULL,0.0,95.0,76.0),
  ('Camarão Fresco',4,-2.30,3.60,260.0,1.77,NULL,0.0,95.0,76.0),
  ('Peixe Congelado',4,-2.20,3.76,258.0,1.86,NULL,-18.0,90.0,76.0),
  ('Presunto Cozido',5,-3.00,3.18,213.0,1.55,NULL,4.0,80.0,60.0),
  ('Salsicha',5,-2.50,3.39,234.0,1.68,NULL,4.0,80.0,63.0),
  ('Sorvete',6,-14.50,1.63,210.0,1.26,NULL,-18.0,90.0,60.0),
  ('Mix de Açaí',6,-10.00,2.10,200.0,1.30,NULL,-18.0,90.0,60.0),
  ('Cerveja Lata',7,-2.20,4.02,268.0,1.97,NULL,4.0,70.0,92.0),
  ('Refrigerante',7,-1.00,4.00,268.0,1.97,NULL,4.0,70.0,90.0),
  ('Vinho',7,-4.20,3.94,264.0,1.95,NULL,8.0,70.0,87.0),
  ('Massa Fresca',8,-3.50,3.30,236.0,1.62,NULL,4.0,85.0,65.0),
  ('Chocolate',8,-17.60,1.47,105.0,1.05,NULL,15.0,50.0,1.0),
  ('Produto Genérico +5',9,0.00,3.50,230.0,1.75,NULL,5.0,80.0,70.0),
  ('Produto Genérico -18',9,-2.00,3.50,230.0,1.75,NULL,-18.0,90.0,70.0)
ON CONFLICT (nome) DO NOTHING;

SELECT setval('unidade_medida_id_seq', GREATEST((SELECT MAX(id) FROM unidade_medida), 1));
SELECT setval('categoria_id_seq', GREATEST((SELECT MAX(id) FROM categoria), 1));
SELECT setval('tipo_produto_termico_id_seq', GREATEST((SELECT MAX(id) FROM tipo_produto_termico), 1));
"""


@router.post("/catalogo")
async def seed_catalogo(token: str, db: AsyncSession = Depends(get_db)):
    """
    Importa equipamentos, componentes, painéis, isolamentos e portas.
    Lê o arquivo seed_catalogo_clean.sql do repositório.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    # Verificar se já tem dados
    result = await db.execute(text("SELECT COUNT(*) FROM equipamento"))
    count = result.scalar()
    if count > 0:
        return {"status": "ja_executado", "equipamentos": count}

    # Ler SQL do arquivo
    import os
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "seed_catalogo_clean.sql")
    if not os.path.exists(sql_path):
        raise HTTPException(status_code=404, detail=f"Arquivo seed não encontrado: {sql_path}")

    with open(sql_path, encoding="utf-8") as f:
        sql_content = f.read()

    # Executar linha por linha (apenas INSERTs)
    inseridos = 0
    for line in sql_content.splitlines():
        line = line.strip()
        if line.startswith("INSERT INTO"):
            try:
                await db.execute(text(line))
                inseridos += 1
            except Exception:
                pass  # ON CONFLICT DO NOTHING equivalente

    await db.commit()

    # Contar resultados
    totais = {}
    for tabela in ["equipamento", "performance_equipamento", "componente_tecnico",
                   "painel_frigorifico", "isolamento_tubulacao", "porta_frigoriifica"]:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
        totais[tabela] = r.scalar()

    return {"status": "sucesso", "inseridos": inseridos, "totais": totais}


@router.post("/delta")
async def seed_delta(token: str, db: AsyncSession = Depends(get_db)):
    """
    Insere dados faltantes (componentes, painéis, isolamentos, portas).
    Usa ON CONFLICT DO NOTHING — seguro rodar múltiplas vezes.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    import os
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "seed_delta.sql")
    if not os.path.exists(sql_path):
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {sql_path}")

    with open(sql_path, encoding="utf-8") as f:
        sql_content = f.read()

    inseridos = 0
    erros = 0
    for line in sql_content.splitlines():
        line = line.strip()
        if line.startswith("INSERT INTO"):
            try:
                await db.execute(text(line))
                inseridos += 1
            except Exception:
                erros += 1

    await db.commit()

    totais = {}
    for tabela in ["componente_tecnico", "performance_componente",
                   "painel_frigorifico", "isolamento_tubulacao", "porta_frigoriifica"]:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
        totais[tabela] = r.scalar()

    return {"status": "sucesso", "inseridos": inseridos, "erros": erros, "totais": totais}


@router.post("/perf-t2")
async def seed_perf_t2(token: str, db: AsyncSession = Depends(get_db)):
    """
    Insere as 128 performances das VETs T2 Danfoss faltantes em produção.
    Usa ON CONFLICT DO NOTHING — seguro rodar múltiplas vezes.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    import os
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "seed_perf_t2.sql")
    if not os.path.exists(sql_path):
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {sql_path}")

    with open(sql_path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip().startswith("INSERT") or l.strip().startswith("SELECT")]

    inseridos = 0
    erros = 0
    for line in lines:
        try:
            await db.execute(text(line))
            inseridos += 1
        except Exception:
            erros += 1

    await db.commit()

    r = await db.execute(text("SELECT COUNT(*) FROM performance_componente"))
    total = r.scalar()

    return {"status": "sucesso", "inseridos": inseridos, "erros": erros,
            "total_performance_componente": total}


@router.post("/sep-oleo")
async def seed_sep_oleo(token: str, db: AsyncSession = Depends(get_db)):
    """Insere separadores de óleo RAC Brasil (10 modelos, 140 performances). Idempotente."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    from app.models.componente import ComponenteTecnico, PerformanceComponente
    from app.models.catalogo import Categoria, Fabricante
    from sqlalchemy import select as sa_select

    CATEGORIA = "Separador de Óleo"
    T_COND = 35

    CATALOGO = [
        {"modelo": 'SOF 1/2"S',   "codigo": "050-101", "conexao": '1/2"',     "tipo": "Solda",
         "R404A": {-40:7140,-30:7397,-20:7653,-10:7910,5:8420},
         "R134a": {-30:4550,-20:4765,-10:4980,5:5500}},
        {"modelo": 'SOF 1/2"R',   "codigo": "050-102", "conexao": '1/2" SAE', "tipo": "Rosca",
         "R404A": {-40:7140,-30:7397,-20:7653,-10:7910,5:8420},
         "R134a": {-30:4550,-20:4765,-10:4980,5:5500}},
        {"modelo": 'SOF 5/8"S',   "codigo": "050-103", "conexao": '5/8"',     "tipo": "Solda",
         "R404A": {-40:14440,-30:14843,-20:15247,-10:15650,5:16850},
         "R134a": {-30:9110,-20:9370,-10:9630,5:11000}},
        {"modelo": 'SOF 5/8"R',   "codigo": "050-104", "conexao": '5/8" SAE', "tipo": "Rosca",
         "R404A": {-40:14440,-30:14843,-20:15247,-10:15650,5:16850},
         "R134a": {-30:9110,-20:9370,-10:9630,5:11000}},
        {"modelo": 'SOF 3/4"R',   "codigo": "050-125", "conexao": '3/4" SAE', "tipo": "Rosca",
         "R404A": {-40:16860,-30:18120,-20:19380,-10:20640,5:22450},
         "R134a": {-30:12040,-20:12640,-10:13240,5:14790}},
        {"modelo": 'SOF 7/8"S',   "codigo": "050-105", "conexao": '7/8"',     "tipo": "Solda",
         "R404A": {-40:21590,-30:22247,-20:22903,-10:23560,5:25370},
         "R134a": {-30:13500,-20:14060,-10:14620,5:16590}},
        {"modelo": 'SOF 1.1/8"S', "codigo": "050-106", "conexao": '1.1/8"',   "tipo": "Solda",
         "R404A": {-40:28720,-30:29580,-20:30440,-10:31300,5:33880},
         "R134a": {-30:18230,-20:19435,-10:20640,5:22100}},
        {"modelo": 'SOF 1.3/8"S', "codigo": "050-107", "conexao": '1.3/8"',   "tipo": "Solda",
         "R404A": {-40:32670,-30:33760,-20:34850,-10:35940,5:38950},
         "R134a": {-30:20980,-20:22355,-10:23730,5:25370}},
        {"modelo": 'SOF 1.5/8"S', "codigo": "050-114", "conexao": '1.5/8"',   "tipo": "Solda",
         "R404A": {-40:48420,-30:50053,-20:51687,-10:53320,5:56160},
         "R134a": {-30:32340,-20:33930,-10:35520,5:39300}},
        {"modelo": 'SOF 2.1/8"S', "codigo": "050-109", "conexao": '2.1/8"',   "tipo": "Solda",
         "R404A": {-40:75770,-30:78380,-20:80990,-10:83600,5:94600},
         "R134a": {-30:57450,-20:60330,-10:63210,5:69580}},
    ]

    # Categoria
    res = await db.execute(sa_select(Categoria).where(Categoria.nome == CATEGORIA))
    cat = res.scalar_one_or_none()
    if not cat:
        cat = Categoria(nome=CATEGORIA)
        db.add(cat); await db.flush()

    # Fabricante
    res = await db.execute(sa_select(Fabricante).where(Fabricante.nome == "RAC"))
    fab = res.scalar_one_or_none()
    if not fab:
        fab = Fabricante(nome="RAC")
        db.add(fab); await db.flush()

    comp_novos = 0; perf_ins = 0; perf_upd = 0

    for item in CATALOGO:
        cap_max = float(max(item["R404A"].values()))
        res = await db.execute(sa_select(ComponenteTecnico).where(
            ComponenteTecnico.modelo == item["modelo"],
            ComponenteTecnico.categoria_id == cat.id))
        comp = res.scalar_one_or_none()
        if not comp:
            comp = ComponenteTecnico(
                modelo=item["modelo"], codigo_fabricante=item["codigo"],
                categoria_id=cat.id, fabricante_id=fab.id,
                conexao_entrada=item["conexao"], conexao_saida=item["conexao"],
                capacidade_nominal=cap_max,
                dados_especificos={"tipo_conexao": item["tipo"], "t_cond_base": T_COND},
                custo=0)
            db.add(comp); await db.flush()
            comp_novos += 1

        for fluido, perfs in [("R404A", item["R404A"]), ("R22", item["R404A"]), ("R134a", item["R134a"])]:
            for t_evap, cap in perfs.items():
                res = await db.execute(sa_select(PerformanceComponente).where(
                    PerformanceComponente.componente_id == comp.id,
                    PerformanceComponente.fluido == fluido,
                    PerformanceComponente.temp_evaporacao == t_evap,
                    PerformanceComponente.temp_condensacao == T_COND))
                ex = res.scalar_one_or_none()
                if ex:
                    ex.capacidade_kcalh = float(cap); perf_upd += 1
                else:
                    db.add(PerformanceComponente(
                        componente_id=comp.id, fluido=fluido,
                        temp_evaporacao=t_evap, temp_condensacao=T_COND,
                        capacidade_kcalh=float(cap), capacidade_min_kcalh=0.0))
                    perf_ins += 1

    await db.commit()

    res = await db.execute(sa_select(Categoria).where(Categoria.nome == CATEGORIA))
    cat = res.scalar_one_or_none()
    r = await db.execute(text(f"SELECT COUNT(*) FROM componente_tecnico WHERE categoria_id={cat.id}"))
    r2 = await db.execute(text(f"SELECT COUNT(*) FROM performance_componente pc JOIN componente_tecnico ct ON ct.id=pc.componente_id WHERE ct.categoria_id={cat.id}"))

    return {"status": "sucesso", "componentes_novos": comp_novos,
            "performances_inseridas": perf_ins, "performances_atualizadas": perf_upd,
            "total_componentes": r.scalar(), "total_performances": r2.scalar()}


@router.get("/auditoria")
async def auditoria(token: str, db: AsyncSession = Depends(get_db)):
    """
    Relatório de integridade do banco de produção.
    Mostra contagens por tabela, componentes sem performance e equipamentos sem performance.
    Usar após qualquer importação local para verificar se produção está sincronizada.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    resultado = {}

    # ── Contagens gerais ──────────────────────────────────────────────────
    tabelas = [
        "categoria", "fabricante",
        "equipamento", "performance_equipamento",
        "componente_tecnico", "performance_componente",
        "painel_frigorifico", "isolamento_tubulacao", "porta_frigoriifica",
        "perfil_produto_termico",
    ]
    contagens = {}
    for t in tabelas:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {t}"))
        contagens[t] = r.scalar()
    resultado["contagens"] = contagens

    # ── Componentes sem performance (problema de integridade) ─────────────
    r = await db.execute(text("""
        SELECT ct.modelo, cat.nome as categoria
        FROM componente_tecnico ct
        JOIN categoria cat ON cat.id = ct.categoria_id
        LEFT JOIN performance_componente pc ON pc.componente_id = ct.id
        WHERE pc.id IS NULL
        ORDER BY cat.nome, ct.modelo
    """))
    sem_perf = [{"modelo": row[0], "categoria": row[1]} for row in r.fetchall()]
    resultado["componentes_sem_performance"] = sem_perf
    resultado["componentes_sem_performance_total"] = len(sem_perf)

    # ── Equipamentos sem performance ──────────────────────────────────────
    r = await db.execute(text("""
        SELECT e.modelo, cat.nome as categoria
        FROM equipamento e
        JOIN categoria cat ON cat.id = e.categoria_id
        LEFT JOIN performance_equipamento pe ON pe.equipamento_id = e.id
        WHERE pe.id IS NULL
        ORDER BY cat.nome, e.modelo
    """))
    eq_sem_perf = [{"modelo": row[0], "categoria": row[1]} for row in r.fetchall()]
    resultado["equipamentos_sem_performance"] = eq_sem_perf
    resultado["equipamentos_sem_performance_total"] = len(eq_sem_perf)

    # ── Performances por componente (detecta distribuição desigual) ───────
    r = await db.execute(text("""
        SELECT ct.modelo, COUNT(pc.id) as total_performances
        FROM componente_tecnico ct
        LEFT JOIN performance_componente pc ON pc.componente_id = ct.id
        GROUP BY ct.modelo
        ORDER BY ct.modelo
    """))
    perf_por_comp = {row[0]: row[1] for row in r.fetchall()}
    resultado["performances_por_componente"] = perf_por_comp

    # ── Status geral ──────────────────────────────────────────────────────
    ok = (len(sem_perf) == 0 and len(eq_sem_perf) == 0)
    resultado["status"] = "OK" if ok else "ATENCAO — itens sem performance detectados"

    return resultado


@router.post("/executar")
async def executar_seed(token: str, db: AsyncSession = Depends(get_db)):
    """
    Executa o seed de dados iniciais.
    Protegido por token = SECRET_KEY do sistema.
    Chamar apenas UMA vez após o deploy inicial.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    # Verificar se já tem dados
    result = await db.execute(text("SELECT COUNT(*) FROM categoria"))
    count = result.scalar()
    if count > 0:
        return {"status": "ja_executado", "categorias": count}

    # Executar seed
    await db.execute(text(SEED_SQL))
    await db.commit()

    # Contar resultados
    totais = {}
    for tabela in ["categoria", "tipo_produto_termico", "perfil_produto_termico", "fabricante"]:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
        totais[tabela] = r.scalar()

    return {"status": "sucesso", "registros": totais}


@router.post("/base-completo")
async def seed_base_completo(token: str, db: AsyncSession = Depends(get_db)):
    """
    Força a inserção de todas as categorias, fabricantes e dados base
    mesmo que já existam registros. Usa ON CONFLICT DO NOTHING — seguro.
    Útil para completar bancos que foram criados com seed parcial.
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    # Executa cada bloco separadamente para contornar limitação do driver async
    sqls = [
        """INSERT INTO categoria (id, nome) VALUES
          (1,'Unidade Condensadora'),(2,'Evaporadora'),(3,'Compressor'),
          (4,'Válvula de Expansão Termostática'),(5,'Filtro Secador'),
          (6,'Visor de Líquido'),(7,'Válvula Solenoide'),(8,'Pressostato'),
          (9,'Tubulação de Cobre'),(10,'Isolamento Térmico'),
          (11,'Material Elétrico'),(12,'Painel Frigorífico'),
          (13,'Solda e Fluxo'),(14,'Separador de Líquido'),
          (15,'Separador de Óleo')
        ON CONFLICT DO NOTHING""",

        """INSERT INTO fabricante (nome) VALUES
          ('Tecumseh'),('Embraco'),('Bitzer'),('Danfoss'),('Parker'),
          ('Elgin'),('Genérico'),('Kingspan Isoeste'),('RAC'),('Armacel')
        ON CONFLICT (nome) DO NOTHING""",

        """INSERT INTO unidade_medida (id, nome, sigla) VALUES
          (1,'unidade','un'),(2,'metro','m'),(3,'metro quadrado','m²'),
          (4,'quilograma','kg'),(5,'litro','L'),(6,'conjunto','cj')
        ON CONFLICT DO NOTHING""",
    ]

    for sql in sqls:
        await db.execute(text(sql))

    await db.commit()

    totais = {}
    for tabela in ["categoria", "fabricante", "unidade_medida"]:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
        totais[tabela] = r.scalar()

    # Lista as categorias inseridas
    r = await db.execute(text("SELECT id, nome FROM categoria ORDER BY id"))
    totais["categorias_lista"] = [{"id": row[0], "nome": row[1]} for row in r.fetchall()]

    return {"status": "sucesso", "totais": totais}


@router.post("/fix-categorias")
async def fix_categorias(token: str, db: AsyncSession = Depends(get_db)):
    """Corrige nomes de categorias para bater exatamente com o código."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    updates = [
        (1,  "Unidade Condensadora"),
        (2,  "Evaporadora"),
        (3,  "Compressor"),
        (4,  "Válvula de Expansão Termostática"),
        (5,  "Filtro Secador"),
        (6,  "Visor de Líquido"),
        (7,  "Válvula Solenoide"),
        (8,  "Pressostato"),
        (9,  "Tubulação de Cobre"),
        (10, "Isolamento Térmico"),
        (11, "Material Elétrico"),
        (12, "Painel Frigorífico"),
        (13, "Solda e Fluxo"),
        (14, "Separador de Líquido"),
        (15, "Separador de Óleo"),
    ]

    for cat_id, nome in updates:
        await db.execute(
            text("UPDATE categoria SET nome = :nome WHERE id = :id"),
            {"nome": nome, "id": cat_id}
        )

    await db.commit()

    r = await db.execute(text("SELECT id, nome FROM categoria ORDER BY id"))
    categorias = [{"id": row[0], "nome": row[1]} for row in r.fetchall()]

    return {"status": "sucesso", "categorias": categorias}


@router.post("/fix-equipamentos-duplicados")
async def fix_equipamentos_duplicados(token: str, db: AsyncSession = Depends(get_db)):
    """Remove registros duplicados de equipamento (mesmo modelo, mantém o de menor id)."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    # Encontra duplicatas
    r = await db.execute(text("""
        SELECT modelo, COUNT(*) as total, MIN(id) as manter
        FROM equipamento
        GROUP BY modelo
        HAVING COUNT(*) > 1
    """))
    duplicatas = r.fetchall()

    removidos = 0
    for modelo, total, manter_id in duplicatas:
        # Deleta todos exceto o de menor id
        res = await db.execute(text("""
            DELETE FROM equipamento
            WHERE modelo = :m AND id != :keep
        """), {"m": modelo, "keep": manter_id})
        removidos += res.rowcount

    await db.commit()

    r = await db.execute(text("SELECT COUNT(*) FROM equipamento"))
    r2 = await db.execute(text("SELECT COUNT(*) FROM performance_equipamento"))

    return {
        "status": "sucesso",
        "duplicatas_encontradas": len(duplicatas),
        "registros_removidos": removidos,
        "total_equipamentos": r.scalar(),
        "total_performances": r2.scalar()
    }


@router.get("/export-equipamentos")
async def export_equipamentos(token: str, db: AsyncSession = Depends(get_db)):
    """Exporta todos os equipamentos com performances para sincronização entre bancos."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    r = await db.execute(text("""
        SELECT e.id, e.modelo, cat.nome as categoria, f.nome as fabricante,
               e.qtde_ventiladores, e.diametro_ventilador_mm,
               e.vazao_ar_m3h, e.flecha_ar_m, e.custo
        FROM equipamento e
        JOIN categoria cat ON cat.id = e.categoria_id
        JOIN fabricante f ON f.id = e.fabricante_id
        ORDER BY cat.nome, e.modelo
    """))
    equipamentos = []
    for row in r.fetchall():
        eq_id = row[0]
        r2 = await db.execute(text("""
            SELECT fluido, temp_ambiente, temp_evaporacao, delta_t,
                   capacidade, consumo_kw
            FROM performance_equipamento
            WHERE equipamento_id = :eid
            ORDER BY fluido, temp_evaporacao
        """), {"eid": eq_id})
        perfs = [{"fluido": p[0], "temp_amb": p[1], "temp_evap": p[2],
                  "delta_t": float(p[3]), "capacidade": p[4],
                  "consumo_kw": float(p[5]) if p[5] else None}
                 for p in r2.fetchall()]
        equipamentos.append({
            "modelo": row[1], "categoria": row[2], "fabricante": row[3],
            "qtde_vent": row[4], "diam_vent": row[5],
            "vazao_ar": row[6], "flecha_ar": row[7],
            "custo": float(row[8]) if row[8] else 0,
            "performances": perfs
        })

    return {"total": len(equipamentos), "equipamentos": equipamentos}


@router.post("/isolamentos")
async def seed_isolamentos(token: str, db: AsyncSession = Depends(get_db)):
    """Insere os 97 registros de isolamento Armacel. Idempotente."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    DADOS = [
        (6.0,"D","D-06",6.0),(6.0,"F","F-06",9.0),(6.0,"H","H-06",13.0),(6.0,"M","M-06",19.0),
        (10.0,"D","D-10",6.5),(10.0,"F","F-10",9.0),(10.0,"H","H-10",13.0),(10.0,"M","M-10",19.0),
        (12.0,"D","D-12",7.0),(12.0,"F","F-12",9.5),(12.0,"H","H-12",13.0),(12.0,"M","M-12",19.0),(12.0,"R","R-12",25.0),
        (15.0,"D","D-15",7.0),(15.0,"F","F-15",9.5),(15.0,"H","H-15",13.0),(15.0,"M","M-15",19.0),(15.0,"R","R-15",25.0),(15.0,"T","T-15",32.0),
        (18.0,"D","D-18",7.0),(18.0,"F","F-18",10.0),(18.0,"H","H-18",13.0),(18.0,"M","M-18",19.0),(18.0,"R","R-18",25.0),(18.0,"T","T-18",32.0),
        (22.0,"D","D-22",7.5),(22.0,"F","F-22",10.0),(22.0,"H","H-22",13.0),(22.0,"M","M-22",20.0),(22.0,"R","R-22",25.0),(22.0,"T","T-22",32.0),
        (25.0,"D","D-25",7.5),(25.0,"F","F-25",10.5),(25.0,"H","H-25",13.0),(25.0,"M","M-25",20.5),(25.0,"R","R-25",25.0),(25.0,"T","T-25",32.0),
        (28.0,"D","D-28",7.5),(28.0,"F","F-28",10.5),(28.0,"H","H-28",13.5),(28.0,"M","M-28",21.0),(28.0,"R","R-28",25.0),(28.0,"T","T-28",33.5),
        (32.0,"M","M-32",21.5),(32.0,"R","R-32",27.0),
        (35.0,"F","F-35",11.0),(35.0,"H","H-35",14.0),(35.0,"M","M-35",21.5),(35.0,"R","R-35",27.0),(35.0,"T","T-35",35.0),
        (38.0,"M","M-38",22.0),(38.0,"R","R-38",27.0),
        (42.0,"F","F-42",11.0),(42.0,"H","H-42",14.5),(42.0,"M","M-42",22.0),(42.0,"R","R-42",27.0),(42.0,"T","T-42",36.5),
        (48.0,"F","F-48",11.0),(48.0,"H","H-48",14.5),(48.0,"M","M-48",22.5),(48.0,"R","R-48",27.5),(48.0,"T","T-48",37.5),
        (54.0,"F","F-54",11.5),(54.0,"H","H-54",14.5),(54.0,"M","M-54",23.0),(54.0,"R","R-54",28.5),(54.0,"T","T-54",38.0),
        (60.0,"F","F-60",11.5),(60.0,"H","H-60",15.0),(60.0,"M","M-60",23.5),(60.0,"R","R-60",29.0),(60.0,"T","T-60",39.0),
        (64.0,"F","F-64",11.5),(64.0,"H","H-64",15.0),(64.0,"M","M-64",23.5),(64.0,"R","R-64",29.0),(64.0,"T","T-64",39.5),
        (76.2,"F","F-76",11.5),(76.2,"H","H-76",15.0),(76.2,"M","M-76",24.0),(76.2,"R","R-76",30.0),(76.2,"T","T-76",40.5),
        (80.0,"F","F-80",11.5),(80.0,"H","H-80",15.5),(80.0,"M","M-80",24.5),(80.0,"R","R-80",30.5),(80.0,"T","T-80",41.0),
        (88.9,"F","F-89",11.5),(88.9,"H","H-89",15.5),(88.9,"M","M-89",24.5),(88.9,"R","R-89",30.5),(88.9,"T","T-89",41.5),
        (101.6,"F","F-102",11.5),(101.6,"H","H-102",15.5),(101.6,"M","M-102",25.0),(101.6,"R","R-102",31.5),(101.6,"T","T-102",42.5),
    ]

    # Busca fabricante Armacel
    r = await db.execute(text("SELECT id FROM fabricante WHERE nome = 'Armacel'"))
    row = r.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Fabricante 'Armacel' não encontrado.")
    fab_id = row[0]

    inseridos = 0
    for diam, padrao, ref, esp in DADOS:
        await db.execute(text("""
            INSERT INTO isolamento_tubulacao
              (fabricante_id, diametro_cu_mm, padrao, referencia, espessura_mm, custo)
            VALUES (:fab, :d, :p, :r, :e, 0)
            ON CONFLICT (fabricante_id, padrao, referencia) DO UPDATE
              SET diametro_cu_mm=EXCLUDED.diametro_cu_mm, espessura_mm=EXCLUDED.espessura_mm
        """), {"fab": fab_id, "d": diam, "p": padrao, "r": ref, "e": esp})
        inseridos += 1

    await db.commit()
    r = await db.execute(text("SELECT COUNT(*) FROM isolamento_tubulacao"))
    return {"status": "sucesso", "processados": inseridos, "total": r.scalar()}


@router.post("/fix-sequences")
async def fix_sequences(token: str, db: AsyncSession = Depends(get_db)):
    """Reseta todas as sequências de autoincremento para o valor correto."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    tabelas = [
        "componente_tecnico", "performance_componente",
        "isolamento_tubulacao", "painel_frigorifico",
        "porta_frigoriifica", "equipamento", "performance_equipamento",
        "categoria", "fabricante", "usuario", "projeto",
    ]
    resultados = {}
    for tabela in tabelas:
        try:
            r = await db.execute(text(
                f"SELECT setval('{tabela}_id_seq', GREATEST((SELECT COALESCE(MAX(id),1) FROM {tabela}), 1))"
            ))
            resultados[tabela] = r.scalar()
        except Exception as e:
            resultados[tabela] = f"erro: {e}"

    await db.commit()
    return {"status": "sucesso", "sequencias": resultados}


@router.post("/fix-componentes-categoria")
async def fix_componentes_categoria(token: str, db: AsyncSession = Depends(get_db)):
    """
    Corrige o vínculo categoria_id dos componentes após renomear as categorias.
    PC2 tinha: id=4 'Separador de Líquido', id=5 'Válvula de Expansão'
    Após fix-categorias: id=4='VET', id=5='Filtro Secador', id=14='Separador de Líquido'
    Precisa mover RAC (id=4→14) e T2 (id=5→4).
    """
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    # Verifica estado atual antes de corrigir
    r = await db.execute(text("""
        SELECT cat.id, cat.nome, COUNT(ct.id) as total
        FROM categoria cat
        LEFT JOIN componente_tecnico ct ON ct.categoria_id = cat.id
        WHERE cat.id IN (4, 5, 14)
        GROUP BY cat.id, cat.nome ORDER BY cat.id
    """))
    antes = [{"id": row[0], "nome": row[1], "componentes": row[2]} for row in r.fetchall()]

    # Move RAC separadores: categoria_id=4 → 14 (Separador de Líquido)
    r1 = await db.execute(text("""
        UPDATE componente_tecnico SET categoria_id = 14
        WHERE categoria_id = 4 AND modelo LIKE 'RAC%'
    """))

    # Move T2 VETs: categoria_id=5 → 4 (Válvula de Expansão Termostática)
    r2 = await db.execute(text("""
        UPDATE componente_tecnico SET categoria_id = 4
        WHERE categoria_id = 5 AND modelo LIKE 'T2%'
    """))

    await db.commit()

    # Verifica estado após correção
    r = await db.execute(text("""
        SELECT cat.id, cat.nome, COUNT(ct.id) as total
        FROM categoria cat
        LEFT JOIN componente_tecnico ct ON ct.categoria_id = cat.id
        WHERE cat.id IN (4, 5, 14)
        GROUP BY cat.id, cat.nome ORDER BY cat.id
    """))
    depois = [{"id": row[0], "nome": row[1], "componentes": row[2]} for row in r.fetchall()]

    return {
        "status": "sucesso",
        "rac_movidos": r1.rowcount,
        "t2_movidos": r2.rowcount,
        "antes": antes,
        "depois": depois
    }


@router.post("/rac-extras")
async def seed_rac_extras(token: str, db: AsyncSession = Depends(get_db)):
    """Insere os 6 modelos RAC de Separador de Líquido maiores via SQL direto."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Token inválido.")

    try:
      return await _rac_extras_impl(db)
    except Exception as e:
      import traceback
      raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


async def _rac_extras_impl(db: AsyncSession):
    # Busca IDs via SQL direto
    r = await db.execute(text("SELECT id FROM categoria WHERE nome = 'Separador de Líquido'"))
    cat_row = r.fetchone()
    if not cat_row:
        raise HTTPException(status_code=404, detail="Categoria 'Separador de Líquido' não encontrada.")
    cat_id = cat_row[0]

    r = await db.execute(text("SELECT id FROM fabricante WHERE nome = 'RAC'"))
    fab_row = r.fetchone()
    if not fab_row:
        raise HTTPException(status_code=404, detail="Fabricante 'RAC' não encontrado.")
    fab_id = fab_row[0]

    MODELOS = [
        ('RAC 1500 1 3/8"',  '1 3/8"',  49020, [("R134a",-30,7224,2924),("R134a",-10,18920,7568),("R134a",5,36980,14792),("R22",-30,15480,6192),("R22",-10,31820,12728),("R22",5,49020,19608),("R404A",-30,15480,6192),("R404A",-10,31820,12728),("R404A",5,49020,19608)]),
        ('RAC 2500 1 5/8"',  '1 5/8"',  79980, [("R134a",-30,10750,4300),("R134a",-10,27520,11008),("R134a",5,52460,20984),("R22",-30,19780,7912),("R22",-10,46440,18576),("R22",5,79980,31992),("R404A",-30,19780,7912),("R404A",-10,46440,18576),("R404A",5,79980,31992)]),
        ('RAC 4500 2 1/8"',  '2 1/8"', 163400, [("R134a",-30,20640,8256),("R134a",-10,55040,22016),("R134a",5,116100,46440),("R22",-30,37840,15136),("R22",-10,98900,39560),("R22",5,163400,65360),("R404A",-30,37840,15136),("R404A",-10,98900,39560),("R404A",5,163400,65360)]),
        ('RAC 9000 2 5/8"',  '2 5/8"', 258000, [("R134a",-30,33540,13416),("R134a",-10,86000,34400),("R134a",5,172000,68800),("R22",-30,61920,24768),("R22",-10,154800,61920),("R22",5,258000,103200),("R404A",-30,61920,24768),("R404A",-10,154800,61920),("R404A",5,258000,103200)]),
        ('RAC 12500 3 1/8"', '3 1/8"', 387000, [("R134a",-30,41280,16512),("R134a",-10,129000,51600),("R134a",5,258000,103200),("R22",-30,94600,37840),("R22",-10,215000,86000),("R22",5,387000,154800),("R404A",-30,94600,37840),("R404A",-10,215000,86000),("R404A",5,387000,154800)]),
        ('RAC 14000 4 1/8"', '4 1/8"', 580500, [("R134a",-30,61920,24768),("R134a",-10,193500,77400),("R134a",5,387000,154800),("R22",-30,141900,56760),("R22",-10,322500,129000),("R22",5,580500,232200),("R404A",-30,141900,56760),("R404A",-10,322500,129000),("R404A",5,580500,232200)]),
    ]

    # Reseta sequências para evitar conflito de ID (dados inseridos com IDs explícitos)
    await db.execute(text(
        "SELECT setval('componente_tecnico_id_seq', (SELECT MAX(id) FROM componente_tecnico))"
    ))
    await db.execute(text(
        "SELECT setval('performance_componente_id_seq', (SELECT MAX(id) FROM performance_componente))"
    ))

    comp_novos = 0; perf_ins = 0

    for modelo, conexao, cap_nom, perfs in MODELOS:
        # Verifica se já existe (busca por modelo apenas, independente de categoria)
        r = await db.execute(text(
            "SELECT id, categoria_id FROM componente_tecnico WHERE modelo=:m"),
            {"m": modelo})
        row = r.fetchone()

        if row:
            # Já existe — atualiza categoria_id se necessário
            comp_id = row[0]
            if row[1] != cat_id:
                await db.execute(text(
                    "UPDATE componente_tecnico SET categoria_id=:c WHERE id=:i"),
                    {"c": cat_id, "i": comp_id})
        else:
            # Não existe — insere
            await db.execute(text("""
                INSERT INTO componente_tecnico
                  (modelo, codigo_fabricante, categoria_id, fabricante_id,
                   conexao_entrada, conexao_saida, capacidade_nominal, dados_especificos, custo)
                VALUES (:modelo, NULL, :cat_id, :fab_id, :cx, :cx, :cap, '{}', 0)
            """), {"modelo": modelo, "cat_id": cat_id, "fab_id": fab_id,
                   "cx": conexao, "cap": float(cap_nom)})
            await db.flush()
            r = await db.execute(text(
                "SELECT id FROM componente_tecnico WHERE modelo=:m"),
                {"m": modelo})
            comp_id = r.fetchone()[0]
            comp_novos += 1

        # Insere performances
        for fluido, t_evap, cap, cap_min in perfs:
            await db.execute(text("""
                INSERT INTO performance_componente
                  (componente_id, fluido, temp_evaporacao, temp_condensacao,
                   capacidade_kcalh, capacidade_min_kcalh)
                VALUES (:cid, :fl, :te, 45, :cap, :cmin)
                ON CONFLICT (componente_id, fluido, temp_evaporacao, temp_condensacao)
                DO UPDATE SET capacidade_kcalh=EXCLUDED.capacidade_kcalh,
                              capacidade_min_kcalh=EXCLUDED.capacidade_min_kcalh
            """), {"cid": comp_id, "fl": fluido, "te": t_evap,
                   "cap": float(cap), "cmin": float(cap_min)})
            perf_ins += 1

    await db.commit()

    r = await db.execute(text(f"SELECT COUNT(*) FROM componente_tecnico WHERE categoria_id={cat_id}"))
    r2 = await db.execute(text(f"SELECT COUNT(*) FROM performance_componente pc JOIN componente_tecnico ct ON ct.id=pc.componente_id WHERE ct.categoria_id={cat_id}"))

    return {"status": "sucesso", "modelos_processados": comp_novos,
            "performances_processadas": perf_ins,
            "total_separadores_liquido": r.scalar(),
            "total_performances": r2.scalar()}
