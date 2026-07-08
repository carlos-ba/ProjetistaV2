# 03 - Banco de Dados

Atualizado em: 2026-06-28

---

## 1. Tecnologia

- **PostgreSQL 17** (local porta 5432 / Render managed em produção)
- **Driver:** psycopg3 (`psycopg[binary]`) — string: `postgresql+psycopg://`
- **ORM:** SQLAlchemy 2.0 async (`AsyncSession`)
- **Migrations:** Alembic (0001 → 0016)

---

## 2. Tabelas

### Autenticação e Usuários

| Tabela | Descrição |
|--------|-----------|
| `usuario` | Usuários do sistema — e-mail, senha hash, verificação de e-mail |

---

### Projetos e Clientes

| Tabela | Campos principais | Descrição |
|--------|-------------------|-----------|
| `projeto` | `id`, `nome`, `usuario_id`, `cliente_id`, `dados_completos` (JSONB) | Estado completo de todos os cards salvo em JSON |
| `cliente` | `id`, `nome`, `email`, `telefone`, `endereco` | Clientes vinculados a projetos |

O campo `dados_completos` armazena o estado serializado de cada card para permitir salvar/carregar projetos com invalidação em cascata.

---

### Catálogo Técnico (global — gerenciado pelo admin SaaS)

| Tabela | Descrição |
|--------|-----------|
| `fabricante` | Danfoss, Kingspan, Elgin, Tecumseh, etc. |
| `categoria` | Condensadora, Evaporadora, VET, Filtro, Solenoide, Separador, etc. |
| `unidade_medida` | un, m, kg, m² |
| `equipamento` | Unidades condensadoras e evaporadoras (modelo, conexões, volume interno) |
| `performance_equipamento` | Capacidade (kcal/h) e consumo (kW) por fluido / T.Evap / T.Amb |
| `componente_tecnico` | VET, separadores de líquido e óleo (modelo, conexão, capacidade) |
| `performance_componente` | Capacidade dos componentes por fluido / T.Evap / T.Cond |
| `painel_frigorifico` | Painéis PIR Kingspan Isoeste (núcleo, espessura, largura) |
| `porta_frigoriifica` | Portas frigoríficas (dimensões, trilhos, fabricante) |
| `isolamento_tubulacao` | Espuma Armacel por bitola e padrão (D/F/H/M/R/T) — 97 registros |
| `perfil_produto_termico` | Dados termodinâmicos ASHRAE por produto (carne, frango, FLV, etc.) — 26 registros |
| `peso_tubo_cobre` | Peso por metro de tubo de cobre por bitola e espessura de parede |

---

### Fluxo de Cotação e Proposta

| Tabela | Descrição |
|--------|-----------|
| `cotacao` | Planilha Excel enviada ao fornecedor (header + itens) |
| `proposta` | Proposta comercial PDF gerada com preços importados |

---

### Configurações

| Tabela | Descrição |
|--------|-----------|
| `configuracao_montagem` | Perfis de montagem por usuário: tipo de filtro preferido, visor, trechos padrão, flags de inclusão de componentes |

---

## 3. Migrations (Alembic)

| Versão | Conteúdo |
|--------|---------|
| 0001 | Schema completo v2 (todas as tabelas base) |
| 0002 | Campo de verificação de e-mail no usuário |
| 0003 | Campo `consumo_kw` em performance_equipamento |
| 0004 | Campo `temp_ambiente` em performance_equipamento |
| 0005 | Tabela `painel_frigorifico` (Kingspan PIR) |
| 0006 | Tabela `isolamento_tubulacao` |
| 0007 | Tabela `porta_frigoriifica` |
| 0008 | Tabela `cotacao` com fornecedor |
| 0009 | Tabela `proposta` comercial PDF |
| 0010 | Campo `volume_conexoes` em equipamento |
| 0011 | Conexões em condensadoras |
| 0012 | Tabela `configuracao_montagem` |
| 0013 | Flags de inclusão em `configuracao_montagem` |
| 0014 | Tabela `cliente` |
| 0015 | Tabela `peso_tubo_cobre` |
| 0016 | Campo `qtde_metros` em cotacao_item |

---

## 4. Observações Técnicas

### Campo `temp_condensacao` em `performance_equipamento`
Armazena **T.Amb** (temperatura ambiente), não T.Cond. Padrão dos catálogos técnicos brasileiros — os fabricantes (Elgin, Tecumseh, etc.) publicam curvas por T.Amb.

Para calcular T.Cond real: `T.Cond = T.Amb + ΔT_condensação` (ΔT informado pelo contexto, tipicamente 8–15°C).

### Dados reais no banco
O banco contém apenas dados reais de catálogos de fabricantes. Seeds de teste foram removidos. Exceção: perfis termodinâmicos ASHRAE — são dados técnicos validados.

### Catálogo global × catálogo por empresa
O catálogo atual é global (gerenciado pelo admin SaaS). Na Fase 2, será adicionado o catálogo por empresa (`equipamento_empresa`, `componente_empresa`) com código interno, fornecedor e preço negociado.

---

## 5. Ordem de Dependências

```
unidade_medida
fabricante
categoria
   ↓
equipamento → performance_equipamento
componente_tecnico → performance_componente
painel_frigorifico
porta_frigoriifica
isolamento_tubulacao
perfil_produto_termico
peso_tubo_cobre
   ↓
usuario
cliente
   ↓
projeto (referencia usuario + cliente)
cotacao → proposta
configuracao_montagem (referencia usuario)
```

---

## 6. Índices Relevantes

- `idx_performance_equipamento_busca` — (equipamento_id, fluido, temp_evaporacao, temp_condensacao)
- `idx_projeto_usuario` — (usuario_id)
- `idx_cotacao_projeto` — (projeto_id)
