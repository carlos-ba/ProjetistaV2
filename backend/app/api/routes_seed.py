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
