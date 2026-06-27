# CLAUDE.md — ProjetistaV2

Leia este arquivo no início de toda sessão. Ele descreve o estado real do projeto,
como rodar localmente, convenções adotadas e o que está pendente de implementar.

---

## Identidade do Produto

**IceNexus IAR** — SaaS de dimensionamento frigorífico para técnicos e engenheiros de refrigeração.
Substitui planilhas manuais por um wizard guiado de 6 etapas.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic |
| Driver DB | psycopg3 (`psycopg[binary]`) — string: `postgresql+psycopg://` |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Deploy backend | Render (auto-deploy no push para `main`) |
| Deploy frontend | Vercel (auto-deploy no push para `main`) |
| Migrations | Alembic (0001→0009), roda no `startCommand` do Render |

---

## Ambiente Local (PC2 — notebook)

### Subir o backend

```powershell
cd C:\projetos\ProjetistaV2\backend
C:\projetos\ProjetistaV2\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Subir o frontend

```powershell
cd C:\projetos\ProjetistaV2\frontend
npm run dev
```

Frontend abre em `http://localhost:5173`. Backend em `http://localhost:8000`.

### Banco local

- PostgreSQL 17 na porta 5432
- Database: `projetista_v2`, User: `projetista`
- Conectar: `$env:PGPASSWORD = "projetista"; & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U projetista -p 5432 -d projetista_v2`

### Variáveis de ambiente (.env no backend/)

```
DATABASE_URL=postgresql+psycopg://projetista:projetista@localhost:5432/projetista_v2
SECRET_KEY=...
```

---

## URLs de Produção

| Serviço | URL |
|---------|-----|
| Frontend | https://projetista-v2.vercel.app |
| Backend API | https://projetista-v2-api-alt.onrender.com |
| API Docs | https://projetista-v2-api-alt.onrender.com/docs |
| GitHub | https://github.com/carlos-ba/ProjetistaV2 |

---

## Estrutura do Wizard (6 Cards)

O fluxo é um wizard linear. Cada card passa dados para o próximo via callbacks em `App.jsx`.

| Card | Componente | Descrição |
|------|-----------|-----------|
| 1 | `CalculadoraGabinete.jsx` | Dimensões, isolamento (painel PIR), temperatura interna, tipo de piso |
| 2 | `CalculadoraCargaTermica.jsx` | Cálculo de carga térmica (kcal/h) |
| 3 | `SelecaoEquipamentos.jsx` | Seleção de UC + Evaporadora do banco de dados |
| 4 | `ComponentesFluxo.jsx` | Componentes de fluxo e segurança (solenoide, separadores, etc.) |
| 5 | `CalculadoraTubulacao.jsx` | Dimensionamento de tubulação (bitolas ASHRAE) |
| 6 | `GeradorOrcamento.jsx` | Geração de orçamento + cotação + proposta comercial |

---

## Card 4 — ComponentesFluxo — Estado Atual (commit ec50321)

Este é o card com mais desenvolvimento recente. Leia com atenção.

### Dois modos de seleção

**Modo Automático** (padrão):
- Busca componentes do banco via `POST /api/v1/componentes`
- Busca solenoide via `POST /api/v1/solenoide/selecionar` em paralelo (Promise.allSettled)
- Exibe grid de cards clicáveis (toggle incluir/excluir)
- Solenoide aparece como card 4 com borda roxa — calculado por Kv interno (sem Coolselector)
- Separador de líquido e separador de óleo: selecionados automaticamente pelo banco

**Modo Engenharia**:
- Abre CoolSelector®2 Online (Danfoss) para seleção manual
- Mostra parâmetros do projeto (fluido, T.Evap, T.Cond, capacidade em kW)
- Técnico registra manualmente VET, Filtro Secador, Solenoide, Visor de Líquido
- Separadores ainda vêm do banco automaticamente

### Motor de seleção de solenoide (já implementado)

- Arquivo: `backend/app/services/solenoide.py`
- Endpoint: `POST /api/v1/selenoide/selecionar`
- Parâmetros: `fluido`, `te_c`, `tc_c`, `capacidade_kw`, `dp_bar` (default 0.10)
- Fluidos suportados: **R404A** e **R22** (tabelas do CoolPack/DTU)
- Fórmula: `Q[kW] = Kv × √(1000 × ΔP × ρ_L) × Δh / 3600`
- Família: Danfoss EVR v2 (EVR2 a EVR40), ordenados por Kv crescente
- Margem de segurança: 10% (seleciona menor EVR com Q_válvula ≥ Q_requerida × 1.10)
- Validado contra CoolSelector2 local: EVR 6 man v2 para R404A -25°C/-35°C 5.8kW ✓

### O que FALTA implementar no Card 4 — Modo Automático

Estes itens precisam ser adicionados como cards automáticos (igual à solenoide):

**1. Filtro Secador (Danfoss)**
- Regra DML vs DMC:
  - **DML** = sistema com tanque de líquido separado (padrão refrigeração comercial)
  - **DMC** = sistema pequeno SEM tanque de líquido (combinado receptor + filtro)
  - **DCL** = igual ao DML mas com 20% alumina ativada — R22 com óleo mineral, T.Cond alta
- Seleção de tamanho: pelo diâmetro da linha de líquido (vem do Card 5 — tubulação)
- Codificação do modelo: `DML XY` onde X = volume em in³, Y = conexão (Y/8 = polegadas)
  - Exemplo: DML 53 → 5 in³, conexão 3/8" (10mm)
- Falta definir: como saber se o projeto tem ou não tanque de líquido (campo no projeto?)

**2. Visor de Líquido (Danfoss SGN)**
- Modelo padrão: **SGN** com sufixo "s" (solda brasada) — ex: SGN 16s para linha 5/8"
- Seleção: exclusivamente pelo **diâmetro da linha de líquido**
- Tamanhos: SGN 6 (1/4"), SGN 10 (3/8"), SGN 12 (1/2"), SGN 16 (5/8"), SGN 19 (3/4"), SGN 22s (7/8")
- Posição de instalação: depois do filtro secador, antes da VET
- Indicador de umidade: muda de verde → amarelo quando a umidade está alta

**Problema de sequência:** o diâmetro da linha de líquido é calculado no Card 5 (Tubulação), mas o Card 4 vem antes. Estratégias possíveis:
  a) Calcular a bitola da linha de líquido internamente no Card 4 com base em cargaAlvo + fluido + tempEvap
  b) Deixar visor e filtro como sugestão editável, sem tamanho exato, até o Card 5 confirmar

---

## Convenções de Nomenclatura (OBRIGATÓRIO seguir)

| Termo correto | Não usar |
|---------------|----------|
| **tanque de líquido** | receptor, receiver |
| **T. Evaporação / T.Evap** | temperatura de evaporação (abrev.) |
| **T. Condensação / T.Cond** | — |
| **T. Ambiente / T.Amb** | temperatura externa |
| **kcal/h** | BTU/h (não usado neste projeto) |
| **kW** | unidade usada no CoolSelector e nos cálculos internos |

---

## Banco de Dados — Migrations

| Migration | Conteúdo |
|-----------|---------|
| 0001 | Schema completo v2 (todas as tabelas base) |
| 0002 | Verificação de e-mail no usuário |
| 0003 | Campo `consumo_kw` em performance de equipamento |
| 0004 | Campo `temp_ambiente` em performance de equipamento |
| 0005 | Tabela `painel_frigorifico` (Kingspan Isoeste PIR) |
| 0006 | Tabela `isolamento_tubulacao` |
| 0007 | Tabela `porta_frigoriifica` |
| 0008 | Tabela cotação com fornecedor (Fase 2) |
| 0009 | Tabela proposta comercial (Fase 3) |

---

## Catálogo carregado no App com retry

O catálogo (fabricantes de painel, portas) é carregado **no `App.jsx`** antes de renderizar qualquer card, com retry automático a cada 2s até sucesso. **Nunca buscar catálogo dentro de um componente filho.** Passar sempre via props.

---

## Fluxo de Cotação e Proposta (Fases 1-3 — implementadas)

- **Fase 1:** Geração de planilha Excel de cotação com lista de materiais e equipamentos
- **Fase 2:** Importação da planilha devolvida pelo fornecedor com preços preenchidos
- **Fase 3:** Geração de proposta comercial em PDF com preços da cotação
- Acessível via sidebar "Cotações" (`PainelCotacoes.jsx`) e `GeradorOrcamento.jsx`

---

## Fluxo de Trabalho Obrigatório (SEGUIR SEMPRE)

```
EDITAR LOCAL → TESTAR LOCAL → COMMIT → PUSH → PRODUÇÃO
```

**NUNCA editar diretamente em produção. NUNCA fazer push sem testar local primeiro.**

### Passo a passo

1. **Editar** os arquivos em `C:\projetos\ProjetistaV2\`
2. **Subir o backend local** (nova aba do terminal):
   ```powershell
   cd C:\projetos\ProjetistaV2\backend
   C:\projetos\ProjetistaV2\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```
3. **Subir o frontend local** (nova aba do terminal):
   ```powershell
   cd C:\projetos\ProjetistaV2\frontend
   npm run dev
   ```
4. **Testar** em `http://localhost:5173` — verificar TODOS os pontos alterados
5. **Confirmar** com o usuário que está tudo ok
6. **Commit** com mensagem descritiva:
   ```powershell
   cd C:\projetos\ProjetistaV2
   git add backend/... frontend/...
   git commit -m "fix: descrição do que foi corrigido"
   ```
7. **Push** para produção (Render + Vercel auto-deploy):
   ```powershell
   git push origin main
   ```

### Regras derivadas

- Acumular mudanças relacionadas no mesmo commit — não fazer um push por arquivo
- Jamais usar `--no-verify` para pular verificações
- Se o teste local falhar, corrigir antes de qualquer push
- `--reload` só no backend local; produção usa o comando do Render sem `--reload`

---

## Regras de Desenvolvimento
3. **Fluidos suportados no motor de solenoide:** R404A e R22. Para outros, redirecionar ao CoolSelector
4. **T.Condensação calculada como:** T.Amb + 10°C (padrão de mercado brasileiro)
5. **Catálogo de componentes no banco:** separadores de líquido e óleo vêm do banco via `/api/v1/componentes`. VET, filtro secador, solenoide e visor são calculados/selecionados pelo próprio sistema (solenoide já implementado)

---

## Estado atual do código (2026-06-25 — commit ec50321)

| Funcionalidade | Status |
|---------------|--------|
| Wizard 6 cards | ✅ funcional |
| Autenticação JWT | ✅ |
| Gabinete + painéis PIR Kingspan | ✅ |
| Carga térmica | ✅ |
| Seleção UC + Evaporadora | ✅ |
| Card 4 — Modo Automático (separadores) | ✅ banco de dados |
| Card 4 — Solenoide automático (R404A/R22) | ✅ motor Kv implementado |
| Card 4 — Filtro secador automático | ❌ pendente |
| Card 4 — Visor de líquido automático | ❌ pendente |
| Card 4 — Modo Engenharia (CoolSelector) | ✅ |
| Tubulação ASHRAE | ✅ |
| Orçamento + Cotação + Proposta | ✅ |
