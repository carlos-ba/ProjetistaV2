# Guia de Cadastro — Banco de Dados Projetista V2

Este guia explica cada tabela, seus campos e como popular com dados reais.
A ordem de cadastro deve seguir as dependências (tabelas base primeiro).

---

## ORDEM OBRIGATÓRIA DE CADASTRO

```
1. unidade_medida          → sem dependências
2. fabricante              → sem dependências
3. categoria               → sem dependências
4. tipo_produto_termico    → sem dependências
5. perfil_produto_termico  → depende de tipo_produto_termico
6. equipamento             → depende de categoria, fabricante, unidade_medida
7. performance_equipamento → depende de equipamento
8. material                → depende de categoria, fabricante, unidade_medida
9. componente_tecnico      → depende de categoria, fabricante
10. performance_componente → depende de componente_tecnico
```

---

## 1. TABELA: `unidade_medida`

Unidades usadas em equipamentos e materiais.

| Campo | Tipo        | Obrigatório | Descrição |
|-------|-------------|-------------|-----------|
| id    | inteiro     | auto        | Gerado automaticamente |
| nome  | texto (50)  | ✅          | Nome completo da unidade |
| sigla | texto (10)  | ✅          | Abreviação |

### Exemplos reais:
```sql
INSERT INTO unidade_medida (nome, sigla) VALUES
  ('unidade',        'un'),
  ('metro',          'm'),
  ('metro quadrado', 'm²'),
  ('quilograma',     'kg'),
  ('litro',          'L'),
  ('conjunto',       'cj'),
  ('par',            'par');
```

---

## 2. TABELA: `fabricante`

Fabricantes de equipamentos, materiais e componentes.

| Campo | Tipo        | Obrigatório | Descrição |
|-------|-------------|-------------|-----------|
| id    | inteiro     | auto        | Gerado automaticamente |
| nome  | texto (100) | ✅ único    | Nome do fabricante |

### Exemplos reais:
```sql
INSERT INTO fabricante (nome) VALUES
  ('Tecumseh'),
  ('Embraco'),
  ('Bitzer'),
  ('Danfoss'),
  ('Parker'),
  ('Elgin'),
  ('Copeland'),
  ('Heatcraft'),
  ('Hussmann'),
  ('Friga-Bohn'),
  ('Genérico');
```

---

## 3. TABELA: `categoria`

Categorias de equipamentos, materiais e componentes.

| Campo | Tipo        | Obrigatório | Descrição |
|-------|-------------|-------------|-----------|
| id    | inteiro     | auto        | Gerado automaticamente |
| nome  | texto (100) | ✅ único    | Nome da categoria |

### Exemplos reais:
```sql
INSERT INTO categoria (nome) VALUES
  -- Equipamentos
  ('Condensadora'),
  ('Evaporadora'),
  ('Compressor'),
  -- Componentes de fluxo
  ('Válvula de Expansão'),
  ('Filtro Secador'),
  ('Visor de Líquido'),
  ('Válvula Solenoide'),
  ('Pressostato'),
  -- Materiais
  ('Tubulação de Cobre'),
  ('Isolamento Térmico'),
  ('Material Elétrico'),
  ('Painel Frigorífico'),
  ('Solda e Fluxo'),
  ('Acessórios de Instalação');
```

---

## 4. TABELA: `tipo_produto_termico`

Grupos de produtos para cálculo de carga térmica.

| Campo | Tipo        | Obrigatório | Descrição |
|-------|-------------|-------------|-----------|
| id    | inteiro     | auto        | Gerado automaticamente |
| nome  | texto (100) | ✅ único    | Nome do tipo/grupo |

### Exemplos reais:
```sql
INSERT INTO tipo_produto_termico (nome) VALUES
  ('Carnes e Aves'),
  ('Laticínios'),
  ('FLV (Frutas, Legumes e Verduras)'),
  ('Pescados'),
  ('Frios e Embutidos'),
  ('Sorvetes e Congelados'),
  ('Bebidas'),
  ('Padaria e Confeitaria'),
  ('Geral / Industrial');
```

---

## 5. TABELA: `perfil_produto_termico`

Dados termodinâmicos de cada produto para o cálculo de carga térmica.
**Depende de:** `tipo_produto_termico`

| Campo                                | Tipo           | Obrigatório | Descrição |
|--------------------------------------|----------------|-------------|-----------|
| id                                   | inteiro        | auto        | Gerado automaticamente |
| nome                                 | texto (100)    | ✅ único    | Nome do produto |
| tipo_id                              | inteiro        | ✅          | FK → tipo_produto_termico.id |
| ponto_congelamento                   | decimal(5,2)   | ✅          | °C — ex: -1.70 para carne bovina |
| calor_especifico_acima_congelamento  | decimal(6,4)   | ✅          | kJ/kg·°C acima do ponto de congelamento |
| calor_latente_congelamento           | decimal(6,2)   | ✅          | kJ/kg — calor latente de congelamento |
| calor_especifico_abaixo_congelamento | decimal(6,4)   | ✅          | kJ/kg·°C abaixo do ponto de congelamento |
| taxa_respiracao                      | decimal(10,4)  | opcional    | W/tonelada — apenas FLV e frutas |
| temperatura_conservacao              | decimal(5,2)   | opcional    | °C ideal de armazenamento |
| umidade_relativa                     | decimal(5,2)   | opcional    | % de UR ideal |
| teor_agua                            | decimal(5,2)   | opcional    | % de água no produto |

### Exemplos reais (valores técnicos ASHRAE):
```sql
-- tipo_id: 1=Carnes, 2=Laticínios, 3=FLV, 4=Pescados, 5=Frios, 6=Sorvetes, 7=Bebidas
INSERT INTO perfil_produto_termico
  (nome, tipo_id, ponto_congelamento,
   calor_especifico_acima_congelamento, calor_latente_congelamento,
   calor_especifico_abaixo_congelamento,
   taxa_respiracao, temperatura_conservacao, umidade_relativa, teor_agua)
VALUES
  ('Carne Bovina',    1, -1.70, 3.52, 249.0, 1.76, NULL,  2.0, 88.0, 74.0),
  ('Carne Suína',     1, -2.00, 3.44, 243.0, 1.72, NULL,  2.0, 85.0, 72.0),
  ('Frango Inteiro',  1, -2.80, 3.31, 246.0, 1.55, NULL, -1.0, 85.0, 66.0),
  ('Alface',          3, -0.20, 3.96, 256.0, 1.97, 62.0,  2.0, 95.0, 95.0),
  ('Tomate Maduro',   3, -0.50, 3.94, 255.0, 1.96, 28.0, 10.0, 90.0, 94.0),
  ('Cerveja Lata',    7, -2.20, 4.02, 268.0, 1.97, NULL,  4.0, 70.0, 92.0),
  ('Sorvete',         6,-14.50, 1.63, 210.0, 1.26, NULL,-18.0, 90.0, 60.0);
```

---

## 6. TABELA: `equipamento`

Cadastro dos equipamentos (condensadoras, evaporadoras, compressores).
**Depende de:** `categoria`, `fabricante`, `unidade_medida`

| Campo                  | Tipo        | Obrigatório | Descrição |
|------------------------|-------------|-------------|-----------|
| id                     | inteiro     | auto        | Gerado automaticamente |
| modelo                 | texto (100) | ✅          | Código/modelo do equipamento |
| categoria_id           | inteiro     | ✅          | FK → categoria.id |
| fabricante_id          | inteiro     | ✅          | FK → fabricante.id |
| unidade_medida_id      | inteiro     | ✅          | FK → unidade_medida.id (use id=1 = 'unidade') |
| custo                  | decimal     | ✅          | Preço de venda em R$ |
| qtde_ventiladores      | inteiro     | ✅          | Número de ventiladores (0 para compressores) |
| diametro_ventilador_mm | inteiro     | ✅          | Diâmetro do ventilador em mm (0 se não tiver) |
| vazao_ar_m3h           | inteiro     | ✅          | Vazão de ar em m³/h (0 se não tiver) |
| flecha_ar_m            | inteiro     | ✅          | Alcance do ar em metros (0 se não tiver) |

### Exemplos reais:
```sql
-- categoria_id: 1=Condensadora, 2=Evaporadora, 3=Compressor
-- fabricante_id: 1=Tecumseh, 2=Embraco, 6=Elgin
-- unidade_medida_id: 1=unidade

INSERT INTO equipamento
  (modelo, categoria_id, fabricante_id, unidade_medida_id, custo,
   qtde_ventiladores, diametro_ventilador_mm, vazao_ar_m3h, flecha_ar_m)
VALUES
  -- Condensadoras
  ('CAJ2464Z',   1, 1, 1,  1850.00, 1, 300, 1200, 4),
  ('CAJ4519Z',   1, 1, 1,  2300.00, 1, 350, 1800, 5),
  ('CHCB-5000',  1, 6, 1,  2100.00, 1, 350, 2000, 5),
  -- Evaporadoras
  ('SILP22',     2, 1, 1,   980.00, 1, 300, 1200, 3),
  ('EVAP-3000',  2, 6, 1,   850.00, 1, 300, 1500, 3),
  -- Compressores (sem ventilador)
  ('NJ9232GK',   3, 2, 1,   980.00, 0, 0, 0, 0);
```

---

## 7. TABELA: `performance_equipamento`

Curvas de performance do equipamento por fluido e temperatura.
**Depende de:** `equipamento`
⚠️ **Combinação única:** equipamento_id + fluido + temp_condensacao + temp_evaporacao + delta_t

| Campo            | Tipo         | Obrigatório | Descrição |
|------------------|--------------|-------------|-----------|
| id               | inteiro      | auto        | Gerado automaticamente |
| equipamento_id   | inteiro      | ✅          | FK → equipamento.id |
| fluido           | texto (20)   | ✅          | Ex: 'R404A', 'R290', 'R22', 'R448A' |
| temp_condensacao | inteiro      | ✅ (def:45) | °C — temperatura de condensação |
| temp_evaporacao  | inteiro      | ✅          | °C — temperatura de evaporação |
| delta_t          | decimal(4,1) | ✅ (def:0)  | °C — diferencial de temperatura do evaporador |
| capacidade       | inteiro      | ✅          | kcal/h — capacidade frigorífica |
| consumo_w        | inteiro      | opcional    | W — consumo elétrico (0 para evaporadoras) |

### Exemplos reais (use dados do catálogo do fabricante):
```sql
-- Para o equipamento CAJ2464Z (id=1), fluido R404A, condensação 45°C
INSERT INTO performance_equipamento
  (equipamento_id, fluido, temp_condensacao, temp_evaporacao, delta_t, capacidade, consumo_w)
VALUES
  (1, 'R404A', 45, -10, 8, 2100, 680),
  (1, 'R404A', 45, -15, 8, 1700, 620),
  (1, 'R404A', 45, -20, 8, 1350, 560),
  (1, 'R404A', 45, -25, 8, 1050, 500),
  (1, 'R404A', 45, -30, 8,  820, 450),
  -- Mesmo equipamento com R290
  (1, 'R290',  45, -10, 8, 2300, 650),
  (1, 'R290',  45, -15, 8, 1900, 590),
  (1, 'R290',  45, -20, 8, 1500, 530);
```

### Temperaturas de evaporação sugeridas por aplicação:
| Aplicação | Temp. Interna | Temp. Evaporação típica |
|-----------|--------------|------------------------|
| Resfriado +2°C a +8°C | +5°C | -10°C |
| Frios 0°C a +4°C | +2°C | -15°C |
| Congelados -18°C | -18°C | -25°C a -30°C |

---

## 8. TABELA: `material`

Materiais usados na instalação (tubos, isolamento, elétrico, painéis).
**Depende de:** `categoria`, `fabricante`, `unidade_medida`

| Campo              | Tipo        | Obrigatório | Descrição |
|--------------------|-------------|-------------|-----------|
| id                 | inteiro     | auto        | Gerado automaticamente |
| nome               | texto (200) | ✅          | Descrição do material |
| categoria_id       | inteiro     | ✅          | FK → categoria.id |
| fabricante_id      | inteiro     | opcional    | FK → fabricante.id |
| unidade_medida_id  | inteiro     | ✅          | FK → unidade_medida.id |
| custo              | decimal     | ✅          | Preço unitário em R$ |
| diametro_conexao   | texto (50)  | opcional    | Ex: '3/8"', '1/2"', '5/8"' |
| capacidade_nominal | decimal     | ✅ (def:0)  | Capacidade técnica (0 se não aplicável) |
| detalhes_tecnicos  | JSON        | ✅ (def:{}) | Dados extras em formato JSON |

### Exemplos reais:
```sql
-- categoria_id: 9=Tubulação, 10=Isolamento, 11=Elétrico, 12=Painel, 13=Solda
-- unidade_medida_id: 2=metro, 3=m², 4=kg, 1=unidade

INSERT INTO material
  (nome, categoria_id, fabricante_id, custo, unidade_medida_id,
   diametro_conexao, capacidade_nominal, detalhes_tecnicos)
VALUES
  -- Tubulação (por metro)
  ('Tubo Cobre 1/4"',   9, NULL, 12.50, 2, '1/4"', 0, '{"bitola":"1/4","esp_mm":0.8}'),
  ('Tubo Cobre 3/8"',   9, NULL, 18.00, 2, '3/8"', 0, '{"bitola":"3/8","esp_mm":0.8}'),
  ('Tubo Cobre 1/2"',   9, NULL, 24.00, 2, '1/2"', 0, '{"bitola":"1/2","esp_mm":0.9}'),
  ('Tubo Cobre 5/8"',   9, NULL, 32.00, 2, '5/8"', 0, '{"bitola":"5/8","esp_mm":0.9}'),
  ('Tubo Cobre 3/4"',   9, NULL, 44.00, 2, '3/4"', 0, '{"bitola":"3/4","esp_mm":1.0}'),
  -- Isolamento (por metro)
  ('Isolamento 3/8" 9mm', 10, NULL, 10.00, 2, '3/8"', 0, '{"esp_mm":9}'),
  ('Isolamento 1/2" 13mm',10, NULL, 13.00, 2, '1/2"', 0, '{"esp_mm":13}'),
  -- Painel (por m²)
  ('Painel PUR 100mm',  12, NULL, 380.00, 3, NULL, 0, '{"esp_mm":100,"nucleo":"PUR"}'),
  ('Painel PIR 100mm',  12, NULL, 450.00, 3, NULL, 0, '{"esp_mm":100,"nucleo":"PIR"}'),
  -- Solda (por kg)
  ('Solda Riacho 15%',  13, NULL,  85.00, 4, NULL, 0, '{"liga":"15%"}');
```

---

## 9. TABELA: `componente_tecnico`

Componentes do sistema frigorífico (válvulas, filtros, visores, etc).
**Depende de:** `categoria`, `fabricante`

| Campo              | Tipo        | Obrigatório | Descrição |
|--------------------|-------------|-------------|-----------|
| id                 | inteiro     | auto        | Gerado automaticamente |
| modelo             | texto (100) | ✅          | Código/modelo do componente |
| categoria_id       | inteiro     | ✅          | FK → categoria.id |
| fabricante_id      | inteiro     | ✅          | FK → fabricante.id |
| codigo_fabricante  | texto (50)  | opcional    | Código oficial do fabricante |
| conexao_entrada    | texto (20)  | ✅          | Ex: '3/8"', '1/2"', 'Solda 1/2"' |
| conexao_saida      | texto (20)  | ✅          | Ex: '3/8"', '1/2"' |
| capacidade_nominal | decimal     | ✅ (def:0)  | kcal/h máximo do componente |
| custo              | decimal     | ✅ (def:0)  | Preço em R$ |
| dados_especificos  | JSON        | ✅ (def:{}) | Dados técnicos extras |

### Exemplos reais:
```sql
-- categoria_id: 4=VET, 5=Filtro, 6=Visor, 7=Solenoide, 8=Pressostato
-- fabricante_id: 4=Danfoss, 5=Parker

INSERT INTO componente_tecnico
  (modelo, categoria_id, fabricante_id, codigo_fabricante,
   conexao_entrada, conexao_saida, capacidade_nominal, custo, dados_especificos)
VALUES
  -- Válvulas de Expansão Termostática
  ('T2 R404A 1/4"', 4, 4, 'T2-R404A', '1/4"', '1/4"',  2500, 185.00, '{"fluido":"R404A"}'),
  ('T4 R404A 3/8"', 4, 4, 'T4-R404A', '3/8"', '3/8"',  5000, 220.00, '{"fluido":"R404A"}'),
  ('T8 R404A 1/2"', 4, 4, 'T8-R404A', '1/2"', '1/2"', 10000, 280.00, '{"fluido":"R404A"}'),
  -- Filtros Secadores
  ('DML 032S',      5, 4, 'DML032S',  '1/4"', '1/4"',  3000,  42.00, '{"volume_cm3":20}'),
  ('DML 053S',      5, 4, 'DML053S',  '3/8"', '3/8"',  6000,  58.00, '{"volume_cm3":33}'),
  -- Visores de Líquido
  ('SGP 3/8"',      6, 5, 'SGP38',    '3/8"', '3/8"',  6000,  68.00, '{"indicador_umidade":true}'),
  -- Válvulas Solenoides
  ('EVR 6 3/8"',    7, 4, 'EVR6-38',  '3/8"', '3/8"',  6000, 175.00, '{"tensao":"220V"}'),
  -- Presostatos
  ('KP5 Alta',      8, 4, 'KP5',      '1/4"', '1/4"', 15000, 185.00, '{"tipo":"alta_pressao"}'),
  ('KP1 Baixa',     8, 4, 'KP1',      '1/4"', '1/4"', 15000, 165.00, '{"tipo":"baixa_pressao"}');
```

---

## 10. TABELA: `performance_componente`

Capacidade dos componentes por fluido e temperatura.
**Depende de:** `componente_tecnico`
⚠️ **Combinação única:** componente_id + fluido + temp_evaporacao + temp_condensacao

| Campo                | Tipo         | Obrigatório | Descrição |
|----------------------|--------------|-------------|-----------|
| id                   | inteiro      | auto        | Gerado automaticamente |
| componente_id        | inteiro      | ✅          | FK → componente_tecnico.id |
| fluido               | texto (20)   | ✅          | Ex: 'R404A', 'R290' |
| temp_evaporacao      | inteiro      | ✅          | °C |
| temp_condensacao     | inteiro      | ✅ (def:45) | °C |
| capacidade_kcalh     | decimal      | ✅          | kcal/h máximo nessa condição |
| capacidade_min_kcalh | decimal      | ✅ (def:0)  | kcal/h mínimo (0 se não aplicável) |

### Exemplo:
```sql
-- Válvula T4 R404A (id=2)
INSERT INTO performance_componente
  (componente_id, fluido, temp_evaporacao, temp_condensacao, capacidade_kcalh, capacidade_min_kcalh)
VALUES
  (2, 'R404A', -10, 45, 6000, 500),
  (2, 'R404A', -15, 45, 5200, 450),
  (2, 'R404A', -20, 45, 4500, 400),
  (2, 'R404A', -25, 45, 3800, 350);
```

---

## SCRIPT COMPLETO PARA LIMPAR E RECARREGAR

Se quiser apagar tudo e começar do zero:

```sql
-- CUIDADO: apaga todos os dados do catálogo
TRUNCATE TABLE performance_componente, componente_tecnico,
               performance_equipamento, equipamento,
               material, perfil_produto_termico,
               tipo_produto_termico, categoria,
               fabricante, unidade_medida
CASCADE;

-- Depois rode seu novo seed_dados.sql
```

---

## DICA: Como verificar os IDs existentes

```sql
-- Ver categorias e seus IDs
SELECT id, nome FROM categoria ORDER BY id;

-- Ver fabricantes e seus IDs
SELECT id, nome FROM fabricante ORDER BY id;

-- Ver unidades de medida
SELECT id, nome, sigla FROM unidade_medida ORDER BY id;

-- Ver tipos de produto
SELECT id, nome FROM tipo_produto_termico ORDER BY id;
```
