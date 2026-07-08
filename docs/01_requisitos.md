# 01 - Requisitos do Projeto V2

**Versão:** 2.0
**Data:** 2026-06-28
**Status:** Implementado (MVP em produção)

---

## 1. Visão Geral do Produto

O **IceNexus IAR** é um SaaS web voltado para técnicos e engenheiros de refrigeração que precisam dimensionar câmaras frigoríficas e gerar propostas comerciais.

O sistema guia o usuário por um **wizard de 6 etapas** — do dimensionamento do gabinete até a geração da proposta em PDF — substituindo planilhas manuais por um fluxo guiado e automatizado.

---

## 2. Perfis de Usuário

### 2.1 Técnico / Engenheiro de Refrigeração (usuário principal)
- Acessa o sistema pelo navegador (desktop prioritário)
- Realiza projetos de câmaras frigoríficas
- Seleciona equipamentos e componentes com base nos cálculos
- Gera proposta comercial para o cliente final

### 2.2 Admin SaaS (operador interno)
- Gerencia o catálogo global de equipamentos e componentes
- Cadastra painéis, portas, equipamentos, performances
- Fase 2 — ainda não implementado

---

## 3. Requisitos Funcionais

### RF-01 — Autenticação de Usuário
- Login com e-mail e senha (JWT)
- Sessão autenticada com token de acesso + refresh token
- Logout
- **Status:** ✅ implementado

---

### RF-02 — Dimensionamento do Gabinete (Card 1)
- Usuário informa: dimensões (largura, altura, comprimento), temperatura interna, tipo de piso, painel PIR (espessura/fabricante) e portas frigoríficas
- Sistema calcula: área das paredes, lista de corte de painéis, materiais de montagem
- Catálogo de painéis PIR Kingspan Isoeste e portas carregado via API
- **Status:** ✅ implementado

---

### RF-03 — Cálculo de Carga Térmica (Card 2)
- Entradas: temperatura ambiente (T.Amb), produto armazenado, infiltração, ocupação, iluminação
- Dois métodos: simplificado e psicrométrico (ASHRAE)
- Saída: carga total em kcal/h
- **Status:** ✅ implementado

---

### RF-04 — Seleção de Equipamentos (Card 3)
- Sistema busca no banco unidades condensadoras (UC) e evaporadoras compatíveis com:
  - carga calculada (kcal/h)
  - fluido refrigerante
  - temperatura de evaporação (T.Evap)
- Usuário seleciona UC + evaporadora
- **Status:** ✅ implementado

---

### RF-05 — Dimensionamento de Tubulação (Card 4)
- Entradas: distâncias de cada trecho (líquido, sucção, descarga), desnível
- Cálculo de bitolas seguindo tabelas ASHRAE
- Sugestão automática de padrão de isolamento Armacel (D/F/H/M/R/T) por T.Evap
- Linha de sucção sempre isolada; linha de líquido opcional
- Saída: lista de tubos (bitola, metros, peso, isolamento) para orçamento
- **Status:** ✅ implementado

---

### RF-06 — Seleção de Componentes de Fluxo (Card 5)
**Modo Automático:**
- Separadores de líquido e óleo: selecionados do banco por capacidade
- Válvula solenoide: motor de cálculo Kv interno, família Danfoss EVR v2 (R404A e R22)
- Filtro secador: DML (com tanque de líquido) ou DMC (sem tanque), seleção pelo diâmetro da linha
- Visor de líquido: Danfoss SGN, seleção pelo diâmetro da linha de líquido
- Tanque de líquido: seleção automática via NBR 16.069 após estimativa de carga de fluido
- Estimativa de carga de fluido: kg por trecho (evaporador + linhas)
- Cavalete: análise automática de luvas de redução, porcas e luvas de passagem

**Modo Engenharia:**
- Integração com CoolSelector®2 Online (Danfoss) para seleção manual
- Campos para registrar manualmente: VET, Filtro Secador, Solenoide, Visor
- Separadores ainda automáticos do banco

- **Status:** ✅ implementado

---

### RF-07 — Orçamento e Proposta Comercial (Card 6)
- Consolidação de todos os itens dos cards anteriores
- **Fase 1:** Geração de planilha Excel de cotação (lista de materiais com metros e kg)
- **Fase 2:** Importação da planilha devolvida pelo fornecedor com preços
- **Fase 3:** Geração de proposta comercial em PDF
- **Status:** ✅ implementado

---

### RF-08 — Salvar e Carregar Projetos
- Usuário salva o projeto com nome e associação a um cliente
- Estado completo de todos os cards salvo em `dados_completos` (JSONB)
- Carregamento automático ao reabrir o projeto
- Invalidação em cascata: recalcular card N invalida os cards N+1 a 6
- **Status:** ✅ implementado

---

### RF-09 — Gestão de Clientes
- Cadastro de clientes (nome, e-mail, telefone, endereço)
- Vínculo entre projeto e cliente
- **Status:** ✅ implementado

---

### RF-10 — Configurações de Montagem
- Perfis de montagem salvos por usuário: tipo de filtro preferido, tipo de visor, trechos padrão
- Aplicados automaticamente ao iniciar um novo projeto
- **Status:** ✅ implementado

---

## 4. Requisitos Não Funcionais

### RNF-01 — Desempenho
- Cálculos processados em menos de 3 segundos para projetos padrão
- Interface carregando em menos de 2 segundos em conexões convencionais

### RNF-02 — Disponibilidade
- Disponibilidade mínima de 99% (garantida por Render + Vercel)

### RNF-03 — Segurança
- Senhas armazenadas com hash (nunca em texto puro)
- Comunicação exclusiva via HTTPS
- Backend valida e sanitiza todos os dados de entrada
- Tokens JWT com prazo de expiração

### RNF-04 — Escalabilidade
- Backend stateless — estado persistido apenas no banco
- Escalável horizontalmente

### RNF-05 — Manutenibilidade
- Separação rígida entre camadas: api, services, models, schemas
- Decisões técnicas registradas em `docs/07_decisoes_tecnicas.md` e `docs/DECISOES_ARQUITETURA.md`
- Schema do banco controlado por migrations Alembic

### RNF-06 — Usabilidade
- Interface responsiva para desktop (prioritário) e tablet
- Funciona em Chrome, Firefox, Edge, Safari modernos

---

## 5. Fluxo Principal do Usuário

```
1. Usuário acessa o sistema e faz login
2. Usuário cria novo projeto (nome + cliente)
3. Card 1: preenche dimensões do gabinete e escolhe painéis/portas
4. Card 2: informa produto e condições para cálculo de carga térmica
5. Card 3: seleciona UC + evaporadora compatíveis
6. Card 4: informa distâncias de tubulação → sistema dimensiona bitolas e isolamento
7. Card 5: sistema seleciona automaticamente todos os componentes de fluxo
8. Card 6: revisa orçamento, gera planilha Excel para cotação e proposta PDF
9. Usuário salva o projeto a qualquer momento
```

---

## 6. Fora do Escopo Atual

- Admin panel / cadastro de equipamentos pelo cliente (Fase 2)
- IA com Tool Use para análise e sugestões (Fase 3)
- Testes automatizados de regressão (Fase 4)
- Billing e planos de assinatura (Fase 5)
- Aplicativo mobile
- Modo offline
- Compartilhamento de projetos entre usuários

---

## 7. Restrições e Premissas

| Item | Decisão |
|------|---------|
| Linguagem do sistema | Português (pt-BR) |
| Plataforma alvo | Web (desktop prioritário) |
| Autenticação | E-mail + senha (JWT) |
| Deploy | Vercel (frontend) + Render (backend + banco) |
| Banco de dados | PostgreSQL 17 |
| Backend | Python + FastAPI + SQLAlchemy 2.0 async |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Comunicação | REST API (JSON) |
| Unidade de capacidade | kcal/h (padrão mercado BR) |
| Fluidos suportados | R404A e R22 (motor solenoide); outros via Modo Engenharia |
