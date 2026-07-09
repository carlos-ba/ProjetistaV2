# Auditoria Técnica — ProjetistaV2 / IceNexus IAR (2026-07-08)

## Pontos fortes
1. **Arquitetura limpa**: backend separado em routes → services → models; motores de cálculo isolados e documentados com fontes técnicas (CoolPack/DTU, ASHRAE, NBR 16.069).
2. **Multi-tenancy básico correto**: queries filtram por `owner_id`/`usuario_id` consistentemente.
3. **Segurança de configuração**: `config.py` recusa produção com `SECRET_KEY` padrão ou CORS `*`; bcrypt; JWT tipado (access/refresh); migrations disciplinadas (0001→0016).
4. **Boas decisões de produto**: invalidação em cascata dos cards; catálogo com retry no App.jsx; `dados_completos` como snapshot JSON do wizard.

## A corrigir (por prioridade)

### 1. Zero testes automatizados
Nenhum `test_*.py` ou `.test.jsx`. Começar pelos services do backend (solenoide Kv,
tubulação ASHRAE, carga térmica) — funções puras, fáceis de testar, onde erro custa caro.

### 2. Componentes frontend gigantes
- `GeradorOrcamento.jsx`: 1.854 linhas, ~30 estados
- `ComponentesFluxo.jsx`: 991 linhas · `App.jsx`: 962 linhas
- Lógica duplicada tela × PDF diverge silenciosamente (causa dos bugs de jul/2026).
- **Ação**: extrair `calcFinanceiro` e `agruparItens` para módulo compartilhado (fonte única).

### 3. Classificação de itens por texto do nome
Palavras-chave no nome ("isolamento", "porta", "placa") decidem o bloco financeiro.
Bug real: Isolamento Armacel (tubulação) cai em "Painéis, estrutura e materiais".
**Ação**: propagar campo `categoria` estruturado do backend para todos os itens
(já iniciado com `categoria='equipamento'`).

### 4. Erros engolidos no frontend
25 blocos `catch {` com mensagens genéricas. **Ação**: exibir `error.response?.data?.detail`.

### 5. routes_seed.py exposto em produção
882 linhas; protegido por `token == SECRET_KEY` na **query string** (chave mestra em logs).
**Ação**: remover em produção ou usar token separado via header.

### 6. Pontos menores
- Tokens JWT em localStorage (XSS rouba sessão) → httpOnly cookies na Fase 2
- Sem rate-limit no login (força bruta possível)
- `dados_completos: Dict[str, Any]` sem limite de tamanho
- `window.prompt`/`alert` em 14 lugares → modais próprios
- `PropostaComercial.jsx` (787 linhas) possivelmente redundante com PDF nativo → candidato a remoção

## Tarefas de PRÉ-LANÇAMENTO (adiadas de propósito)

- **Rate-limiting nos endpoints da API** (ex.: slowapi). Proteção real contra raspagem
  em massa do catálogo/tabelas. Adiado de propósito: durante o desenvolvimento é atrito
  (limitador bloqueia testes repetidos) e agrega pouco com um único usuário atrás de login.
  Fazer perto do lançamento, calibrando limites pelo uso real. Não muda arquitetura nem cálculos.
- **Contexto (2026-07-09):** susto com o Gemini "explicando" o programa foi falso alarme —
  ele descreveu a metodologia ASHRAE pública (até errou detalhes, citou BTU/h que o projeto
  não usa), não leu o código. Cálculos rodam no backend (não expostos); o "muro" real são os
  dados no banco (U-values, catálogo, tabelas Kv) e o produto integrado, não a fórmula.

## Melhoria futura: agente IA conversa → orçamento (VIÁVEL)

Arquitetura recomendada:
- **Fase A — Transcrição**: áudio → texto via speech-to-text (Whisper/AssemblyAI; Claude não transcreve áudio).
- **Fase B — Extração estruturada** (MVP recomendado): Claude lê a transcrição e devolve JSON
  validado (structured outputs) com os campos do wizard → pré-preenche os cards, técnico revisa.
- **Fase C — Agente com Tool Use** (Fase 3 do roadmap): os 20 endpoints existentes viram as
  ferramentas do agente (`calcular_gabinete`, `carga_termica`, `selecao`, `tubulacao`,
  `componentes`, `orcamento`). O agente percorre a trilha; cálculos continuam determinísticos
  no backend (risco de alucinação numérica ≈ zero). Se faltar dado, o agente pergunta.
- Custos: centavos a poucos reais por orçamento. Exigir revisão humana antes de enviar ao cliente.
- Começar pela Fase B — baixo risco, alto valor.
