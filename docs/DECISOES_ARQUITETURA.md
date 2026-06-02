# Decisões de Arquitetura — Projetista V2

Registro das decisões técnicas tomadas durante o desenvolvimento.
Serve de referência para implementações futuras.

---

## 1. Catálogo Global × Catálogo da Empresa

**Data:** 2026-06-01
**Decisão:** Separar catálogo técnico global do catálogo personalizado por empresa.

### Estrutura planejada (implementar na Fase 2 — Admin)

```
equipamento (global — gerenciado pelo admin SaaS)
    → dados técnicos, performance, fabricante

equipamento_empresa (por tenant — gerenciado pelo cliente)
    → equipamento_id (FK)
    → empresa_id (FK)
    → codigo_interno      (código da empresa)
    → codigo_fornecedor   (código do distribuidor)
    → custo               (preço negociado)
    → fornecedor
    → observacao
    → ativo
```

Mesma lógica para `componente_empresa`.

**Motivo:** cada cliente SaaS tem seus próprios códigos internos, fornecedores e preços negociados. O catálogo técnico é compartilhado e gerenciado centralmente.

**Quando implementar:** Fase 2 — Admin panel, junto com multi-tenancy.

---

## 2. Preço no Orçamento, não no Catálogo

**Data:** 2026-06-01
**Decisão:** O campo `custo` no catálogo é apenas um preço de referência (base).
O preço real fica no item do orçamento, editável pelo técnico por projeto.

```
catalogo.custo         → preço base (sugestão)
item_orcamento.valor   → preço real (editável por projeto)
```

**Motivo:** preço varia por projeto, cliente, data e negociação.

---

## 3. Unidades ASHRAE no Banco

**Data:** 2026-06-01
**Decisão:** Todos os dados termodinâmicos seguem o padrão SI do ASHRAE.

| Campo | Unidade | Referência |
|---|---|---|
| `calor_especifico_*` | kJ/(kg·K) | ASHRAE Cap. 19 |
| `calor_latente_congelamento` | kJ/kg | ASHRAE Cap. 19 |
| `taxa_respiracao` | W/tonne | ASHRAE Cap. 19 |
| `capacidade` (equipamento) | kcal/h | Padrão de mercado BR |
| `consumo_kw` | kW | Padrão de mercado BR |
| `temp_condensacao` | °C (T.Amb direto) | Padrão de mercado BR |

**Conversões aplicadas no serviço:**
- kJ → kcal: `× (1/4.184)`
- W → kcal/h: `× 0.86`
- W/tonne → kcal/h: `(mov_kg/1000) × taxa × 0.86`

---

## 4. Campo `temp_condensacao` guarda Temperatura Ambiente

**Data:** 2026-06-01
**Decisão:** O campo `temp_condensacao` na tabela `performance_equipamento`
armazena a **temperatura ambiente (T.Amb)** conforme publicado nos catálogos
técnicos dos fabricantes (Elgin, Tecumseh, etc.).

**Motivo:** padrão de mercado brasileiro. Os fabricantes publicam as curvas
de capacidade por temperatura ambiente, não por temperatura de condensação.

**Regra para cálculos futuros:**
Quando um cálculo precisar da temperatura de condensação real (T.Cond),
ela NÃO deve ser assumida — deve ser calculada no momento do uso com:

```
T.Cond = T.Amb + ΔT_condensação
```

O valor de ΔT deve ser **informado pelo usuário ou pelo contexto do projeto**
(tipicamente 8°C a 15°C dependendo do tipo de condensador e condições locais).
Nunca assumir um ΔT fixo sem solicitação explícita.

---

## 5. Infiltração — Dois Métodos

**Data:** 2026-06-01
**Decisão:** Disponibilizar dois métodos de cálculo de infiltração.

| Método | Quando usar |
|---|---|
| **Simplificado** | Projetos rápidos, câmaras convencionais |
| **Psicrométrico** | Projetos críticos, câmaras em regiões muito quentes/úmidas |

Método psicrométrico usa fórmula de Magnus para pressão de saturação
e equação ASHRAE Fundamentals Cap.1 para entalpia do ar úmido.

---

## 6. Categoria = Formulário Próprio no Admin

**Data:** 2026-06-01
**Decisão:** Cada categoria de equipamento/componente terá seu formulário
de cadastro específico no Admin panel.

| Categoria | Campos específicos |
|---|---|
| Unidade Condensadora | T.Amb range, fluidos, qt_vent, vazao |
| Evaporadora | T.Evap range, fluidos, qt_vent, vazao, flecha |
| Compressor | Tipo (hermético/semi), cilindrada, fluidos |
| Válvula de Expansão Termostática | Fluido, orifício, conexão, faixa cap. |
| Filtro Secador | Volume cm³, tipo núcleo, conexão |
| Válvula Solenoide | Tensão, conexão, capacidade |
| Pressostato | Tipo (alta/baixa), faixa de ajuste |

**Quando implementar:** Fase 2 — Admin panel.

---

## 7. Dados de Seed vs Dados Reais

**Data:** 2026-06-01
**Decisão:** Banco deve conter apenas dados reais de catálogos de fabricantes.
Dados de seed foram removidos. Exceção: perfis termodinâmicos ASHRAE
(Carne Bovina, Frango, FLV etc.) que são dados técnicos validados,
não estimativas.
