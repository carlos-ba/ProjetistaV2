# 09 - Próximos Passos

Atualizado em: 2026-06-28

O wizard de 6 cards está completo e funcional em produção. Os próximos passos são evoluções de produto, não funcionalidades básicas.

---

## Fase 2 — Admin Panel e Multi-Tenancy

### Objetivo
Permitir que cada empresa cliente gerencie seus próprios dados sem depender do admin SaaS.

### Itens
1. **Catálogo por empresa** — tabelas `equipamento_empresa` e `componente_empresa`:
   - `equipamento_id` (FK catálogo global)
   - `empresa_id` (FK tenant)
   - `codigo_interno`, `codigo_fornecedor`, `custo`, `fornecedor`, `ativo`
2. **Admin panel** — formulários de cadastro por categoria de equipamento/componente
3. **Multi-tenancy** — isolamento de dados por empresa (RLS ou filtro por `empresa_id`)
4. **Gestão de usuários por empresa** — perfis: admin da empresa, técnico, visualizador

---

## Fase 3 — IA com Tool Use

### Objetivo
Usar Claude API com tool use para análises e sugestões automáticas durante o dimensionamento.

### Candidatos de uso
- Análise de coerência do projeto (carga vs. equipamento selecionado)
- Sugestão de fluido refrigerante com base no perfil da câmara
- Detecção de inconsistências entre cards (ex.: bitola subimensionada)
- Geração de memorial descritivo em linguagem natural

---

## Fase 4 — Testes Automatizados

### Objetivo
Cobrir os cálculos críticos com testes de regressão.

### Prioridade
1. Cálculo de carga térmica (método simplificado e psicrométrico)
2. Seleção de solenoide (motor Kv — R404A e R22)
3. Dimensionamento ASHRAE de tubulação
4. Seleção de equipamento por interpolação de performance

---

## Fase 5 — Billing e Planos

### Objetivo
Monetizar o SaaS com planos de assinatura.

### Itens
1. Integração com gateway de pagamento (Stripe ou Pagar.me)
2. Definição de planos (free trial, básico, profissional, empresa)
3. Limite de projetos por plano
4. Portal do cliente para gestão de assinatura

---

## Melhorias Contínuas (qualquer fase)

- Ampliar o banco de equipamentos (mais fabricantes, mais modelos, R290)
- Adicionar compressores como opção no Card 3
- Suporte a fluidos além de R404A e R22 no motor de solenoide
- Exportação do diagrama SVG do cavalete junto com a proposta PDF
- Modo escuro na interface
- Responsividade para tablet

---

## Regra de Trabalho

1. Sempre iniciar com `git pull origin main`
2. Implementar em pequenas entregas com commit por etapa
3. Testar local antes de qualquer push
4. Atualizar `docs/08_status_atual.md` ao final de sessões relevantes
