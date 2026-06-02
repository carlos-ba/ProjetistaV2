-- ============================================================
-- SEED — Dados iniciais para testes do Projetista V2
-- ============================================================

-- ------------------------------------------------------------
-- 1. UNIDADES DE MEDIDA
-- ------------------------------------------------------------
INSERT INTO unidade_medida (id, nome, sigla) VALUES
  (1, 'unidade',        'un'),
  (2, 'metro',          'm'),
  (3, 'metro quadrado', 'm²'),
  (4, 'quilograma',     'kg'),
  (5, 'litro',          'L'),
  (6, 'conjunto',       'cj')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 2. FABRICANTES
-- ------------------------------------------------------------
INSERT INTO fabricante (id, nome) VALUES
  (1, 'Tecumseh'),
  (2, 'Embraco'),
  (3, 'Bitzer'),
  (4, 'Danfoss'),
  (5, 'Parker'),
  (6, 'Elgin'),
  (7, 'Genérico')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 3. CATEGORIAS
-- ------------------------------------------------------------
INSERT INTO categoria (id, nome) VALUES
  (1,  'Condensadora'),
  (2,  'Evaporadora'),
  (3,  'Compressor'),
  (4,  'Válvula de Expansão'),
  (5,  'Filtro Secador'),
  (6,  'Visor de Líquido'),
  (7,  'Válvula Solenoide'),
  (8,  'Pressostato'),
  (9,  'Tubulação de Cobre'),
  (10, 'Isolamento Térmico'),
  (11, 'Material Elétrico'),
  (12, 'Painel Frigorífico'),
  (13, 'Solda e Fluxo')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 4. TIPOS DE PRODUTO TÉRMICO
-- ------------------------------------------------------------
INSERT INTO tipo_produto_termico (id, nome) VALUES
  (1, 'Carnes e Aves'),
  (2, 'Laticínios'),
  (3, 'FLV (Frutas, Legumes e Verduras)'),
  (4, 'Pescados'),
  (5, 'Frios e Embutidos'),
  (6, 'Sorvetes e Congelados'),
  (7, 'Bebidas'),
  (8, 'Padaria e Confeitaria'),
  (9, 'Geral / Industrial')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 5. PERFIS DE PRODUTO TÉRMICO
--    (ponto_congelamento °C | cp_acima | calor_latente | cp_abaixo | taxa_resp W/ton | temp_cons °C | UR % | teor_agua %)
-- ------------------------------------------------------------
INSERT INTO perfil_produto_termico
  (nome, tipo_id, ponto_congelamento, calor_especifico_acima_congelamento,
   calor_latente_congelamento, calor_especifico_abaixo_congelamento,
   taxa_respiracao, temperatura_conservacao, umidade_relativa, teor_agua)
VALUES
  -- Carnes
  ('Carne Bovina',        1, -1.70, 3.52, 249.0, 1.76, NULL,  2.0, 88.0, 74.0),
  ('Carne Suína',         1, -2.00, 3.44, 243.0, 1.72, NULL,  2.0, 85.0, 72.0),
  ('Frango Inteiro',      1, -2.80, 3.31, 246.0, 1.55, NULL, -1.0, 85.0, 66.0),
  ('Carne Congelada',     1, -1.70, 3.52, 249.0, 1.76, NULL,-18.0, 90.0, 74.0),
  -- Laticínios
  ('Queijo Maturado',     2, -10.0, 2.09, 84.0,  1.26, NULL,  6.0, 80.0, 37.0),
  ('Manteiga',            2, -2.30, 2.05, 113.0, 1.26, NULL,  4.0, 80.0, 16.0),
  ('Leite Pasteurizado',  2, -0.60, 3.93, 268.0, 1.93, NULL,  4.0, 85.0, 87.0),
  -- FLV
  ('Alface',              3, -0.20, 3.96, 256.0, 1.97, 62.0,  2.0, 95.0, 95.0),
  ('Tomate Maduro',       3, -0.50, 3.94, 255.0, 1.96, 28.0, 10.0, 90.0, 94.0),
  ('Banana Madura',       3, -0.80, 3.35, 224.0, 1.65, 25.0, 14.0, 90.0, 74.0),
  ('Maçã',                3, -1.50, 3.73, 243.0, 1.84, 10.0,  2.0, 92.0, 84.0),
  ('Batata',              3, -0.60, 3.51, 236.0, 1.77,  9.0,  8.0, 90.0, 77.0),
  -- Pescados
  ('Peixe Fresco',        4, -2.20, 3.76, 258.0, 1.86, NULL,  0.0, 95.0, 76.0),
  ('Camarão Fresco',      4, -2.30, 3.60, 260.0, 1.77, NULL,  0.0, 95.0, 76.0),
  ('Peixe Congelado',     4, -2.20, 3.76, 258.0, 1.86, NULL,-18.0, 90.0, 76.0),
  -- Frios e Embutidos
  ('Presunto Cozido',     5, -3.00, 3.18, 213.0, 1.55, NULL,  4.0, 80.0, 60.0),
  ('Salsicha',            5, -2.50, 3.39, 234.0, 1.68, NULL,  4.0, 80.0, 63.0),
  -- Sorvetes
  ('Sorvete',             6,-14.50, 1.63, 210.0, 1.26, NULL,-18.0, 90.0, 60.0),
  ('Mix de Açaí',         6,-10.00, 2.10, 200.0, 1.30, NULL,-18.0, 90.0, 60.0),
  -- Bebidas
  ('Cerveja Lata',        7, -2.20, 4.02, 268.0, 1.97, NULL,  4.0, 70.0, 92.0),
  ('Refrigerante',        7, -1.00, 4.00, 268.0, 1.97, NULL,  4.0, 70.0, 90.0),
  ('Vinho',               7, -4.20, 3.94, 264.0, 1.95, NULL,  8.0, 70.0, 87.0),
  -- Padaria
  ('Massa Fresca',        8, -3.50, 3.30, 236.0, 1.62, NULL,  4.0, 85.0, 65.0),
  ('Chocolate',           8,-17.60, 1.47, 105.0, 1.05, NULL, 15.0, 50.0, 1.00),
  -- Geral
  ('Produto Genérico +5', 9,  0.00, 3.50, 230.0, 1.75, NULL,  5.0, 80.0, 70.0),
  ('Produto Genérico -18',9, -2.00, 3.50, 230.0, 1.75, NULL,-18.0, 90.0, 70.0)
ON CONFLICT (nome) DO NOTHING;

-- ------------------------------------------------------------
-- 6. EQUIPAMENTOS — Condensadoras/Evaporadoras
-- ------------------------------------------------------------
INSERT INTO equipamento
  (id, categoria_id, modelo, fabricante_id, custo, unidade_medida_id,
   qtde_ventiladores, diametro_ventilador_mm, vazao_ar_m3h, flecha_ar_m)
VALUES
  -- Condensadoras Tecumseh
  (1,  1, 'CAJ2464Z',   1,  1850.00, 1, 1, 300, 1200, 4),
  (2,  1, 'CAJ4519Z',   1,  2300.00, 1, 1, 350, 1800, 5),
  (3,  1, 'CAJ9513Z',   1,  3200.00, 1, 2, 350, 3200, 5),
  (4,  1, 'TAJ4519Z',   1,  4500.00, 1, 2, 400, 4500, 6),
  -- Condensadoras Elgin
  (5,  1, 'CHCB-5000',  6,  2100.00, 1, 1, 350, 2000, 5),
  (6,  1, 'CHCB-8000',  6,  3400.00, 1, 2, 400, 3800, 6),
  (7,  1, 'CHCB-12000', 6,  5200.00, 1, 2, 450, 5500, 7),
  -- Evaporadoras Tecumseh
  (8,  2, 'SILP22',     1,   980.00, 1, 1, 300, 1200, 3),
  (9,  2, 'SILP44',     1,  1450.00, 1, 2, 300, 2400, 3),
  (10, 2, 'SILP66',     1,  1950.00, 1, 2, 350, 3200, 4),
  -- Evaporadoras Elgin
  (11, 2, 'EVAP-3000',  6,   850.00, 1, 1, 300, 1500, 3),
  (12, 2, 'EVAP-6000',  6,  1350.00, 1, 2, 300, 2800, 3),
  (13, 2, 'EVAP-10000', 6,  2100.00, 1, 2, 350, 4500, 4),
  -- Compressores Embraco
  (14, 3, 'EMI30HER',   2,   620.00, 1, 0, 0, 0, 0),
  (15, 3, 'NJ9232GK',   2,   980.00, 1, 0, 0, 0, 0),
  (16, 3, 'NJ2212GK',   2,  1250.00, 1, 0, 0, 0, 0),
  -- Compressores Tecumseh
  (17, 3, 'CAJ2464Z-C', 1,   750.00, 1, 0, 0, 0, 0),
  (18, 3, 'TAJ4519Z-C', 1,  1800.00, 1, 0, 0, 0, 0)
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 7. PERFORMANCE DOS EQUIPAMENTOS
--    R404A e R290 nas temperaturas mais comuns
-- ------------------------------------------------------------
INSERT INTO performance_equipamento
  (equipamento_id, fluido, temp_condensacao, temp_evaporacao, delta_t, capacidade, consumo_w)
VALUES
-- CAJ2464Z — R404A
  (1,'R404A',45,-10,8,2100,680),(1,'R404A',45,-15,8,1700,620),(1,'R404A',45,-20,8,1350,560),
  (1,'R404A',45,-25,8,1050,500),(1,'R404A',45,-30,8, 820,450),
-- CAJ2464Z — R290
  (1,'R290', 45,-10,8,2300,650),(1,'R290', 45,-15,8,1900,590),(1,'R290', 45,-20,8,1500,530),
  (1,'R290', 45,-25,8,1150,470),(1,'R290', 45,-30,8, 900,420),

-- CAJ4519Z — R404A
  (2,'R404A',45,-10,8,3800,1200),(2,'R404A',45,-15,8,3100,1100),(2,'R404A',45,-20,8,2500,980),
  (2,'R404A',45,-25,8,1950,860), (2,'R404A',45,-30,8,1500,750),
-- CAJ4519Z — R290
  (2,'R290', 45,-10,8,4200,1150),(2,'R290', 45,-15,8,3500,1050),(2,'R290', 45,-20,8,2800,940),
  (2,'R290', 45,-25,8,2200,820), (2,'R290', 45,-30,8,1700,710),

-- CAJ9513Z — R404A
  (3,'R404A',45,-10,8,7200,2200),(3,'R404A',45,-15,8,5900,2000),(3,'R404A',45,-20,8,4700,1800),
  (3,'R404A',45,-25,8,3700,1600),(3,'R404A',45,-30,8,2900,1400),
-- CAJ9513Z — R290
  (3,'R290', 45,-10,8,7800,2100),(3,'R290', 45,-15,8,6400,1900),(3,'R290', 45,-20,8,5100,1700),
  (3,'R290', 45,-25,8,4000,1500),(3,'R290', 45,-30,8,3100,1300),

-- TAJ4519Z — R404A
  (4,'R404A',45,-10,8,12000,3800),(4,'R404A',45,-15,8,9800,3400),(4,'R404A',45,-20,8,7800,3000),
  (4,'R404A',45,-25,8,6100,2650),(4,'R404A',45,-30,8,4700,2300),
-- TAJ4519Z — R290
  (4,'R290', 45,-10,8,13000,3600),(4,'R290', 45,-15,8,10700,3200),(4,'R290', 45,-20,8,8500,2800),
  (4,'R290', 45,-25,8,6600,2450),(4,'R290', 45,-30,8,5100,2100),

-- CHCB-5000 — R404A
  (5,'R404A',45,-10,8,3500,1100),(5,'R404A',45,-15,8,2850,1000),(5,'R404A',45,-20,8,2250,890),
  (5,'R404A',45,-25,8,1750,780),(5,'R404A',45,-30,8,1350,680),
-- CHCB-8000 — R404A
  (6,'R404A',45,-10,8,6500,2000),(6,'R404A',45,-15,8,5300,1800),(6,'R404A',45,-20,8,4200,1600),
  (6,'R404A',45,-25,8,3300,1400),(6,'R404A',45,-30,8,2550,1200),
-- CHCB-12000 — R404A
  (7,'R404A',45,-10,8,10500,3200),(7,'R404A',45,-15,8,8600,2900),(7,'R404A',45,-20,8,6800,2600),
  (7,'R404A',45,-25,8,5300,2300),(7,'R404A',45,-30,8,4100,2000),

-- Evaporadoras SILP22 — R404A
  (8,'R404A',45,-10,8,2000,0),(8,'R404A',45,-15,8,1700,0),(8,'R404A',45,-20,8,1400,0),
  (8,'R404A',45,-25,8,1100,0),(8,'R404A',45,-30,8, 850,0),
-- Evaporadoras SILP44 — R404A
  (9,'R404A',45,-10,8,4000,0),(9,'R404A',45,-15,8,3300,0),(9,'R404A',45,-20,8,2650,0),
  (9,'R404A',45,-25,8,2050,0),(9,'R404A',45,-30,8,1600,0),
-- Evaporadoras SILP66 — R404A
  (10,'R404A',45,-10,8,6200,0),(10,'R404A',45,-15,8,5100,0),(10,'R404A',45,-20,8,4100,0),
  (10,'R404A',45,-25,8,3200,0),(10,'R404A',45,-30,8,2450,0),
-- Evaporadoras EVAP-3000 — R404A
  (11,'R404A',45,-10,8,2200,0),(11,'R404A',45,-15,8,1800,0),(11,'R404A',45,-20,8,1450,0),
  (11,'R404A',45,-25,8,1100,0),(11,'R404A',45,-30,8, 850,0),
-- Evaporadoras EVAP-6000 — R404A
  (12,'R404A',45,-10,8,4500,0),(12,'R404A',45,-15,8,3700,0),(12,'R404A',45,-20,8,2950,0),
  (12,'R404A',45,-25,8,2300,0),(12,'R404A',45,-30,8,1750,0),
-- Evaporadoras EVAP-10000 — R404A
  (13,'R404A',45,-10,8,7500,0),(13,'R404A',45,-15,8,6200,0),(13,'R404A',45,-20,8,4950,0),
  (13,'R404A',45,-25,8,3850,0),(13,'R404A',45,-30,8,2950,0)

ON CONFLICT ON CONSTRAINT uq_performance_equipamento DO NOTHING;

-- ------------------------------------------------------------
-- 8. MATERIAIS (tubulação, isolamento, elétrico, etc.)
-- ------------------------------------------------------------
INSERT INTO material
  (nome, categoria_id, fabricante_id, custo, unidade_medida_id,
   diametro_conexao, capacidade_nominal, detalhes_tecnicos)
VALUES
  -- Tubulação de cobre
  ('Tubo Cobre 1/4"',   9, 7,  12.50, 2, '1/4"', 0, '{"bitola":"1/4","esp_mm":0.8}'),
  ('Tubo Cobre 3/8"',   9, 7,  18.00, 2, '3/8"', 0, '{"bitola":"3/8","esp_mm":0.8}'),
  ('Tubo Cobre 1/2"',   9, 7,  24.00, 2, '1/2"', 0, '{"bitola":"1/2","esp_mm":0.9}'),
  ('Tubo Cobre 5/8"',   9, 7,  32.00, 2, '5/8"', 0, '{"bitola":"5/8","esp_mm":0.9}'),
  ('Tubo Cobre 3/4"',   9, 7,  44.00, 2, '3/4"', 0, '{"bitola":"3/4","esp_mm":1.0}'),
  ('Tubo Cobre 7/8"',   9, 7,  58.00, 2, '7/8"', 0, '{"bitola":"7/8","esp_mm":1.0}'),
  ('Tubo Cobre 1.1/8"', 9, 7,  88.00, 2, '1.1/8"', 0, '{"bitola":"1.1/8","esp_mm":1.1}'),
  -- Isolamento
  ('Isolamento 1/4" x 9mm',  10, 7,   8.50, 2, '1/4"',  0, '{"esp_mm":9}'),
  ('Isolamento 3/8" x 9mm',  10, 7,  10.00, 2, '3/8"',  0, '{"esp_mm":9}'),
  ('Isolamento 1/2" x 13mm', 10, 7,  13.00, 2, '1/2"',  0, '{"esp_mm":13}'),
  ('Isolamento 5/8" x 13mm', 10, 7,  16.00, 2, '5/8"',  0, '{"esp_mm":13}'),
  ('Isolamento 3/4" x 19mm', 10, 7,  22.00, 2, '3/4"',  0, '{"esp_mm":19}'),
  ('Isolamento 7/8" x 19mm', 10, 7,  28.00, 2, '7/8"',  0, '{"esp_mm":19}'),
  -- Solda e Fluxo
  ('Solda Riacho 15% 1kg',   13, 7,  85.00, 4, NULL, 0, '{}'),
  ('Fluxo Decapante 500g',   13, 7,  32.00, 4, NULL, 0, '{}'),
  -- Elétrico
  ('Cabo PP 2x1.5mm 100m',   11, 7, 180.00, 6, NULL, 0, '{"secao":"2x1.5"}'),
  ('Cabo PP 2x2.5mm 100m',   11, 7, 280.00, 6, NULL, 0, '{"secao":"2x2.5"}'),
  ('Cabo PP 3x2.5mm 100m',   11, 7, 320.00, 6, NULL, 0, '{"secao":"3x2.5"}'),
  ('Disjuntor 16A',           11, 7,  28.00, 1, NULL, 0, '{"amperes":16}'),
  ('Disjuntor 25A',           11, 7,  35.00, 1, NULL, 0, '{"amperes":25}'),
  ('Disjuntor 32A',           11, 7,  42.00, 1, NULL, 0, '{"amperes":32}'),
  -- Painéis frigoríficos
  ('Painel PUR 75mm m²',     12, 7, 320.00, 3, NULL, 0, '{"esp_mm":75,"nucleo":"PUR"}'),
  ('Painel PUR 100mm m²',    12, 7, 380.00, 3, NULL, 0, '{"esp_mm":100,"nucleo":"PUR"}'),
  ('Painel PIR 75mm m²',     12, 7, 380.00, 3, NULL, 0, '{"esp_mm":75,"nucleo":"PIR"}'),
  ('Painel PIR 100mm m²',    12, 7, 450.00, 3, NULL, 0, '{"esp_mm":100,"nucleo":"PIR"}')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 9. COMPONENTES DE FLUXO
-- ------------------------------------------------------------
INSERT INTO componente_tecnico
  (categoria_id, modelo, codigo_fabricante, fabricante_id,
   conexao_entrada, conexao_saida, capacidade_nominal, dados_especificos, custo)
VALUES
  -- Válvulas de Expansão Termostática (Danfoss)
  (4, 'T2 1/4"',    'R404A-T2',   4, '1/4"', '1/4"',  2500, '{"fluido":"R404A","orificio":"T2"}',   185.00),
  (4, 'T4 3/8"',    'R404A-T4',   4, '3/8"', '3/8"',  5000, '{"fluido":"R404A","orificio":"T4"}',   220.00),
  (4, 'T8 1/2"',    'R404A-T8',   4, '1/2"', '1/2"', 10000, '{"fluido":"R404A","orificio":"T8"}',   280.00),
  (4, 'T2 1/4" R290','R290-T2',   4, '1/4"', '1/4"',  2500, '{"fluido":"R290","orificio":"T2"}',    195.00),
  (4, 'T4 3/8" R290','R290-T4',   4, '3/8"', '3/8"',  5000, '{"fluido":"R290","orificio":"T4"}',    235.00),
  -- Filtros Secadores (Danfoss)
  (5, 'DML 032S',   'DML032S',    4, '1/4"', '1/4"',  3000, '{"volume_cm3":20}',  42.00),
  (5, 'DML 053S',   'DML053S',    4, '3/8"', '3/8"',  6000, '{"volume_cm3":33}',  58.00),
  (5, 'DML 083S',   'DML083S',    4, '1/2"', '1/2"', 12000, '{"volume_cm3":53}',  75.00),
  -- Visores de Líquido (Parker)
  (6, 'SGP 1/4"',   'SGP14',      5, '1/4"', '1/4"',  3000, '{"indicador_umidade":true}', 55.00),
  (6, 'SGP 3/8"',   'SGP38',      5, '3/8"', '3/8"',  6000, '{"indicador_umidade":true}', 68.00),
  (6, 'SGP 1/2"',   'SGP12',      5, '1/2"', '1/2"', 12000, '{"indicador_umidade":true}', 85.00),
  -- Válvulas Solenoides (Danfoss)
  (7, 'EVR 3 1/4"', 'EVR3-14',    4, '1/4"', '1/4"',  3000, '{"tensao":"220V"}', 145.00),
  (7, 'EVR 6 3/8"', 'EVR6-38',    4, '3/8"', '3/8"',  6000, '{"tensao":"220V"}', 175.00),
  (7, 'EVR10 1/2"', 'EVR10-12',   4, '1/2"', '1/2"', 12000, '{"tensao":"220V"}', 215.00),
  -- Presostatos (Danfoss)
  (8, 'KP5 Alta',   'KP5',        4, '1/4"', '1/4"', 15000, '{"tipo":"alta_pressao","ajuste_bar":"12-30"}', 185.00),
  (8, 'KP1 Baixa',  'KP1',        4, '1/4"', '1/4"', 15000, '{"tipo":"baixa_pressao","ajuste_bar":"0.2-7"}', 165.00)
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- Ajustar sequences para evitar conflito de IDs futuros
-- ------------------------------------------------------------
SELECT setval('unidade_medida_id_seq',  (SELECT MAX(id) FROM unidade_medida));
SELECT setval('fabricante_id_seq',      (SELECT MAX(id) FROM fabricante));
SELECT setval('categoria_id_seq',       (SELECT MAX(id) FROM categoria));
SELECT setval('tipo_produto_termico_id_seq', (SELECT MAX(id) FROM tipo_produto_termico));
SELECT setval('equipamento_id_seq',     (SELECT MAX(id) FROM equipamento));
SELECT setval('material_id_seq',        (SELECT MAX(id) FROM material));
